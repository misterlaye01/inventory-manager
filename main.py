# https://github.com/misterlaye01/inventory-manager.git

import os
import bcrypt
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from datetime import datetime
from getpass import getpass


load_dotenv()

DEFAULT_DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ['DB_USER'],
    'password': os.environ['DB_PASSWORD'],
    'database': os.environ['DB_NAME'],
    'port': int(os.environ.get('DB_PORT', '3306'))
}

user_connected = None

def get_connection():
    """ Retourne une nouvelle connexion MySQL """

    return mysql.connector.connect(**DEFAULT_DB_CONFIG)

def create_tables():
    """ Crée les tables nécessaires si elles n'existent pas encore """

    cnx = get_connection()
    cur = cnx.cursor()

    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category_name VARCHAR(32) UNIQUE NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_name VARCHAR(32) NOT NULL,
            quantity INT NOT NULL DEFAULT 0,
            category_id INT NOT NULL,
            CONSTRAINT fk_categories_products FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
            """
        )

        cur.execute(
            """ 
            CREATE TABLE IF NOT EXISTS history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            quantity INT NOT NULL,
            type VARCHAR(10) NOT NULL,
            date DATETIME NOT NULL,
            product_id INT NOT NULL,
            CONSTRAINT fk_products_history FOREIGN KEY (product_id) REFERENCES products(id)
            )
            """
        )

        cur.execute(
            """ 
            CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(64) NOT NULL,
            email VARCHAR(128) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role ENUM('admin', 'gestionnaire', 'observateur') NOT NULL DEFAULT 'observateur',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cnx.commit()
    except Error as e:
        cnx.rollback()
        print(f'Erreur lors de la création des tables : {e}')
    finally:
        cur.close()
        cnx.close()

def user_input(text):
    """ Validation de la saisie utilisateur """

    while True:
        user_input = input(text).strip()
        if user_input:
            return user_input
        print('Ce champ ne peut pas être vide')

def email_input(text):
    """ Validation de l'email """
    
    while True:
        email = input(text).strip().lower()
        if '@'in email and '.' in email.split('@')[-1]:
            return email
        print('Adresse email invalide')

def hash_password(password):
    """ Hashage du mot de passe """

    salt = bcrypt.gensalt()
    hashed_pwd = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_pwd.decode('utf-8')

def verify_password(password, hashed_pwd):
    """ Vérifie le mot de passe avec celui de dans la base de données """

    return bcrypt.checkpw(password.encode('utf-8'), hashed_pwd.encode('utf-8'))

def first_account():
    """  """

    cnx = get_connection()
    cur = cnx.cursor()

    try:
        cur.execute('SELECT COUNT(*) FROM users')
        users = cur.fetchone()[0]
    finally:
        cur.close()
        cnx.close()

        if users > 0:
            return
        
        print('Aucun utilisateur trouvé. Créer le compte administrateur\n')

        username = user_input('Nom utilisateur : ')
        email = email_input('Email :')

        while True:
            password = getpass('Mot de passe (8 caractères minimum) : ')
            confirm_password = getpass('Confirmer le mot de passe : ')

            if password != confirm_password:
                print('Les mots de passe ne correspondent pas')
            elif len(password) < 8:
                print('Le mot de passe doit contenir au moins 8 caractères')
            else:
                break
        
        cnx = get_connection()
        cur = cnx.cursor()

        try:
            cur.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, 'admin')", (username, email, hash_password(password)))
            cnx.commit()
            print(f'\n{username} créé en tant que administrateur')
        except Error as e:
            cnx.rollback()
            print(f'Erreur lors de la création : {e}')
        finally:
            cur.close()
            cnx.close()

def login():
    """ Demande email et mot de passe """

    global user_connected

    email = email_input('Email : ')
    password = getpass('Mot de passe : ')

    cnx = get_connection()
    cur = cnx.cursor(dictionary=True)

    try:
        cur.execute('SELECT id, username, email, password, role FROM users WHERE email = %s', (email,))
        user = cur.fetchone()

        if user is None or not verify_password(password, user['password']):
            print('Email ou mot de passe incorrect')
            return None
        
        user_connected = user
        print(f'Bienvenue {user['username']} ! ({user['role']})')
        return user
    except Error as e:
        print(f'Erreur lors de la connexion : {e}')
        return None
    finally:
        cur.close()
        cnx.close()

def is_allowed(*role):
    """ Vérifie si l'utilisateur est autorisé """

    if user_connected is None:
        print('Vous devez être connecté')
        return False
    
    if user_connected['role'] not in role:
        print(f'Accès refusé')
        return False
    
    return True

