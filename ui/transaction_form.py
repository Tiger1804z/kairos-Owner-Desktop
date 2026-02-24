from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QSpinBox,
    QDateEdit,
    QMessageBox,
)

from db.client_repo import ClientRow

class TransactionForm(QDialog):
    """Formulaire pour creer ou modifier une transaction"""
    
    def __init__(
        self,
        parent=None,
        initial: dict | None = None,
        clients: List[ClientRow] | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Transaction")
        self.setModal(True)
        self.setMinimumWidth(420)
        
        
        initial = initial or {}
        clients = clients or []
        
        # liste parallele: index dans le combo box -> id_client 
        self._client_ids: List[Optional[int]] = [None] + [c.id_client for c in clients]
        
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)
        
        # type
        row_type = QHBoxLayout()
        row_type.addWidget(QLabel("Type"))
        self.cb_type = QComboBox()
        self.cb_type.addItems(["income", "expense"])
        type_init = (initial.get("transaction_type") or  "income").strip()
        idx = self.cb_type.findText(type_init)
        self.cb_type.setCurrentIndex(idx if idx >= 0 else 0)
        row_type.addWidget(self.cb_type,1)
        root.addLayout(row_type)
        
        
        # Montant
        row_amount = QHBoxLayout()
        row_amount.addWidget(QLabel("Montant * ($)"))
        self.ed_amount = QLineEdit()
        self.ed_amount.setPlaceholderText(" ex: 123.45")
        if initial.get("amount") is not None:
            self.ed_amount.setText(str(initial["amount"]))
        row_amount.addWidget(self.ed_amount,1)
        root.addLayout(row_amount)
        
        # date 
        row_date = QHBoxLayout()
        row_date.addWidget(QLabel("Date *"))
        self.de_date = QDateEdit()
        self.de_date.setCalendarPopup(True)
        self.de_date.setDisplayFormat("yyyy-MM-dd")
        if initial.get("transaction_date") :
            dt = initial["transaction_date"]
            self.de_date.setDate(QDate(dt.year, dt.month, dt.day))
        else:
            self.de_date.setDate(QDate.currentDate())
        row_date.addWidget(self.de_date,1)
        root.addLayout(row_date)
        
        # client
        row_client = QHBoxLayout()
        row_client.addWidget(QLabel("Client"))
        self.cb_client = QComboBox()
        self.cb_client.addItem(" - aucun - ")
        for c in clients:
            parts = []
            if c.first_name:
                parts.append(c.first_name)
            if c.last_name:
                parts.append(c.last_name)
            if c.company_name and not parts:
                parts.append(c.company_name)
            name = " ".join(parts) if parts else f"client #{c.id_client}"
            self.cb_client.addItem(name)
            
        # preselection en mode edition
        init_client = initial.get("client_id")
        if init_client is not None:
            try:
                sel_idx = self._client_ids.index(int(init_client))
                self.cb_client.setCurrentIndex(sel_idx)
            except ValueError:
                self.cb_client.setCurrentIndex(0)
        row_client.addWidget(self.cb_client,1)
        root.addLayout(row_client)
        
        # methode de paiement
        
        row_pay = QHBoxLayout()
        row_pay.addWidget(QLabel("Methode de paiement"))
        self.cb_payment = QComboBox()
        self.cb_payment.addItem(" - aucun - ")
        self.cb_payment.addItems(["cash", "card", "transfer", "check", "other"])
        pay_init = (initial.get("payment_method") or "").strip()
        pay_idx = self.cb_payment.findText(pay_init)
        self.cb_payment.setCurrentIndex(pay_idx if pay_idx >= 0 else 0)
        row_pay.addWidget(self.cb_payment,1)
        root.addLayout(row_pay)
        
        # categorie
        row_cat = QHBoxLayout()
        row_cat.addWidget(QLabel("Categorie"))
        self.ed_category = QLineEdit()
        self.ed_category.setPlaceholderText(" ex: 'Food', 'Salary', ...")
        self.ed_category.setText(initial.get("category") or "")
        row_cat.addWidget(self.ed_category,1)
        root.addLayout(row_cat)
        
         # référence 
        row_ref = QHBoxLayout()
        row_ref.addWidget(QLabel("Référence"))
        self.ed_ref = QLineEdit()
        self.ed_ref.setPlaceholderText("ex: INV-2024-001")
        self.ed_ref.setText(initial.get("reference_number") or "")
        row_ref.addWidget(self.ed_ref, 1)
        root.addLayout(row_ref)

        # engagement ID 
        row_eng = QHBoxLayout()
        row_eng.addWidget(QLabel("Engagement ID"))
        self.spin_eng = QSpinBox()
        self.spin_eng.setRange(0, 2_000_000_000)
        self.spin_eng.setValue(int(initial.get("engagement_id") or 0))
        self.spin_eng.setToolTip("0 = aucun engagement lié")
        row_eng.addWidget(self.spin_eng, 1)
        root.addLayout(row_eng)

        # description 
        row_desc = QHBoxLayout()
        row_desc.addWidget(QLabel("Description"))
        self.ed_desc = QLineEdit()
        self.ed_desc.setPlaceholderText("Notes libres…")
        self.ed_desc.setText(initial.get("description") or "")
        row_desc.addWidget(self.ed_desc, 1)
        root.addLayout(row_desc)

        # boutons 
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
        
    def _on_submit(self):
        amount_txt = (self.ed_amount.text() or "").strip()
        if not amount_txt:
            QMessageBox.warning(self, "Erreur", "Le montant est obligatoire")
            return
        try:
            amount = Decimal(amount_txt)
        except InvalidOperation:
            QMessageBox.warning(self, "Erreur", "Le montant doit être au format décimal (ex: 123.45).")
            return
        if amount <= 0:
            QMessageBox.warning(self, "Erreur", "Le montant doit être supérieur à zéro.")
            return
        self.accept()
        
    def get_data(self) -> dict:
        amount = Decimal(self.ed_amount.text().strip())
        
        # tpPyDate() convertit en objet date de python
        qd = self.de_date.date().toPyDate()
        transaction_date = datetime(qd.year, qd.month, qd.day)
        
        client_id = self._client_ids[self.cb_client.currentIndex()]
        pay_txt = self.cb_payment.currentText()
        payment_method = None if self.cb_payment.currentIndex() == 0 else pay_txt
        
        eng_val = self.spin_eng.value()
        engagement_id = None if eng_val == 0 else eng_val
        
        category = (self.ed_category.text() or "").strip() or None
        reference_number = (self.ed_ref.text() or "").strip() or None
        description = (self.ed_desc.text() or "").strip() or None
        
        return {
            "transaction_type": self.cb_type.currentText(),
            "amount": amount,
            "transaction_date": transaction_date,
            "client_id": client_id,
            "payment_method": payment_method,
            "category": category,
            "reference_number": reference_number,
            "engagement_id": engagement_id,
            "description": description,
        }
        
        
        
        
                
