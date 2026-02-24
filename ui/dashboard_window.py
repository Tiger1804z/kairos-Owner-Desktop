"""
KAIROS Owner Desktop - Tableau de bord principal
- Tab 1: Businesses (CRUD)
- Tab 2: Clients (CRUD) liés à la business sélectionnée
- Tab 3: Engagements (CRUD) liés à la business sélectionnée (option filtre client)
         + Engagement Items (CRUD) liés à l'engagement sélectionné
- Tab 4: Transactions (CRUD) liées à la business sélectionnée
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QHBoxLayout,
    QPushButton,
    QAbstractItemView,
    QSizePolicy,
    QHeaderView,
    QTabWidget,
    QComboBox,
    QFrame,
)
from PyQt6.QtGui import QIcon

from db.auth_repo import AuthUser

# ─── Mixins ──────────────────────────────────────────────────────────────────
from ui.dashboard_helpers import SharedHelpersMixin
from ui.dashboard_businesses import BusinessesMixin
from ui.dashboard_clients import ClientsMixin
from ui.dashboard_engagements import EngagementsMixin
from ui.dashboard_transactions import TransactionsMixin
from ui.dashboard_stats import StatsMixin


class DashboardWindow(
    QWidget,
    SharedHelpersMixin,
    BusinessesMixin,
    ClientsMixin,
    EngagementsMixin,
    TransactionsMixin,
    StatsMixin,
):
    def __init__(self, user: AuthUser):
        super().__init__()
        self.user = user

        self.selected_business_id: int | None = None
        self.selected_client_id: int | None = None
        self.engagement_client_filter: int | None = None
        self.selected_engagement_id: int | None = None
        self.selected_transaction_id: int | None = None

        # Defensive: avoid "None None"
        first = (user.first_name or "").strip()
        last = (user.last_name or "").strip()
        self.full_name = (first + " " + last).strip() or user.email

        self.setWindowTitle("Owner Desktop — Dashboard")
        self.setMinimumWidth(900)
        self.setMinimumHeight(520)

        icon = QIcon("assets/kairos_logo(3).png")
        if not icon.isNull():
            self.setWindowIcon(icon)

        root = QVBoxLayout()
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        header = QLabel(f"Bienvenue, {self.full_name}!")
        header.setStyleSheet("font-size: 16px; font-weight: 600;")
        root.addWidget(header)

        toolbar = self.build_toolbar()
        root.addWidget(toolbar)

        # Tabs container
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        # =========================
        # TAB: BUSINESSES
        # =========================
        self.tab_businesses = QWidget()
        biz_layout = QVBoxLayout(self.tab_businesses)
        biz_layout.setContentsMargins(0, 0, 0, 0)
        biz_layout.setSpacing(10)

        biz_actions = QHBoxLayout()

        self.btn_add = QPushButton("➕ Ajouter")
        self.btn_delete = QPushButton("🗑️ Supprimer")
        self.btn_refresh = QPushButton("🔄 Rafraîchir")

        self.btn_delete.setEnabled(False)

        self.btn_add.setObjectName("btnPrimary")
        self.btn_delete.setObjectName("btnDanger")
        self.btn_refresh.setObjectName("btnNeutral")

        self.btn_add.clicked.connect(self.on_add_business)
        self.btn_delete.clicked.connect(self.on_delete_business)
        self.btn_refresh.clicked.connect(self.refresh_businesses)

        biz_actions.addWidget(self.btn_add)
        biz_actions.addWidget(self.btn_delete)
        biz_actions.addWidget(self.btn_refresh)
        
        biz_actions.addStretch(1)
        self.btn_export_tx = QPushButton("📤 Transactions CSV")
        self.btn_export_clients_eng = QPushButton("📤 Clients/Engagements CSV")
        self.btn_export_tx.setObjectName("btnNeutral")
        self.btn_export_clients_eng.setObjectName("btnNeutral")
        self.btn_export_tx.setEnabled(False)
        self.btn_export_clients_eng.setEnabled(False)
        self.btn_export_tx.clicked.connect(self.on_export_transactions)
        self.btn_export_clients_eng.clicked.connect(self.on_export_clients_engagements)
        biz_actions.addWidget(self.btn_export_tx)
        biz_actions.addWidget(self.btn_export_clients_eng)
        
        
        biz_layout.addLayout(biz_actions)

        self.biz_table = QTableWidget()
        self.biz_table.setColumnCount(7)
        self.biz_table.setHorizontalHeaderLabels(
            ["ID", "Nom", "Type", "Ville", "Pays", "Devise", "Actif"]
        )

        self.biz_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.biz_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.biz_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.biz_table.setSortingEnabled(True)
        self.biz_table.setAlternatingRowColors(True)

        self.biz_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.biz_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.biz_table.cellDoubleClicked.connect(self.on_business_double_click)
        self.biz_table.itemSelectionChanged.connect(self.on_business_selection_changed)
        self.biz_table.itemSelectionChanged.connect(self.on_business_selected_for_clients)

        biz_layout.addWidget(self.biz_table, 1)

        self.tab_businesses_idx = self.tabs.addTab(self.tab_businesses, "Businesses")

        # =========================
        # TAB: CLIENTS
        # =========================
        self.tab_clients = QWidget()
        clients_layout = QVBoxLayout(self.tab_clients)
        clients_layout.setContentsMargins(0, 0, 0, 0)
        clients_layout.setSpacing(10)

        clients_actions = QHBoxLayout()

        self.btn_client_add = QPushButton("➕ Ajouter")
        self.btn_client_delete = QPushButton("🗑️ Supprimer")
        self.btn_client_refresh = QPushButton("🔄 Rafraîchir")

        self.btn_client_view_eng = QPushButton("Voir engagements")
        self.btn_client_view_eng.clicked.connect(self.on_view_engagements_for_selected_client)

        self.btn_client_add.setObjectName("btnPrimary")
        self.btn_client_delete.setObjectName("btnDanger")
        self.btn_client_refresh.setObjectName("btnNeutral")

        self.btn_client_delete.setEnabled(False)

        self.btn_client_add.clicked.connect(self.on_add_client)
        self.btn_client_delete.clicked.connect(self.on_delete_client)
        self.btn_client_refresh.clicked.connect(self.refresh_clients)

        clients_actions.addWidget(self.btn_client_add)
        clients_actions.addWidget(self.btn_client_delete)
        clients_actions.addWidget(self.btn_client_refresh)
        clients_actions.addStretch(1)
        clients_actions.addWidget(self.btn_client_view_eng)
        clients_layout.addLayout(clients_actions)

        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(7)
        self.clients_table.setHorizontalHeaderLabels(
            ["ID", "Prénom", "Nom", "Entreprise", "Email", "Téléphone", "Actif"]
        )

        self.clients_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.clients_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.clients_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.clients_table.setSortingEnabled(True)
        self.clients_table.setAlternatingRowColors(True)

        self.clients_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.clients_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.clients_table.itemSelectionChanged.connect(self.on_client_selection_changed)
        self.clients_table.cellDoubleClicked.connect(self.on_client_double_click)

        clients_layout.addWidget(self.clients_table, 1)

        self.tab_clients_idx = self.tabs.addTab(self.tab_clients, "Clients")
        self.tabs.setTabEnabled(self.tab_clients_idx, False)

        # =========================
        # TAB: ENGAGEMENTS
        # =========================
        self.tab_engagements = QWidget()
        eng_layout = QVBoxLayout(self.tab_engagements)
        eng_layout.setContentsMargins(0, 0, 0, 0)
        eng_layout.setSpacing(10)

        lbl_eng_title = QLabel("Engagements")
        lbl_eng_title.setStyleSheet("font-size: 14px; font-weight: 700;")
        eng_layout.addWidget(lbl_eng_title)

        header_row = QHBoxLayout()
        self.lbl_eng_filter = QLabel("Filtre: Business (tous les engagements)")
        self.btn_eng_clear_filter = QPushButton("Clear filtre client")
        self.btn_eng_clear_filter.clicked.connect(self.on_clear_engagement_client_filter)
        header_row.addWidget(self.lbl_eng_filter)
        header_row.addStretch(1)
        header_row.addWidget(self.btn_eng_clear_filter)
        eng_layout.addLayout(header_row)

        eng_actions = QHBoxLayout()
        self.btn_eng_add = QPushButton("➕ Ajouter")
        self.btn_eng_delete = QPushButton("🗑️ Supprimer")
        self.btn_eng_refresh = QPushButton("🔄 Rafraîchir")

        self.btn_eng_add.clicked.connect(self.on_engagement_add)
        self.btn_eng_delete.clicked.connect(self.on_engagement_delete)
        self.btn_eng_refresh.clicked.connect(self.refresh_engagements)

        self.btn_eng_delete.setEnabled(False)

        eng_actions.addWidget(self.btn_eng_add)
        eng_actions.addWidget(self.btn_eng_delete)
        eng_actions.addWidget(self.btn_eng_refresh)
        eng_layout.addLayout(eng_actions)

        self.eng_table = QTableWidget()
        self.eng_table.setColumnCount(8)
        self.eng_table.setHorizontalHeaderLabels(
            ["ID", "ClientID", "Titre", "Status", "Description", "Start", "End", "Total"]
        )

        self.eng_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.eng_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.eng_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.eng_table.setSortingEnabled(True)
        self.eng_table.setAlternatingRowColors(True)
        self.eng_table.setWordWrap(False)

        hdr = self.eng_table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for idx in [0, 1, 3, 5, 6, 7]:
            hdr.setSectionResizeMode(idx, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        self.eng_table.itemSelectionChanged.connect(self.on_engagement_selection_changed)
        self.eng_table.itemSelectionChanged.connect(self.on_engagement_selection_btn_state)
        self.eng_table.cellDoubleClicked.connect(self.on_engagement_double_click)

        eng_layout.addWidget(self.eng_table, 1)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("color: #333;")
        eng_layout.addWidget(sep)

        items_header = QHBoxLayout()
        self.lbl_items_title = QLabel("Items — Sélectionne un engagement")
        self.lbl_items_title.setStyleSheet("font-size: 13px; font-weight: 650;")
        items_header.addWidget(self.lbl_items_title)
        items_header.addStretch(1)
        eng_layout.addLayout(items_header)

        items_actions = QHBoxLayout()
        self.btn_item_add = QPushButton("➕ Ajouter item")
        self.btn_item_delete = QPushButton("🗑️ Supprimer item")
        self.btn_item_add.clicked.connect(self.on_item_add)
        self.btn_item_delete.clicked.connect(self.on_item_delete)
        self.btn_item_delete.setEnabled(False)

        items_actions.addWidget(self.btn_item_add)
        items_actions.addWidget(self.btn_item_delete)
        eng_layout.addLayout(items_actions)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels(
            ["ID", "Nom", "Type", "Qty", "Unit price", "Line total", "BusinessID"]
        )

        self.items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.items_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.items_table.setSortingEnabled(True)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setWordWrap(False)

        hdr2 = self.items_table.horizontalHeader()
        hdr2.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for idx in [0, 2, 3, 4, 5, 6]:
            hdr2.setSectionResizeMode(idx, QHeaderView.ResizeMode.ResizeToContents)
        hdr2.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.items_table.itemSelectionChanged.connect(self.on_item_selection_btn_state)
        self.items_table.cellDoubleClicked.connect(self.on_item_double_click)

        eng_layout.addWidget(self.items_table, 1)

        self.tab_engagements_idx = self.tabs.addTab(self.tab_engagements, "Engagements")
        self.tabs.setTabEnabled(self.tab_engagements_idx, False)

        # =========================
        # TAB: TRANSACTIONS
        # =========================
        self.tab_transactions = QWidget()
        tx_layout = QVBoxLayout(self.tab_transactions)
        tx_layout.setContentsMargins(0, 0, 0, 0)
        tx_layout.setSpacing(10)

        tx_top = QHBoxLayout()

        self.btn_tx_add = QPushButton("➕ Ajouter")
        self.btn_tx_delete = QPushButton("🗑️ Supprimer")
        self.btn_tx_refresh = QPushButton("🔄 Rafraîchir")
        self.btn_tx_delete.setEnabled(False)

        self.btn_tx_add.setObjectName("btnPrimary")
        self.btn_tx_delete.setObjectName("btnDanger")
        self.btn_tx_refresh.setObjectName("btnNeutral")

        self.btn_tx_add.clicked.connect(self.on_add_transaction)
        self.btn_tx_delete.clicked.connect(self.on_delete_transaction)
        self.btn_tx_refresh.clicked.connect(self.refresh_transactions)

        # Filtre type
        self.cb_tx_filter = QComboBox()
        self.cb_tx_filter.addItems(["Tous", "Revenus", "Dépenses"])
        self.cb_tx_filter.currentIndexChanged.connect(self.refresh_transactions)

        # Label balance
        self.lbl_balance = QLabel("Balance : —")
        self.lbl_balance.setStyleSheet("font-weight: bold; font-size: 13px;")

        tx_top.addWidget(self.btn_tx_add)
        tx_top.addWidget(self.btn_tx_delete)
        tx_top.addWidget(self.btn_tx_refresh)
        tx_top.addWidget(QLabel("Afficher :"))
        tx_top.addWidget(self.cb_tx_filter)
        tx_top.addStretch(1)
        tx_top.addWidget(self.lbl_balance)
        tx_layout.addLayout(tx_top)

        self.tx_table = QTableWidget()
        self.tx_table.setColumnCount(7)
        self.tx_table.setHorizontalHeaderLabels(
            ["ID", "Date", "Type", "Montant", "Client", "Catégorie", "Description"]
        )
        self.tx_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tx_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tx_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tx_table.setSortingEnabled(True)
        self.tx_table.setAlternatingRowColors(True)
        self.tx_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tx_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.tx_table.itemSelectionChanged.connect(self.on_tx_selection_changed)
        self.tx_table.cellDoubleClicked.connect(self.on_tx_double_click)

        tx_layout.addWidget(self.tx_table, 1)

        self.tab_transactions_idx = self.tabs.addTab(self.tab_transactions, "Transactions")
        self.tabs.setTabEnabled(self.tab_transactions_idx, False)
        
        # =========================
        # TAB: STATISTIQUES
        # =========================
        self.tab_stats_idx = self.tabs.addTab(self.build_stats_tab(), "Statistiques")
        self.tabs.setTabEnabled(self.tab_stats_idx, False)


        # =========================
        # Status
        # =========================
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #aaa; padding: 6px;")
        root.addWidget(self.status_label)

        self.setLayout(root)

        # initial load
        self.refresh_businesses()
        self.load_businesses_into_combo()
        self.refresh_clients()
        self.refresh_engagements()
