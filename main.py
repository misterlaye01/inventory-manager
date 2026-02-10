# https://github.com/misterlaye01/inventory-manager.git

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()

DEFAULT_DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ['DB_USER'],
    'password': os.environ['DB_PASSWORD'],
    'database': os.environ['DB_NAME'],
    'port': int(os.environ.get('DB_PORT', '3306'))
}

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

def add_category():
    """ Ajoute une nouvelle catégorie """
    
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
        cur.execute('SELECT * FROM categories ORDER BY category_name')
        categories = cur.fetchall()

        if not categories:
            print('Aucune catégorie enregistrée')
            return
        
        for cat in categories:
            print(f'{cat['id']} : {cat['category_name']}')
    except Error as e:
        print(f"Erreur lors de l'affichage des catégories : {e}")
    finally:
        cur.close()
        cnx.close()

def add_product():
    """ Ajoute un produit """

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
            print(f'{prod['id']} - {prod['product_name']} - {prod['quantity']} - {prod['category_name']}')
    except Error as e:
        print(f"Erreur lors de l'affichage des produits : {e}")
    finally:
        cur.close()
        cnx.close()

def add_stock():
    """ Enregistre une entrée pour un produit existant """

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
            print(f'{histo['product_name']} - {histo['quantity']} - {histo['type']} - {histo['date'].strftime('%d/%m/%Y %H:%M')}')
    except Error as e:
        print(f"Erreur lors de l'affichage de l'historique : {e}")
    finally:
        cur.close()
        cnx.close()



# ---------- PROGRAMME PRINCIPAL ----------
create_tables()

while True:
    print(
        """ 
        1. Ajouter catégorie
        2. Ajouter produit
        3. Entrée stock
        4. Sortie stock
        5. Liste produits
        6. Historique
        0. Quitter
        """
    )

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
            display_products()
        case '6':
            show_history()
        case '0':
            break
        case _:
            print('Choix invalide')