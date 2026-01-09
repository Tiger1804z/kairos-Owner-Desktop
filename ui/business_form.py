"""
KAIROS Owner Desktop - Formulaire de gestion des entreprises
"""

# ui/business_form.py
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QLabel,
    QComboBox,
)


class BusinessForm(QDialog):
    def __init__(self, parent=None, initial=None):
        super().__init__(parent)
        self.setWindowTitle("Modifier Business")
        self.initial = initial or {}

        layout = QVBoxLayout()

        # Nom
        layout.addWidget(QLabel("Nom"))
        self.name = QLineEdit(self.initial.get("name", "") or "")
        self.name.setPlaceholderText("Nom")
        layout.addWidget(self.name)

        # Type
        layout.addWidget(QLabel("Type"))
        self.business_type = QLineEdit(self.initial.get("business_type", "") or "")
        self.business_type.setPlaceholderText("ex: salon, restaurant, etc.")
        layout.addWidget(self.business_type)

        # Ville
        layout.addWidget(QLabel("Ville"))
        self.city = QLineEdit(self.initial.get("city", "") or "")
        self.city.setPlaceholderText("Ville")
        layout.addWidget(self.city)

        # Pays
        layout.addWidget(QLabel("Pays"))
        self.country = QLineEdit(self.initial.get("country", "") or "")
        self.country.setPlaceholderText("Pays")
        layout.addWidget(self.country)

        # Devise (combo simple)
        layout.addWidget(QLabel("Devise"))
        self.currency = QComboBox()
        self.currency.addItems(["CAD", "USD", "EUR"])
        current_currency = (self.initial.get("currency") or "CAD").upper()
        idx = self.currency.findText(current_currency)
        if idx >= 0:
            self.currency.setCurrentIndex(idx)
        layout.addWidget(self.currency)

        # Timezone (texte pour rester simple)
        layout.addWidget(QLabel("Timezone"))
        self.timezone = QLineEdit(self.initial.get("timezone", "") or "America/Montreal")
        self.timezone.setPlaceholderText("ex: America/Montreal")
        layout.addWidget(self.timezone)

        # Actif
        self.is_active = QCheckBox("Actif")
        self.is_active.setChecked(bool(self.initial.get("is_active", True)))
        layout.addWidget(self.is_active)

        # Save
        self.btn_save = QPushButton("Sauvegarder")
        self.btn_save.clicked.connect(self.accept)
        self.btn_save.setObjectName("btnPrimary")

        layout.addWidget(self.btn_save)

        self.setLayout(layout)

    def get_data(self) -> dict:
        return {
            "name": self.name.text().strip(),
            "business_type": self.business_type.text().strip() or None,
            "city": self.city.text().strip() or None,
            "country": self.country.text().strip() or None,
            "currency": self.currency.currentText().strip(),
            "timezone": self.timezone.text().strip() or "America/Montreal",
            "is_active": self.is_active.isChecked(),
        }
