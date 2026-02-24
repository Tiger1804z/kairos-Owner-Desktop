from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidgetItem,
)
from PyQt6.QtGui import QAction, QPixmap

from db.business_repo import list_businesses


class SharedHelpersMixin:
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
    def build_toolbar(self) -> QFrame:
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
            self.tabs.setTabEnabled(self.tab_stats_idx, False)
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
            self.tabs.setTabEnabled(self.tab_stats_idx, False)
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
        self.tabs.setTabEnabled(self.tab_stats_idx, enabled)

        self.selected_client_id = None
        self.engagement_client_filter = None
        self.selected_engagement_id = None

        self.refresh_clients()
        self.refresh_engagements()
        self.refresh_stats()
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
