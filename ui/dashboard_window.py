"""
KAIROS Owner Desktop - Tableau de bord principal
- Tab 1: Businesses (CRUD)
- Tab 2: Clients (CRUD) liés à la business sélectionnée
- Tab 3: Engagements (CRUD) liés à la business sélectionnée (option filtre client)
         + Engagement Items (CRUD) liés à l’engagement sélectionné
"""

from __future__ import annotations

from decimal import Decimal

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHBoxLayout,
    QPushButton,
    QAbstractItemView,
    QSizePolicy,
    QHeaderView,
    QTabWidget,
    QComboBox,
    QFrame,
    QMenu,
)
from PyQt6.QtGui import QPixmap, QAction, QIcon

from db.auth_repo import AuthUser
from db.business_repo import list_businesses, update_business, delete_business, create_business
from db.client_repo import list_clients, create_client, update_client, delete_client

# ✅ engagement + items repos (conformes schema)
from db.engagement_repo import list_engagements, create_engagement, update_engagement, delete_engagement
from db.engagement_item_repo import list_items, create_item, update_item, delete_item

# ✅ forms conformes schema
from ui.engagement_form import EngagementForm
from ui.item_form import ItemForm

from ui.business_form import BusinessForm
from ui.client_form import ClientForm


class DashboardWindow(QWidget):
    def __init__(self, user: AuthUser):
        super().__init__()
        self.user = user

        self.selected_business_id: int | None = None
        self.selected_client_id: int | None = None
        self.engagement_client_filter: int | None = None
        self.selected_engagement_id: int | None = None

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

    # =========================
    # BUSINESS: CRUD + selection
    # =========================
    def refresh_businesses(self) -> None:
        businesses = list_businesses(self.user.id_user)

        was_sorting = self.biz_table.isSortingEnabled()
        self.biz_table.setSortingEnabled(False)

        self.biz_table.setRowCount(len(businesses))
        for row_idx, b in enumerate(businesses):
            self.biz_table.setItem(row_idx, 0, QTableWidgetItem(str(b.id_business)))
            self.biz_table.setItem(row_idx, 1, QTableWidgetItem(b.name or ""))
            self.biz_table.setItem(row_idx, 2, QTableWidgetItem(b.business_type or ""))
            self.biz_table.setItem(row_idx, 3, QTableWidgetItem(b.city or ""))
            self.biz_table.setItem(row_idx, 4, QTableWidgetItem(b.country or ""))
            self.biz_table.setItem(row_idx, 5, QTableWidgetItem(b.currency or ""))
            self.biz_table.setItem(row_idx, 6, QTableWidgetItem("Oui" if b.is_active else "Non"))

        self.biz_table.setSortingEnabled(was_sorting)
        self.set_status(f"📄 {len(businesses)} business(es) chargée(s).")

        if self.selected_business_id is not None:
            ids = {b.id_business for b in businesses}
            if self.selected_business_id not in ids:
                self.selected_business_id = None
                self.selected_client_id = None
                self.engagement_client_filter = None
                self.selected_engagement_id = None
                self.refresh_clients()
                self.refresh_engagements()

        self.load_businesses_into_combo(keep_selection=True)
        self.update_window_title()

    def on_business_selection_changed(self) -> None:
        self.btn_delete.setEnabled(self.biz_table.currentRow() >= 0)

    def on_business_selected_for_clients(self) -> None:
        row = self.biz_table.currentRow()

        if row < 0:
            self.selected_business_id = None
            self.selected_client_id = None
            self.engagement_client_filter = None
            self.selected_engagement_id = None

            self.tabs.setTabEnabled(self.tab_clients_idx, False)
            self.tabs.setTabEnabled(self.tab_engagements_idx, False)

            self.clients_table.setRowCount(0)
            self.eng_table.setRowCount(0)
            self.items_table.setRowCount(0)

            self.set_status("ℹ️ Sélectionner une business (onglet Businesses) pour voir ses clients/engagements.")
            self.update_window_title()
            return

        item = self.biz_table.item(row, 0)
        if not item:
            return

        self.selected_business_id = int(item.text())
        self.selected_client_id = None
        self.engagement_client_filter = None
        self.selected_engagement_id = None

        self.tabs.setTabEnabled(self.tab_clients_idx, True)
        self.tabs.setTabEnabled(self.tab_engagements_idx, True)

        self.tabs.setCurrentIndex(self.tab_clients_idx)

        self.select_business_in_combo(self.selected_business_id)

        self.refresh_clients()
        self.refresh_engagements()
        self.update_window_title()

    def on_business_double_click(self, row: int, col: int) -> None:
        item_id = self.biz_table.item(row, 0)
        if not item_id:
            return

        id_business = int(item_id.text())
        initial = {
            "name": self.biz_table.item(row, 1).text() if self.biz_table.item(row, 1) else "",
            "business_type": self.biz_table.item(row, 2).text() if self.biz_table.item(row, 2) else "",
            "city": self.biz_table.item(row, 3).text() if self.biz_table.item(row, 3) else "",
            "country": self.biz_table.item(row, 4).text() if self.biz_table.item(row, 4) else "",
            "currency": self.biz_table.item(row, 5).text() if self.biz_table.item(row, 5) else "CAD",
            "timezone": "America/Montreal",
            "is_active": (
                (self.biz_table.item(row, 6).text().lower() if self.biz_table.item(row, 6) else "")
                in ("oui", "true", "1")
            ),
        }

        dlg = BusinessForm(self, initial=initial)
        if dlg.exec():
            data = dlg.get_data()
            if not data.get("name"):
                QMessageBox.warning(self, "Erreur", "Le nom est requis.")
                return
            try:
                update_business(self.user.id_user, id_business, data)
                self.set_status("💾 Business mise à jour.")
                self.refresh_businesses()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def on_add_business(self) -> None:
        dlg = BusinessForm(
            self,
            initial={"currency": "CAD", "timezone": "America/Montreal", "is_active": True},
        )
        if dlg.exec():
            data = dlg.get_data()
            if not data.get("name"):
                QMessageBox.warning(self, "Erreur", "Le nom est requis.")
                return
            try:
                create_business(
                    owner_id=self.user.id_user,
                    name=data["name"],
                    business_type=data.get("business_type"),
                    city=data.get("city"),
                    country=data.get("country"),
                    currency=data.get("currency") or "CAD",
                    timezone=data.get("timezone") or "America/Montreal",
                    is_active=bool(data.get("is_active", True)),
                )
                self.set_status("✅ Business ajoutée.")
                self.refresh_businesses()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def on_delete_business(self) -> None:
        row = self.biz_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Info", "Sélectionner une business à supprimer.")
            return

        id_business = int(self.biz_table.item(row, 0).text())
        name = self.biz_table.item(row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirmer suppression",
            f"Supprimer la business '{name}' (ID {id_business}) ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            ok = delete_business(self.user.id_user, id_business)
            if not ok:
                QMessageBox.warning(self, "Refusé", "Suppression impossible (non autorisé ou introuvable).")
                return

            if self.selected_business_id == id_business:
                self.selected_business_id = None
                self.selected_client_id = None
                self.engagement_client_filter = None
                self.selected_engagement_id = None

            self.set_status("🗑️ Business supprimée.")
            self.refresh_businesses()
            self.refresh_clients()
            self.refresh_engagements()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    # =========================
    # CLIENTS: CRUD
    # =========================
    def refresh_clients(self) -> None:
        self.clients_table.setRowCount(0)
        self.btn_client_delete.setEnabled(False)
        self.selected_client_id = None

        if not self.selected_business_id:
            self.set_status("ℹ️ Sélectionner une business (onglet Businesses) pour voir ses clients.")
            return

        clients = list_clients(self.selected_business_id)

        was_sorting = self.clients_table.isSortingEnabled()
        self.clients_table.setSortingEnabled(False)

        self.clients_table.setRowCount(len(clients))
        for i, c in enumerate(clients):
            self.clients_table.setItem(i, 0, QTableWidgetItem(str(c.id_client)))
            self.clients_table.setItem(i, 1, QTableWidgetItem(c.first_name or ""))
            self.clients_table.setItem(i, 2, QTableWidgetItem(c.last_name or ""))
            self.clients_table.setItem(i, 3, QTableWidgetItem(c.company_name or ""))
            self.clients_table.setItem(i, 4, QTableWidgetItem(c.email or ""))
            self.clients_table.setItem(i, 5, QTableWidgetItem(c.phone or ""))
            self.clients_table.setItem(i, 6, QTableWidgetItem("Oui" if c.is_active else "Non"))

        self.clients_table.setSortingEnabled(was_sorting)
        self.set_status(f"👥 {len(clients)} client(s) chargé(s).")

    def on_client_selection_changed(self) -> None:
        row = self.clients_table.currentRow()
        self.btn_client_delete.setEnabled(row >= 0)

        if row < 0:
            self.selected_client_id = None
            return

        item = self.clients_table.item(row, 0)
        if not item or not item.text().strip():
            self.selected_client_id = None
            return

        self.selected_client_id = int(item.text())

    def on_add_client(self) -> None:
        if not self.selected_business_id:
            QMessageBox.information(self, "Info", "Sélectionner une business avant d’ajouter un client.")
            return

        dlg = ClientForm(self, initial={"is_active": True})
        if dlg.exec():
            data = dlg.get_data()
            if not (data.get("company_name") or data.get("first_name") or data.get("last_name")):
                QMessageBox.warning(self, "Erreur", "Entrer au minimum un nom ou une entreprise.")
                return

            try:
                create_client(
                    business_id=self.selected_business_id,
                    first_name=data.get("first_name"),
                    last_name=data.get("last_name"),
                    company_name=data.get("company_name"),
                    email=data.get("email"),
                    phone=data.get("phone"),
                    is_active=bool(data.get("is_active", True)),
                )
                self.set_status("✅ Client ajouté.")
                self.refresh_clients()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def on_delete_client(self) -> None:
        if not self.selected_business_id:
            return

        row = self.clients_table.currentRow()
        if row < 0:
            return

        id_client = int(self.clients_table.item(row, 0).text())

        label = (self.clients_table.item(row, 3).text() if self.clients_table.item(row, 3) else "").strip()
        if not label:
            fn = (self.clients_table.item(row, 1).text() if self.clients_table.item(row, 1) else "").strip()
            ln = (self.clients_table.item(row, 2).text() if self.clients_table.item(row, 2) else "").strip()
            label = (fn + " " + ln).strip() or f"ID {id_client}"

        confirm = QMessageBox.question(
            self,
            "Confirmer suppression",
            f"Supprimer le client '{label}' (ID {id_client}) ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            ok = delete_client(self.selected_business_id, id_client)
            if not ok:
                QMessageBox.warning(self, "Refusé", "Suppression impossible (introuvable).")
                return

            self.set_status("🗑️ Client supprimé.")
            self.refresh_clients()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def on_client_double_click(self, row: int, col: int) -> None:
        if not self.selected_business_id:
            return

        item_id = self.clients_table.item(row, 0)
        if not item_id:
            return

        id_client = int(item_id.text())
        initial = {
            "first_name": self.clients_table.item(row, 1).text() if self.clients_table.item(row, 1) else "",
            "last_name": self.clients_table.item(row, 2).text() if self.clients_table.item(row, 2) else "",
            "company_name": self.clients_table.item(row, 3).text() if self.clients_table.item(row, 3) else "",
            "email": self.clients_table.item(row, 4).text() if self.clients_table.item(row, 4) else "",
            "phone": self.clients_table.item(row, 5).text() if self.clients_table.item(row, 5) else "",
            "is_active": (
                (self.clients_table.item(row, 6).text().lower() if self.clients_table.item(row, 6) else "")
                in ("oui", "true", "1")
            ),
        }

        dlg = ClientForm(self, initial=initial)
        if dlg.exec():
            data = dlg.get_data()
            try:
                update_client(self.selected_business_id, id_client, data)
                self.set_status("💾 Client mis à jour.")
                self.refresh_clients()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    # =========================
    # ENGAGEMENTS + ITEMS 
    # =========================
    def update_engagement_filter_label(self) -> None:
        if self.engagement_client_filter is None:
            self.lbl_eng_filter.setText("Filtre: Business (tous les engagements)")
            self.btn_eng_clear_filter.setEnabled(False)
        else:
            self.lbl_eng_filter.setText(f"Filtre: Client ID = {self.engagement_client_filter}")
            self.btn_eng_clear_filter.setEnabled(True)

    def _fmt_dt(self, dt) -> str:
        if not dt:
            return ""
        try:
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return str(dt)

    def refresh_engagements(self, keep_selection: bool = False) -> None:
        keep_id = self.selected_engagement_id if keep_selection else None

        self.eng_table.setRowCount(0)
        self.items_table.setRowCount(0)
        self.btn_eng_delete.setEnabled(False)
        self.btn_item_delete.setEnabled(False)
        self.lbl_items_title.setText("Items — Sélectionne un engagement")

        if not keep_selection:
            self.selected_engagement_id = None

        if not self.selected_business_id:
            return

        self.update_engagement_filter_label()

        engagements = list_engagements(
            self.selected_business_id,
            client_id=self.engagement_client_filter,
        )

        was_sorting = self.eng_table.isSortingEnabled()
        self.eng_table.setSortingEnabled(False)

        self.eng_table.setRowCount(len(engagements))
        for i, e in enumerate(engagements):
            self.eng_table.setItem(i, 0, QTableWidgetItem(str(e.id_engagement)))
            self.eng_table.setItem(i, 1, QTableWidgetItem("" if e.client_id is None else str(e.client_id)))
            self.eng_table.setItem(i, 2, QTableWidgetItem(e.title or ""))

            # Status (color)
            status_txt = e.status or "draft"
            status_item = QTableWidgetItem(status_txt)
            status_item.setForeground(self._status_color(status_txt))
            self.eng_table.setItem(i, 3, status_item)

            # Description tooltip if long
            desc_txt = e.description or ""
            desc_item = QTableWidgetItem(desc_txt)
            if len(desc_txt) > 30:
                desc_item.setToolTip(desc_txt)
            self.eng_table.setItem(i, 4, desc_item)

            self.eng_table.setItem(i, 5, QTableWidgetItem(self._fmt_dt(e.start_date)))
            self.eng_table.setItem(i, 6, QTableWidgetItem(self._fmt_dt(e.end_date)))

            # Total (align right + format)
            tot_item = QTableWidgetItem(self._fmt_money(e.total_amount))
            tot_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
            self.eng_table.setItem(i, 7, tot_item)

        self.eng_table.setSortingEnabled(was_sorting)

        # Reselect if requested
        if keep_id is not None:
            self._reselect_engagement_row(keep_id)

    def on_clear_engagement_client_filter(self) -> None:
        self.engagement_client_filter = None
        self.refresh_engagements()

    def on_view_engagements_for_selected_client(self) -> None:
        if not self.selected_business_id:
            QMessageBox.information(self, "Business requise", "Sélectionne une business avant.")
            return
        if not self.selected_client_id:
            QMessageBox.information(self, "Client requis", "Sélectionne un client avant.")
            return

        self.engagement_client_filter = self.selected_client_id
        self.tabs.setCurrentIndex(self.tab_engagements_idx)
        self.refresh_engagements()

    def on_engagement_selection_btn_state(self) -> None:
        self.btn_eng_delete.setEnabled(self.eng_table.currentRow() >= 0)

    def on_engagement_selection_changed(self) -> None:
        row = self.eng_table.currentRow()
        self.items_table.setRowCount(0)
        self.btn_item_delete.setEnabled(False)

        if row < 0:
            self.selected_engagement_id = None
            self.lbl_items_title.setText("Items — Sélectionne un engagement")
            return

        item = self.eng_table.item(row, 0)
        if not item:
            self.selected_engagement_id = None
            self.lbl_items_title.setText("Items — Sélectionne un engagement")
            return

        self.selected_engagement_id = int(item.text())

        # update bottom title
        title = self.eng_table.item(row, 2).text() if self.eng_table.item(row, 2) else ""
        cid = self.eng_table.item(row, 1).text() if self.eng_table.item(row, 1) else ""
        tot = self.eng_table.item(row, 7).text() if self.eng_table.item(row, 7) else ""
        self.lbl_items_title.setText(
            f"Items — Engagement #{self.selected_engagement_id} | Client: {cid or '—'} | {title} | Total: {tot or '—'}"
        )

        self.refresh_items()

    def refresh_items(self) -> None:
        self.items_table.setRowCount(0)
        self.btn_item_delete.setEnabled(False)

        if not self.selected_engagement_id:
            return

        items = list_items(self.selected_engagement_id)

        was_sorting = self.items_table.isSortingEnabled()
        self.items_table.setSortingEnabled(False)

        self.items_table.setRowCount(len(items))
        for i, it in enumerate(items):
            self.items_table.setItem(i, 0, QTableWidgetItem(str(it.id_item)))
            self.items_table.setItem(i, 1, QTableWidgetItem(it.item_name or ""))
            self.items_table.setItem(i, 2, QTableWidgetItem(it.item_type or ""))
            self.items_table.setItem(i, 3, QTableWidgetItem(str(it.quantity)))

            up_item = QTableWidgetItem(self._fmt_money(it.unit_price))
            up_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
            self.items_table.setItem(i, 4, up_item)

            lt_item = QTableWidgetItem(self._fmt_money(it.line_total))
            lt_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
            self.items_table.setItem(i, 5, lt_item)

            self.items_table.setItem(i, 6, QTableWidgetItem(str(it.business_id)))

        self.items_table.setSortingEnabled(was_sorting)

    def on_engagement_add(self) -> None:
        if not self.selected_business_id:
            QMessageBox.information(self, "Business requise", "Sélectionne une business avant.")
            return

        initial = {}
        if self.engagement_client_filter is not None:
            initial["client_id"] = self.engagement_client_filter

        dlg = EngagementForm(self, initial=initial, allow_client=True)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        data = dlg.get_data()
        if not (data.get("title") or "").strip():
            QMessageBox.warning(self, "Erreur", "Le titre est requis.")
            return

        try:
            create_engagement(
                business_id=self.selected_business_id,
                title=data["title"],
                status=data.get("status") or "draft",
                description=data.get("description"),
                client_id=data.get("client_id"),
                start_date=data.get("start_date"),
                end_date=data.get("end_date"),
                total_amount=data.get("total_amount"),
            )
            self.set_status("✅ Engagement créé.")
            self.refresh_engagements()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def on_engagement_double_click(self, row: int, col: int) -> None:
        if not self.selected_business_id:
            return

        item_id = self.eng_table.item(row, 0)
        if not item_id:
            return
        id_eng = int(item_id.text())

        initial = {
            "client_id": None,
            "title": self.eng_table.item(row, 2).text() if self.eng_table.item(row, 2) else "",
            "status": self.eng_table.item(row, 3).text() if self.eng_table.item(row, 3) else "draft",
            "description": self.eng_table.item(row, 4).text() if self.eng_table.item(row, 4) else "",
            "start_date": self.eng_table.item(row, 5).text() if self.eng_table.item(row, 5) else "",
            "end_date": self.eng_table.item(row, 6).text() if self.eng_table.item(row, 6) else "",
            "total_amount": self.eng_table.item(row, 7).text() if self.eng_table.item(row, 7) else "",
        }

        cid_cell = self.eng_table.item(row, 1)
        if cid_cell and cid_cell.text().strip():
            try:
                initial["client_id"] = int(cid_cell.text())
            except ValueError:
                initial["client_id"] = None

        dlg = EngagementForm(self, initial=initial, allow_client=True)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        data = dlg.get_data()
        if not (data.get("title") or "").strip():
            QMessageBox.warning(self, "Erreur", "Le titre est requis.")
            return

        try:
            update_engagement(self.selected_business_id, id_eng, data)
            self.set_status("💾 Engagement mis à jour.")
            self.refresh_engagements(keep_selection=True)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def on_engagement_delete(self) -> None:
        if not self.selected_business_id:
            return

        row = self.eng_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Sélection", "Sélectionne un engagement.")
            return

        item_id = self.eng_table.item(row, 0)
        if not item_id:
            return
        id_eng = int(item_id.text())

        confirm = QMessageBox.question(
            self,
            "Confirmer suppression",
            f"Supprimer l’engagement ID {id_eng} ? (les items seront supprimés aussi)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            ok = delete_engagement(self.selected_business_id, id_eng)
            if not ok:
                QMessageBox.warning(self, "Refusé", "Suppression impossible (introuvable ou non autorisé).")
                return
            self.set_status("🗑️ Engagement supprimé.")
            self.refresh_engagements()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def on_item_selection_btn_state(self) -> None:
        self.btn_item_delete.setEnabled(self.items_table.currentRow() >= 0)

    def on_item_add(self) -> None:
        if not self.selected_business_id:
            QMessageBox.information(self, "Business requise", "Sélectionne une business avant.")
            return
        if not self.selected_engagement_id:
            QMessageBox.information(self, "Engagement requis", "Sélectionne un engagement.")
            return

        dlg = ItemForm(self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        data = dlg.get_data()
        if not (data.get("item_name") or "").strip():
            QMessageBox.warning(self, "Erreur", "Le nom est requis.")
            return

        try:
            create_item(
                engagement_id=self.selected_engagement_id,
                business_id=self.selected_business_id,
                item_name=data["item_name"],
                item_type=data.get("item_type") or "service",
                quantity=int(data.get("quantity") or 1),
                unit_price=Decimal(str(data.get("unit_price") or "0.00")),
            )
            self.set_status("✅ Item ajouté.")
            self._refresh_engagement_after_item_change()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def on_item_double_click(self, row: int, col: int) -> None:
        if not self.selected_engagement_id:
            return

        item_id = self.items_table.item(row, 0)
        if not item_id:
            return

        id_item = int(item_id.text())
        initial = {
            "item_name": self.items_table.item(row, 1).text() if self.items_table.item(row, 1) else "",
            "item_type": self.items_table.item(row, 2).text() if self.items_table.item(row, 2) else "service",
            "quantity": self.items_table.item(row, 3).text() if self.items_table.item(row, 3) else "1",
            "unit_price": self.items_table.item(row, 4).text() if self.items_table.item(row, 4) else "0.00",
        }

        dlg = ItemForm(self, initial=initial)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        data = dlg.get_data()
        if not (data.get("item_name") or "").strip():
            QMessageBox.warning(self, "Erreur", "Le nom est requis.")
            return

        try:
            ok = update_item(self.selected_engagement_id, id_item, data)
            if not ok:
                QMessageBox.warning(self, "Info", "Item introuvable.")
                return
            self.set_status("💾 Item mis à jour.")
            self._refresh_engagement_after_item_change()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))


    def on_item_delete(self) -> None:
        if not self.selected_engagement_id:
            return

        row = self.items_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Sélection", "Sélectionne un item.")
            return

        item_id = self.items_table.item(row, 0)
        if not item_id:
            return
        id_item = int(item_id.text())

        confirm = QMessageBox.question(
            self,
            "Confirmer suppression",
            f"Supprimer l’item ID {id_item} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            ok = delete_item(self.selected_engagement_id, id_item)
            if not ok:
                QMessageBox.warning(self, "Refusé", "Suppression impossible (introuvable).")
                return
            self.set_status("🗑️ Item supprimé.")
            self._refresh_engagement_after_item_change()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))


    # =========================
    # Helpers
    # =========================
    def set_status(self, msg: str) -> None:
        if hasattr(self, "biz_combo") and self.selected_business_id:
            biz = self.biz_combo.currentText()
            self.status_label.setText(f"{msg} — Business active: {biz}")
        else:
            self.status_label.setText(msg)

    def _fmt_money(self, v) -> str:
        if v is None:
            return ""
        try:
            x = float(v)
            return f"{x:,.2f}".replace(",", " ")
        except Exception:
            return str(v)

    def _status_color(self, status: str):
        s = (status or "").lower()
        if s == "active":
            return Qt.GlobalColor.cyan
        if s == "completed":
            return Qt.GlobalColor.green
        if s == "cancelled":
            return Qt.GlobalColor.red
        return Qt.GlobalColor.lightGray

    def _reselect_engagement_row(self, engagement_id: int) -> None:
        # Reselect l'engagement après refresh, pour éviter de perdre le focus
        for r in range(self.eng_table.rowCount()):
            it = self.eng_table.item(r, 0)
            if it and it.text().strip() and int(it.text()) == engagement_id:
                # éviter double refresh
                self.eng_table.blockSignals(True)
                self.eng_table.selectRow(r)
                self.eng_table.blockSignals(False)

                self.selected_engagement_id = engagement_id

                # Met à jour le titre items (comme si on avait cliqué)
                cid = self.eng_table.item(r, 1).text() if self.eng_table.item(r, 1) else ""
                title = self.eng_table.item(r, 2).text() if self.eng_table.item(r, 2) else ""
                tot = self.eng_table.item(r, 7).text() if self.eng_table.item(r, 7) else ""
                self.lbl_items_title.setText(
                    f"Items — Engagement #{engagement_id} | Client: {cid or '—'} | {title} | Total: {tot or '—'}"
                )

                self.eng_table.scrollToItem(it)
                return

    # =========================
    # ToolBar and Menus
    # =========================
    def build_toolbar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("topBar")
        bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row = QHBoxLayout(bar)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(12)

        brand = QHBoxLayout()
        brand.setSpacing(8)

        logo = QLabel()
        logo.setObjectName("topBarLogo")

        pm = QPixmap("assets/kairos_logo(3).png")
        if not pm.isNull():
            logo.setPixmap(
                pm.scaled(
                    34,
                    34,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        logo.setFixedSize(36, 36)
        brand.addWidget(logo)

        app_name = QLabel("Kairos")
        app_name.setObjectName("topBarTitle")
        brand.addWidget(app_name)

        row.addLayout(brand)
        row.addStretch(1)

        biz_label = QLabel("Business")
        biz_label.setObjectName("topBarLabel")
        row.addWidget(biz_label)

        self.biz_combo = QComboBox()
        self.biz_combo.setObjectName("bizCombo")
        self.biz_combo.setMinimumWidth(260)
        self.biz_combo.currentIndexChanged.connect(self.on_business_combo_changed)
        row.addWidget(self.biz_combo)

        row.addStretch(1)

        self.user_btn = QPushButton(self.full_name)
        self.user_btn.setObjectName("btnUserMenu")
        self.user_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        menu = QMenu(self)
        act_profile = QAction("Profil", self)
        act_logout = QAction("Déconnexion", self)

        act_profile.triggered.connect(self.on_profile)
        act_logout.triggered.connect(self.on_logout)

        menu.addAction(act_profile)
        menu.addSeparator()
        menu.addAction(act_logout)

        self.user_btn.setMenu(menu)
        row.addWidget(self.user_btn)

        return bar

    def load_businesses_into_combo(self, keep_selection: bool = False) -> None:
        businesses = list_businesses(self.user.id_user)

        previous = self.selected_business_id if keep_selection else None

        self.biz_combo.blockSignals(True)
        self.biz_combo.clear()

        for b in businesses:
            label = b.name or f"Business #{b.id_business}"
            self.biz_combo.addItem(label, b.id_business)

        self.biz_combo.blockSignals(False)

        if not businesses:
            self.selected_business_id = None
            self.tabs.setTabEnabled(self.tab_clients_idx, False)
            self.tabs.setTabEnabled(self.tab_engagements_idx, False)
            self.clients_table.setRowCount(0)
            self.eng_table.setRowCount(0)
            self.items_table.setRowCount(0)
            self.set_status("ℹ️ Aucune business. Créer une business pour gérer les clients.")
            self.update_window_title()
            return

        if previous and any(b.id_business == previous for b in businesses):
            self.selected_business_id = previous
            self.select_business_in_combo(previous)
        else:
            self.selected_business_id = businesses[0].id_business
            self.biz_combo.setCurrentIndex(0)

    def select_business_in_combo(self, business_id: int) -> None:
        for i in range(self.biz_combo.count()):
            if self.biz_combo.itemData(i) == business_id:
                self.biz_combo.blockSignals(True)
                self.biz_combo.setCurrentIndex(i)
                self.biz_combo.blockSignals(False)
                return

    def on_business_combo_changed(self, idx: int) -> None:
        if idx < 0:
            self.selected_business_id = None
            self.selected_client_id = None
            self.engagement_client_filter = None
            self.selected_engagement_id = None

            self.tabs.setTabEnabled(self.tab_clients_idx, False)
            self.tabs.setTabEnabled(self.tab_engagements_idx, False)

            self.clients_table.setRowCount(0)
            self.eng_table.setRowCount(0)
            self.items_table.setRowCount(0)

            self.update_window_title()
            self.set_status("ℹ️ Aucune business sélectionnée.")
            return

        biz_id = self.biz_combo.currentData()
        self.selected_business_id = int(biz_id) if biz_id is not None else None

        enabled = self.selected_business_id is not None
        self.tabs.setTabEnabled(self.tab_clients_idx, enabled)
        self.tabs.setTabEnabled(self.tab_engagements_idx, enabled)

        self.selected_client_id = None
        self.engagement_client_filter = None
        self.selected_engagement_id = None

        self.refresh_clients()
        self.refresh_engagements()
        self.update_window_title()
        self.set_status("✅ Business active changée. Données rafraîchies.")

    def on_profile(self) -> None:
        biz_label = ""
        biz_id = None

        if hasattr(self, "biz_combo") and self.biz_combo.currentIndex() >= 0:
            biz_label = (self.biz_combo.currentText() or "").strip()
            biz_id = self.biz_combo.currentData()

        role = (self.user.role or "").strip()
        status = "Actif" if bool(self.user.is_active) else "Inactif"

        lines = [
            f"Nom: {self.full_name}",
            f"Email: {self.user.email}",
            f"Rôle: {role}",
            f"Statut: {status}",
        ]

        if biz_id is not None:
            lines.append(f"Business active: {biz_label} (ID {biz_id})")
        else:
            lines.append("Business active: Aucune")

        QMessageBox.information(self, "Profil", "\n".join(lines))

    def on_logout(self) -> None:
        self.close()

    def update_window_title(self) -> None:
        if self.selected_business_id and hasattr(self, "biz_combo"):
            name = self.biz_combo.currentText()
            self.setWindowTitle(f"Owner Desktop — {name}")
        else:
            self.setWindowTitle("Owner Desktop — Dashboard")

    def _refresh_engagement_after_item_change(self) -> None:
        """
        Après CRUD item: le total_amount de l'engagement change en DB.
        On refresh la table engagements + on reselect le même engagement,
        puis on refresh items + label.
        """
        if not self.selected_engagement_id:
            return

        keep_id = self.selected_engagement_id
        self.refresh_engagements()
        self._reselect_engagement_row(keep_id)

        # Ça va déclencher on_engagement_selection_changed si selectionChanged,
        # mais si jamais ça ne trigger pas (selon Qt), on force:
        self.selected_engagement_id = keep_id
        self.refresh_items()
