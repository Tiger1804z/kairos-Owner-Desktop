from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem, QFileDialog

from db.business_repo import list_businesses, create_business, update_business, delete_business
from ui.business_form import BusinessForm
from utils.export_utils import export_transactions_csv, export_clients_engagements_csv



class BusinessesMixin:
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
        selected = self.biz_table.currentRow() >= 0
        self.btn_delete.setEnabled(selected)
        self.btn_export_tx.setEnabled(selected)
        self.btn_export_clients_eng.setEnabled(selected)

    def on_business_selected_for_clients(self) -> None:
        row = self.biz_table.currentRow()

        if row < 0:
            self.selected_business_id = None
            self.selected_client_id = None
            self.engagement_client_filter = None
            self.selected_engagement_id = None
            self.selected_transaction_id = None

            self.tabs.setTabEnabled(self.tab_clients_idx, False)
            self.tabs.setTabEnabled(self.tab_engagements_idx, False)
            self.tabs.setTabEnabled(self.tab_transactions_idx, False)
            self.tabs.setTabEnabled(self.tab_stats_idx, False)  
            self.tx_table.setRowCount(0)
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
        self.selected_transaction_id = None
        self.tabs.setTabEnabled(self.tab_clients_idx, True)
        self.tabs.setTabEnabled(self.tab_engagements_idx, True)
        self.tabs.setTabEnabled(self.tab_transactions_idx, True)
        self.tabs.setTabEnabled(self.tab_stats_idx, True)
        self.refresh_transactions()
        self.refresh_stats()

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
    
    # verifie que une business est selectionnée ensuite recupere le nom de la business depuis le comboBox,
    #  ouvre une boite dialog pour choisir un dossier si user annule -> return, sinon appelle la fonction d'export et
    # fait la query sql pour recuperer les transactions de la business et les exporte dans un fichier csv         
    def on_export_transactions(self) -> None:
        if not self.selected_business_id:
            return
        biz_name = self.biz_combo.currentText() or "business"
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier d'export")
        if not folder:
            return
        try:
            path = export_transactions_csv(self.selected_business_id, biz_name, folder)
            QMessageBox.information(self, "Export réussi", f"Fichier créé :\n{path}")
            self.set_status(f"📤 Export transactions : {path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
            
    # même logique que pour les transactions mais pour les clients et engagements d'une business donnée
    def on_export_clients_engagements(self) -> None:
        if not self.selected_business_id:
            return
        biz_name = self.biz_combo.currentText() or "business"
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier d'export")
        if not folder:
            return
        try:
            path = export_clients_engagements_csv(self.selected_business_id, biz_name, folder)
            QMessageBox.information(self, "Export réussi", f"Fichier créé :\n{path}")
            self.set_status(f"📤 Export clients/engagements : {path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))