def create_user():
    """ Crée un nouvel utilisateur """

    if not is_allowed('admin'):
        return
    
    username = user_input('Nom utilisateur : ')
    email = email_input('Email : ')

    print('Rôles disponibles : admin, gestionnaire, observateur')
    while True:
        role = input('Rôle : ').strip().lower()
        if role in ('admin', 'gestionnaire', 'observateur'):
            break
        print('Rôle invalide')

    while True:
        password = getpass('Mot de passe (8 caractères minimum) : ')
        confirm_password = getpass('Confirmer le mot de passe : ')

        if password != confirm_password:
            print('Les mots de passe ne correspondent pas')
        elif len(password) < 8:
            print('Le mot de passe doit contenir au moins 8 caractères')
        else:
            break
    
    cnx = get_connection()
    cur = cnx.cursor()
    try:
        cur.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)", (username, email, hash_password(password), role))
        cnx.commit()
        print(f"Utilisateur '{username}' ({role}) créé avec succès.")
    except Error as e:
        cnx.rollback()
        print(f"Erreur lors de la création de l'utilisateur : {e}")
    finally:
        cur.close()
        cnx.close()

def list_all_users():
    """ Affiche tous les comptes """

    if not is_allowed('admin'):
        return
    
    cnx = get_connection()
    cur = cnx.cursor(dictionary=True)

    try:
        cur.execute('SELECT id, username, email, role, created_at FROM users ORDER BY role, username')
        users = cur.fetchall()

        if not users:
            print('Aucun utilisateur enregistré')
            return
        
        for u in users:
            print(f"{u['id']}: {u['username']} - {u['email']} - {u['role']} - {u['created_at'].strftime('%d/%m/%Y %H:%M')}")
    except Error as e:
        print(f"Erreur lors de l'affichage des utilisateurs : {e}")
    finally:
        cur.close()
        cnx.close()

def add_category():
    """ Ajoute une nouvelle catégorie """

    if not is_allowed('admin'):
        return
    
    category_name = user_input('Nom de la catégorie : ')

    cnx = get_connection()
    cur = cnx.cursor()

    try:
        cur.execute('INSERT INTO categories (category_name) VALUES (%s)', (category_name,))
        cnx.commit()
        print(f'{category_name} ajoutée dans les catégories')
    except Error as e:
        cnx.rollback()
        print("Erreur lors de l'ajout de la catégorie")
    finally:
        cur.close()
        cnx.close()

def display_categories():
    """ Affiche la liste des catégories disponibles """

    cnx = get_connection()
    cur = cnx.cursor(dictionary=True)

    try:
        cur.execute('SELECT * FROM categories ORDER BY id')
        categories = cur.fetchall()

        if not categories:
            print('Aucune catégorie enregistrée')
            return
        
        for cat in categories:
            print(f"{cat['id']} : {cat['category_name']}")
    except Error as e:
        print(f"Erreur lors de l'affichage des catégories : {e}")
    finally:
        cur.close()
        cnx.close()

def add_product():
    """ Ajoute un produit """

    if not is_allowed('admin'):
        return

    product_name = user_input('Nom du produit : ')
    display_categories()
    while True:
        category_id = input('Identifiant de la catégorie : ').strip()

        if category_id.isdigit() and int(category_id) > 0:
            cnx = get_connection()
            cur = cnx.cursor()

            try:
                cur.execute('INSERT INTO products (product_name, quantity, category_id) VALUES (%s, 0, %s)', (product_name, category_id))
                cnx.commit()
                print(f'{product_name} ajouté avec succès')
            except Error as e:
                cnx.rollback()
                print(f"Erreur lors de l'ajout du produit: {e}")
            finally:
                cur.close()
                cnx.close()
        break

def display_products():
    """ Affiche la liste des produits avec leur catégorie et leur stock actuel """
    
    cnx = get_connection()
    cur = cnx.cursor(dictionary=True)

    try:
        cur.execute(
            """
            SELECT products.id, products.product_name, categories.category_name, products.quantity 
            FROM products JOIN categories ON products.category_id = categories.id
            """
        )
        products = cur.fetchall()
        if not products:
            print('Aucun produit enregistré')
            return

        for prod in products:
            print(f"{prod['id']} - {prod['product_name']} - {prod['quantity']} - {prod['category_name']}")
    except Error as e:
        print(f"Erreur lors de l'affichage des produits : {e}")
    finally:
        cur.close()
        cnx.close()

