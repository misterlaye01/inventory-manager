# Mini Gestionnaire de Stock en Python (CLI + MySQL)

## Description

Ce projet est un mini gestionnaire de stock en ligne de commande (CLI) développé en **Python**, utilisant **MySQL** comme base de données.

Il permet de :

- Gérer des **catégories**
- Ajouter des **produits**
- Enregistrer des **entrées** et **sorties de stock**
- Consulter la **liste des produits**
- Visualiser l’**historique complet des mouvements**

Le programme crée automatiquement les tables nécessaires au démarrage.

---

## 🛠️ Technologies utilisées

- **Python 3.12.3**
- **MySQL**
- `mysql-connector-python`
- `python-dotenv`

---


## 📂 Structure de la base de données

Le programme crée automatiquement 3 tables :

### 1️⃣ `categories`

| Champ         | Type          | Description                      |
|--------------|--------------|----------------------------------|
| id           | INT (PK)     | Identifiant unique               |
| category_name| VARCHAR(32)  | Nom unique de la catégorie       |

---

### 2️⃣ `products`

| Champ        | Type        | Description                          |
|-------------|------------|--------------------------------------|
| id          | INT (PK)   | Identifiant unique                   |
| product_name| VARCHAR(32)| Nom du produit                       |
| quantity    | INT        | Stock actuel                         |
| category_id | INT (FK)   | Référence vers `categories(id)`      |

🔗 Contrainte :
- `ON DELETE CASCADE` → Supprimer une catégorie supprime ses produits.

---

### 3️⃣ `history`

| Champ      | Type        | Description                              |
|------------|------------|------------------------------------------|
| id         | INT (PK)   | Identifiant unique                       |
| quantity   | INT        | Quantité ajoutée ou retirée              |
| type       | VARCHAR(10)| `ENTRÉE` ou `SORTIE`                     |
| date       | DATETIME   | Date du mouvement                        |
| product_id | INT (FK)   | Référence vers `products(id)`            |

---

## ⚙️ Installation

### 1️⃣ Cloner le projet

```bash
git clone https://github.com/misterlaye01/inventory-manager.git
cd inventory-manager/
