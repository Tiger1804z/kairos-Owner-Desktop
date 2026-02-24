# Kairos — Owner Desktop

Application **desktop** pour propriétaires de business, connectée directement à la base de données **Kairos (PostgreSQL sur Neon)**.

Ce module permet de gérer **Businesses, Clients, Engagements, Transactions**, avec des **statistiques visuelles** et un **export CSV**, en travaillant directement sur la base Kairos existante.

---

## Objectif du projet

L'objectif est de fournir un **Owner Desktop** permettant à un propriétaire :

- De gérer plusieurs **businesses**
- De gérer les **clients** d'une business
- De créer des **engagements** (commandes, contrats, projets) avec leurs **items**
- D'enregistrer des **transactions** financières (revenus et dépenses)
- De visualiser des **statistiques** avec des graphiques matplotlib
- D'**exporter** ses données en CSV pour Excel ou pour l'IA Kairos

**Aucun SQL à écrire — Aucune table mock — Connexion directe à la DB réelle (Neon)**

---

## Stack technique

- **Python 3.11+**
- **PyQt6** (application desktop)
- **PostgreSQL (Neon)**
- **matplotlib** (graphiques intégrés dans l'UI)
- Architecture **Repo / Mixin / Form / UI**
- **Decimal** pour tous les montants (jamais float)

---

## Structure du projet

```text
.
├── db/
│   ├── connection.py              # Connexion PostgreSQL (Neon)
│   ├── auth_repo.py               # Authentification user
│   ├── business_repo.py           # Businesses (CRUD)
│   ├── client_repo.py             # Clients (CRUD)
│   ├── engagement_repo.py         # Engagements (CRUD + recalcul total)
│   ├── engagement_item_repo.py    # Engagement items (CRUD)
│   └── transaction_repo.py        # Transactions (CRUD + statistiques)
│
├── ui/
│   ├── dashboard_window.py        # Fenêtre principale + __init__ (onglets)
│   ├── dashboard_helpers.py       # Mixin : helpers partagés, toolbar, combo business
│   ├── dashboard_businesses.py    # Mixin : onglet Businesses + boutons export
│   ├── dashboard_clients.py       # Mixin : onglet Clients
│   ├── dashboard_engagements.py   # Mixin : onglet Engagements + Items
│   ├── dashboard_transactions.py  # Mixin : onglet Transactions
│   ├── dashboard_stats.py         # Mixin : onglet Statistiques (matplotlib)
│   ├── login_window.py            # Écran de login
│   ├── business_form.py           # Modale CRUD business
│   ├── client_form.py             # Modale CRUD client
│   ├── engagement_form.py         # Modale CRUD engagement
│   ├── item_form.py               # Modale CRUD item
│   ├── transaction_form.py        # Modale CRUD transaction
│   └── style.qss                  # Thème dark global
│
├── utils/
│   ├── ui_helpers.py              # WaitCursor, show_error, show_success
│   └── export_utils.py            # Logique export CSV (sans dépendance PyQt6)
│
├── assets/
│   └── kairos_logo(3).png
│
├── main.py                        # Point d'entrée
├── plan.md                        # Plan d'architecture Phase 2
└── README.md
```

### Pourquoi le dashboard est découpé en Mixins ?

`dashboard_window.py` aurait dépassé **2000 lignes** en intégrant les 5 onglets en un seul fichier. Pour garder le code maintenable, chaque onglet a été extrait dans un **fichier Mixin** séparé (`dashboard_businesses.py`, `dashboard_clients.py`, etc.).

`DashboardWindow` hérite de tous ces mixins — Python résout `self` correctement dans chaque mixin. Le `__init__` reste dans `dashboard_window.py` et gère la construction de l'UI.

---

## Authentification

- Connexion avec un user **owner** existant en DB
- Rôle et statut vérifiés
- Nom du user affiché dans le top bar

---

## Flow général

1. **Login**
2. **Sélection de la business active** (combo dans le header)
3. **Accès aux onglets** — toutes les données sont scopées par la business sélectionnée :
   - Businesses
   - Clients
   - Engagements + Items
   - Transactions
   - Statistiques

---

## Businesses

- CRUD complet (créer / modifier / supprimer)
- Sélection de la business active via le combo dans le header
- **Boutons export CSV** dans la barre (activés quand une business est sélectionnée)

---

## Clients

- CRUD complet, liés à une business
- Bouton "Voir engagements" pour filtrer les engagements par client

---

## Engagements

Un engagement = commande, contrat ou projet.

- CRUD complet avec filtrage par client
- Statuts : `draft`, `active`, `completed`, `cancelled`
- Total calculé automatiquement à partir des items

### Items

- CRUD complet
- `line_total = quantity × unit_price` calculé automatiquement
- Chaque ajout / modification / suppression recalcule le total de l'engagement

---

## Transactions

Une transaction = mouvement d'argent réel (revenu ou dépense).

- CRUD complet
- Types : `income` (vert) / `expense` (rouge)
- Filtre Tous / Revenus / Dépenses
- Balance affichée en temps réel (verte si positive, rouge si négative)
- Lien optionnel avec un client ou un engagement

---

## Statistiques

Tableau de bord visuel avec **graphiques matplotlib intégrés dans PyQt6**.

- **Labels** : Revenus totaux, Dépenses totales, Balance (colorée)
- **Graphique 1** : Barres revenus vs dépenses par mois (12 derniers mois)
- **Graphique 2** : Camembert des dépenses par catégorie (tranches < 3% regroupées en "Autres")
- Bouton Rafraîchir — rechargement automatique au changement de business

---

## Export CSV

Deux exports disponibles depuis l'onglet Businesses :

| Fichier | Colonnes | Usage |
|---------|----------|-------|
| `{business}_transactions_{date}.csv` | date, type, amount, payment_method, category, client_name, description | Excel / comptable / analyse IA Kairos |
| `{business}_clients_engagements_{date}.csv` | client_name, company, email, phone, engagement_title, status, total_amount, start_date, end_date | Vue d'ensemble / archive |

- Encodage `utf-8-sig` — accents affichés correctement dans Excel Windows
- La logique d'export est dans `utils/export_utils.py` (aucune dépendance PyQt6)

---

## Lancer le projet

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Créer le fichier .env à la racine
DATABASE_URL=postgresql://user:password@host/database?sslmode=require

# 3. Lancer
python main.py
```

---

## Auteur

**Sébastien Eugène**
Projet Kairos — Owner Desktop
Collège de Maisonneuve — Laboratoire 2, Application Bureau
