from __future__ import annotations

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem

from db.client_repo import list_clients
from db.transaction_repo import (
    list_transactions, create_transaction,
    update_transaction, delete_transaction, get_balance,
)
from ui.transaction_form import TransactionForm


class TransactionsMixin:
    #ONGLET TRANSACTIONS 

    def refresh_transactions(self) -> None:
        self.tx_table.setRowCount(0)
        self.btn_tx_delete.setEnabled(False)
        self.selected_transaction_id = None

        if not self.selected_business_id:
            self.lbl_balance.setText("Balance : —")
            self.lbl_balance.setStyleSheet("font-weight: bold; font-size: 13px;")
            return

        # Filtre : index 0 = Tous, 1 = Revenus, 2 = Dépenses
        filter_map = {0: None, 1: "income", 2: "expense"}
        type_filter = filter_map.get(self.cb_tx_filter.currentIndex())

        transactions = list_transactions(self.selected_business_id, type_filter)

        # Carte client_id → nom (pour afficher le nom dans la table)
        clients = list_clients(self.selected_business_id)
        client_names = {
            c.id_client: " ".join(filter(None, [c.first_name, c.last_name])) or c.company_name or f"#{c.id_client}"
            for c in clients
        }

        was_sorting = self.tx_table.isSortingEnabled()
        self.tx_table.setSortingEnabled(False)
        self.tx_table.setRowCount(len(transactions))

        for i, tx in enumerate(transactions):
            date_str = tx.transaction_date.strftime("%Y-%m-%d")
            client_str = client_names.get(tx.client_id, "—") if tx.client_id else "—"

            self.tx_table.setItem(i, 0, QTableWidgetItem(str(tx.id_transaction)))
            self.tx_table.setItem(i, 1, QTableWidgetItem(date_str))
            self.tx_table.setItem(i, 2, QTableWidgetItem(tx.transaction_type))
            self.tx_table.setItem(i, 3, QTableWidgetItem(self._fmt_money(tx.amount)))
            self.tx_table.setItem(i, 4, QTableWidgetItem(client_str))
            self.tx_table.setItem(i, 5, QTableWidgetItem(tx.category or ""))
            self.tx_table.setItem(i, 6, QTableWidgetItem(tx.description or ""))

            # Coloration : vert income, rouge expense
            color = QColor("#2d5a2d") if tx.transaction_type == "income" else QColor("#5a2d2d")
            for col in range(7):
                item = self.tx_table.item(i, col)
                if item:
                    item.setBackground(color)

        self.tx_table.setSortingEnabled(was_sorting)

        # Balance (toujours totale, peu importe le filtre)
        balance = get_balance(self.selected_business_id)
        color_hex = "#81c784" if balance >= 0 else "#e57373"
        self.lbl_balance.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {color_hex};")
        self.lbl_balance.setText(f"Balance : {self._fmt_money(balance)} $")

        self.set_status(f"💳 {len(transactions)} transaction(s) chargée(s).")

    def on_tx_selection_changed(self) -> None:
        row = self.tx_table.currentRow()
        self.btn_tx_delete.setEnabled(row >= 0)

        if row < 0:
            self.selected_transaction_id = None
            return

        item = self.tx_table.item(row, 0)
        if not item or not item.text().strip():
            self.selected_transaction_id = None
            return

        self.selected_transaction_id = int(item.text())

    def on_add_transaction(self) -> None:
        if not self.selected_business_id:
            QMessageBox.information(self, "Business requise", "Sélectionne une business avant.")
            return

        clients = list_clients(self.selected_business_id)
        dlg = TransactionForm(self, clients=clients)
        if dlg.exec():
            data = dlg.get_data()
            try:
                create_transaction(
                    business_id=self.selected_business_id,
                    transaction_type=data["transaction_type"],
                    amount=data["amount"],
                    transaction_date=data["transaction_date"],
                    client_id=data.get("client_id"),
                    engagement_id=data.get("engagement_id"),
                    payment_method=data.get("payment_method"),
                    category=data.get("category"),
                    reference_number=data.get("reference_number"),
                    description=data.get("description"),
                )
                self.refresh_transactions()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def on_delete_transaction(self) -> None:
        if not self.selected_transaction_id:
            QMessageBox.information(self, "Sélection", "Sélectionne une transaction.")
            return

        reply = QMessageBox.question(
            self, "Confirmation",
            f"Supprimer la transaction #{self.selected_transaction_id} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_transaction(self.selected_business_id, self.selected_transaction_id)
            self.refresh_transactions()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def on_tx_double_click(self, row: int, col: int) -> None:
        id_item = self.tx_table.item(row, 0)
        if not id_item:
            return

        id_tx = int(id_item.text())

        # Charger toutes les transactions pour retrouver celle cliquée
        transactions = list_transactions(self.selected_business_id)
        tx = next((t for t in transactions if t.id_transaction == id_tx), None)
        if not tx:
            return

        clients = list_clients(self.selected_business_id)
        initial = {
            "transaction_type": tx.transaction_type,
            "amount": tx.amount,
            "transaction_date": tx.transaction_date,
            "client_id": tx.client_id,
            "engagement_id": tx.engagement_id,
            "payment_method": tx.payment_method,
            "category": tx.category,
            "reference_number": tx.reference_number,
            "description": tx.description,
        }

        dlg = TransactionForm(self, initial=initial, clients=clients)
        if dlg.exec():
            data = dlg.get_data()
            try:
                update_transaction(self.selected_business_id, id_tx, data)
                self.refresh_transactions()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))
