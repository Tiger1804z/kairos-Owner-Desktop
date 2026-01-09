# ui/client_form.py
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QLabel,
)


class ClientForm(QDialog):
    def __init__(self, parent=None, initial=None):
        super().__init__(parent)
        self.setWindowTitle("Client")
        self.initial = initial or {}

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Prénom"))
        self.first_name = QLineEdit(self.initial.get("first_name", "") or "")
        layout.addWidget(self.first_name)

        layout.addWidget(QLabel("Nom"))
        self.last_name = QLineEdit(self.initial.get("last_name", "") or "")
        layout.addWidget(self.last_name)

        layout.addWidget(QLabel("Entreprise"))
        self.company_name = QLineEdit(self.initial.get("company_name", "") or "")
        layout.addWidget(self.company_name)

        layout.addWidget(QLabel("Email"))
        self.email = QLineEdit(self.initial.get("email", "") or "")
        layout.addWidget(self.email)

        layout.addWidget(QLabel("Téléphone"))
        self.phone = QLineEdit(self.initial.get("phone", "") or "")
        layout.addWidget(self.phone)

        self.is_active = QCheckBox("Actif")
        self.is_active.setChecked(bool(self.initial.get("is_active", True)))
        layout.addWidget(self.is_active)

        self.btn_save = QPushButton("Sauvegarder")
        self.btn_save.setObjectName("btnPrimary")
        self.btn_save.clicked.connect(self.accept)
        layout.addWidget(self.btn_save)

        self.setLayout(layout)

    def get_data(self) -> dict:
        return {
            "first_name": self.first_name.text().strip() or None,
            "last_name": self.last_name.text().strip() or None,
            "company_name": self.company_name.text().strip() or None,
            "email": self.email.text().strip() or None,
            "phone": self.phone.text().strip() or None,
            "is_active": self.is_active.isChecked(),
        }
