# ui/engagement_form.py
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QPushButton,
    QSpinBox,
    QDateEdit,
    QMessageBox,
)


class EngagementForm(QDialog):
    """
    Champs (schema Prisma):
      - client_id (optionnel)
      - title (requis)
      - description (optionnel)
      - status (draft/active/completed/cancelled)
      - start_date (optionnel)
      - end_date (optionnel)
      - total_amount (optionnel Decimal)
    """

    def __init__(self, parent=None, initial: dict | None = None, allow_client: bool = True):
        super().__init__(parent)
        self.setWindowTitle("Engagement")
        self.setModal(True)

        initial = initial or {}

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # Client ID
        row_client = QHBoxLayout()
        row_client.addWidget(QLabel("Client ID"))
        self.spin_client = QSpinBox()
        self.spin_client.setRange(0, 2_000_000_000)
        self.spin_client.setValue(int(initial.get("client_id") or 0))
        self.spin_client.setEnabled(bool(allow_client))
        self.spin_client.setToolTip("0 = aucun client lié")
        row_client.addWidget(self.spin_client, 1)
        root.addLayout(row_client)

        # Title
        row_title = QHBoxLayout()
        row_title.addWidget(QLabel("Titre *"))
        self.ed_title = QLineEdit()
        self.ed_title.setText(initial.get("title") or "")
        row_title.addWidget(self.ed_title, 1)
        root.addLayout(row_title)

        # Status
        row_status = QHBoxLayout()
        row_status.addWidget(QLabel("Status"))
        self.cb_status = QComboBox()
        self.cb_status.addItems(["draft", "active", "completed", "cancelled"])
        status_init = (initial.get("status") or "draft").strip()
        idx = self.cb_status.findText(status_init)
        self.cb_status.setCurrentIndex(idx if idx >= 0 else 0)
        row_status.addWidget(self.cb_status, 1)
        root.addLayout(row_status)

        # Description
        root.addWidget(QLabel("Description"))
        self.ed_desc = QTextEdit()
        self.ed_desc.setPlainText(initial.get("description") or "")
        self.ed_desc.setFixedHeight(90)
        root.addWidget(self.ed_desc)

        # Dates
        row_dates = QHBoxLayout()
        row_dates.addWidget(QLabel("Start date"))
        self.de_start = QDateEdit()
        self.de_start.setCalendarPopup(True)
        self.de_start.setDisplayFormat("yyyy-MM-dd")
        self.de_start.setSpecialValueText("—")
        self.de_start.setDate(QDate.currentDate())
        row_dates.addWidget(self.de_start, 1)

        row_dates.addWidget(QLabel("End date"))
        self.de_end = QDateEdit()
        self.de_end.setCalendarPopup(True)
        self.de_end.setDisplayFormat("yyyy-MM-dd")
        self.de_end.setSpecialValueText("—")
        self.de_end.setDate(QDate.currentDate())
        row_dates.addWidget(self.de_end, 1)

        root.addLayout(row_dates)

        # total amount
        row_total = QHBoxLayout()
        row_total.addWidget(QLabel("Total amount"))
        self.ed_total = QLineEdit()
        self.ed_total.setPlaceholderText("ex: 1250.00 (optionnel)")
        if initial.get("total_amount") is not None:
            self.ed_total.setText(str(initial.get("total_amount")))
        row_total.addWidget(self.ed_total, 1)
        root.addLayout(row_total)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch(1)
        self.btn_cancel = QPushButton("Annuler")
        self.btn_ok = QPushButton("Enregistrer")
        self.btn_ok.setDefault(True)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self._on_submit)

        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        root.addLayout(btns)

    def _on_submit(self) -> None:
        title = (self.ed_title.text() or "").strip()
        if not title:
            QMessageBox.warning(self, "Erreur", "Le titre est requis.")
            return
        self.accept()

    def get_data(self) -> dict:
        client_id = int(self.spin_client.value())
        client_id_val = None if client_id == 0 else client_id

        desc = (self.ed_desc.toPlainText() or "").strip()
        desc_val = desc if desc else None

        # Dates: on garde "optionnel" en permettant à l'user de laisser vide via une convention:
        # si champ laissé à la date du jour mais description vide? -> non.
        # Ici: simple: toujours une date si l'utilisateur ne change pas.
        start_dt = self.de_start.date().toPyDate()
        end_dt = self.de_end.date().toPyDate()
        start_val = datetime(start_dt.year, start_dt.month, start_dt.day)
        end_val = datetime(end_dt.year, end_dt.month, end_dt.day)

        total_txt = (self.ed_total.text() or "").strip()
        total_val = None
        if total_txt:
            try:
                total_val = Decimal(total_txt)
            except (InvalidOperation, ValueError):
                total_val = None  

        return {
            "client_id": client_id_val,
            "title": (self.ed_title.text() or "").strip(),
            "description": desc_val,
            "status": (self.cb_status.currentText() or "draft").strip(),
            "start_date": start_val,
            "end_date": end_val,
            "total_amount": total_val,
        }
