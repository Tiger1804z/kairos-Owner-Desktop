from __future__ import annotations

from decimal import Decimal

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem

from db.engagement_repo import list_engagements, create_engagement, update_engagement, delete_engagement
from db.engagement_item_repo import list_items, create_item, update_item, delete_item
from ui.engagement_form import EngagementForm
from ui.item_form import ItemForm


class EngagementsMixin:
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
            f"Supprimer l'engagement ID {id_eng} ? (les items seront supprimés aussi)",
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
            f"Supprimer l'item ID {id_item} ?",
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
