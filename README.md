# 🧠 Kairos — Owner Desktop

Application **desktop** pour propriétaires de business, connectée directement à la base de données **Kairos (PostgreSQL sur Neon)**.

Ce module permet de gérer **Businesses, Clients, Engagements et Engagement Items**, avec une logique **réelle**, cohérente, et utilisable dans un vrai contexte business (pas juste un CRUD scolaire).

---

## 🎯 Objectif du projet

L'objectif de ce projet est de fournir un **Owner Desktop** permettant à un propriétaire :

- De gérer plusieurs **businesses**
- De gérer les **clients** d'une business
- De créer des **engagements** (commandes, contrats, projets)
- D'ajouter des **items réels** (produits / services)
- D'avoir un **total automatiquement calculé** à partir des items
- De travailler **directement sur la base Kairos existante**

👉 **Aucun SQL à écrire**  
👉 **Aucune table mock**  
👉 Connexion directe à la DB réelle (**Neon**)

---

## 🧱 Stack technique

- **Python 3.11+**
- **PyQt6** (application desktop)
- **PostgreSQL (Neon)**
- Architecture **Repo / Form / UI**
- **Decimal** pour les montants (évite les erreurs de float)

---

## 📁 Structure du projet

```text
.
├── db/
│   ├── connection.py              # Connexion PostgreSQL (Neon)
│   ├── auth_repo.py               # Auth user
│   ├── business_repo.py           # Businesses (CRUD)
│   ├── client_repo.py             # Clients (CRUD)
│   ├── engagement_repo.py         # Engagements (CRUD + total)
│   └── engagement_item_repo.py    # Engagement items (CRUD)
│
├── ui/
│   ├── dashboard_window.py        # Interface principale
│   ├── login_window.py            # Écran de login
│   ├── engagement_form.py         # Form engagement
│   ├── item_form.py               # Form item
│   ├── business_form.py           # Form business
│   └── client_form.py             # Form client
│
├── assets/
│   └── kairos_logo.png
│
├── style.qss                      # Thème UI
├── main.py                        # Point d'entrée
└── README.md
```

---

## 🔐 Authentification

- Connexion avec un user **owner** existant
- Les infos du user sont chargées depuis la DB
- Le rôle et le statut sont respectés
- Le nom du user apparaît dans le top bar

---

## 🧭 Flow général de l'application

1. **Login**
2. **Sélection de la business active**
3. **Accès aux onglets** :
   - Businesses
   - Clients
   - Engagements

➡️ Toutes les données affichées sont liées à la **business sélectionnée**

---

## 🏢 Businesses

### Fonctionnalités
- Créer / modifier / supprimer une business
- Sélectionner la business active via le combo dans le header
- Toutes les autres données dépendent de cette sélection

### Champs principaux
- Nom
- Type
- Ville / Pays
- Devise
- Statut actif

---

## 👥 Clients

### Fonctionnalités
- CRUD complet des clients
- Clients liés à une business
- Bouton "Voir engagements" pour filtrer les engagements par client

### Champs
- Prénom / Nom
- Entreprise
- Email / Téléphone
- Statut actif

---

## 📄 Engagements

Un engagement représente une **commande**, un **contrat** ou un **projet**.

### Fonctionnalités
- CRUD complet
- Filtrage par client
- Double-clic pour éditer
- Statuts visuels :
  - `draft`
  - `active`
  - `completed`
  - `cancelled`

### Champs
- Client (optionnel)
- Titre
- Status
- Description
- Date début / fin
- Total (calculé automatiquement)

---

## 📦 Engagement Items

Les items sont les **lignes réelles** de l'engagement (produits ou services).

### Fonctionnalités
- CRUD complet
- Calcul automatique :
  ```
  line_total = quantity × unit_price
  ```
- Chaque ajout / modification / suppression :  
  👉 recalcule automatiquement le total de l'engagement

### Champs
- Nom
- Type (product ou service)
- Quantité
- Prix unitaire
- Total de ligne

---





## 🚀 Lancer le projet

### 1. Cloner le repo
```bash
git clone <repo_url>
cd kairos-owner-desktop
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Configurer la DB (Neon)
Créer un fichier `.env` à la racine avec :
```
DATABASE_URL=postgresql://user:password@host/database?sslmode=require
```

### 4. Lancer l'application
```bash
python main.py
```

---

## 🧠 Notes importantes

- Le projet utilise la **DB Kairos existante**
- **Aucun changement de schéma requis**
- Toute la logique respecte strictement le schéma réel
- Le projet est pensé pour évoluer vers :
  - Facturation
  - Export PDF
  - Rapports
  - Version web plus tard

---

## ✍️ Auteur

**Sébastien Eugène**  
Projet Kairos — Owner Desktop  