def add_stock():
    """ Enregistre une entrée pour un produit existant """

    if not is_allowed('admin', 'gestionnaire'):
        return

    display_products()
    while True:
        product_id = input('identifiant du produit : ').strip()
        quantity = input('Quantité à ajouter : ').strip()

        if product_id.isdigit() and int(product_id) > 0 and quantity.isdigit() and int(quantity):
            cnx = get_connection()
            cur = cnx.cursor()

            try:
                cur.execute('UPDATE products SET quantity = quantity + %s WHERE id = %s', (quantity, product_id))
                cur.execute("INSERT INTO history (product_id, quantity, type, date) VALUES (%s, %s, 'ENTRÉE', %s)", (product_id,quantity, datetime.now()))
                cnx.commit()
                print(f'Quantité ajoutée : {quantity}')
            except Error as e:
                cnx.rollback()
                print(f"Erreur lors de l'entrée en stock : {e}")
            finally:
                cur.close()
                cnx.close()
        break

def remove_stock():
    """ Enregistre une sortie pour un produit existant """

    if not is_allowed('admin', 'gestionnaire'):
        return

    display_products()
    while True:
        product_id = input('identifiant du produit : ').strip()
        quantity = input('Quantité à retirer : ').strip()

        if product_id.isdigit() and int(product_id) > 0 and quantity.isdigit() and int(quantity):
            cnx = get_connection()
            cur = cnx.cursor()

            try:
                cur.execute('UPDATE products SET quantity = quantity - %s WHERE id = %s', (quantity, product_id))
                cur.execute("INSERT INTO history (product_id, quantity, type, date) VALUES (%s, %s, 'SORTIE', %s)", (product_id,quantity, datetime.now()))
                cnx.commit()
                print(f'Quantité retirée : {quantity}')
            except Error as e:
                cnx.rollback()
                print(f"Erreur lors de la sortie en stock : {e}")
            finally:
                cur.close()
                cnx.close()
        break

def show_history():
    """ Affiche l'historique complet des mouvements de stock """

    if not is_allowed('admin', 'gestionnaire'):
        return

    cnx = get_connection()
    cur = cnx.cursor(dictionary=True)

    try:
        cur.execute(
            """ 
            SELECT products.product_name, history.quantity, history.type, history.date 
            FROM history JOIN products ON products.id = history.product_id 
            ORDER BY date DESC
            """
        )

        history = cur.fetchall()
        if not history:
            print('Historique vide')

        for histo in history:
            print(f"{histo['product_name']} - {histo['quantity']} - {histo['type']} - {histo['date'].strftime('%d/%m/%Y %H:%M')}")
    except Error as e:
        print(f"Erreur lors de l'affichage de l'historique : {e}")
    finally:
        cur.close()
        cnx.close()

def display_menu():
    """ Affiche uniquement les options accessibles au rôle de l'utilisateur connecté """
    role = user_connected['role']
    nom  = user_connected['username']

    print(f"\n--------- MENU PRINCIPAL - {nom} ({role}) ---------")

    if role == 'admin':
        print('1. Ajouter une catégorie')
        print('2. Ajouter un produit')

    if role in ('admin', 'gestionnaire'):
        print('3. Entrée en stock')
        print('4. Sortie de stock')

    print('5. Liste des catégories')
    print('6. Liste des produits')

    if role in ('admin', 'gestionnaire'):
        print('7. Historique des mouvements')

    if role == 'admin':
        print("8. Gestion des utilisateurs")

    print("0. Déconnexion")


# ---------- PROGRAMME PRINCIPAL ----------


create_tables()
first_account()

while True:
    user_connected = None
    attemps = 0

    while attemps < 3:
        user_connected = login()
        if user_connected:
            break
        attemps = attemps + 1
        remaining_attemps = 3 - attemps

        if remaining_attemps > 0:
            print(f'{remaining_attemps} tentatives restantes')
        
    if user_connected is None:
        print('\nNombre de tentatives dépassé')
        break
    
    while True:
        display_menu()

        choice = input('Choisissez une option valide : ').strip()

        match choice:
            case '1':
                add_category()
            case '2':
                add_product()
            case '3':
                add_stock()
            case '4':
                remove_stock()
            case '5':
                display_categories()
            case '6':
                display_products()
            case '7':
                show_history()
            case '8':
                print('\n------- Gestion des utilisateurs -------')
                print('1. Ajouter un utilisateur')
                print('2. Lister les utilisateurs')

                option = input('Choisissez une option valide : ').strip().lower()
                if option == '1':
                    create_user()
                elif option == '2':
                    list_all_users()
                else:
                    print('Option invalide')
            case '0':
                print(f'\nJajeuf {user_connected['username']} !')
                user_connected = None
                break
            case _:
                print('Choix invalide')