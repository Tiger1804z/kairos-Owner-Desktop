from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem

from db.client_repo import list_clients, create_client, update_client, delete_client
from ui.client_form import ClientForm


class ClientsMixin:
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
            QMessageBox.information(self, "Info", "Sélectionner une business avant d'ajouter un client.")
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
