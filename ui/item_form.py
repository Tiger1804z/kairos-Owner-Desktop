# ui/item_form.py
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QPushButton,
    QMessageBox,
)


class ItemForm(QDialog):
    """
    Champs (schema Prisma):
      - item_name (requis)
      - item_type (product/service/hourly/subscription)
      - quantity (int)
      - unit_price (Decimal)
    line_total est calculé côté repo.
    """

    def __init__(self, parent=None, initial: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Engagement Item")
        self.setModal(True)

        initial = initial or {}

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # name
        row_name = QHBoxLayout()
        row_name.addWidget(QLabel("Nom *"))
        self.ed_name = QLineEdit()
        self.ed_name.setText(initial.get("item_name") or "")
        row_name.addWidget(self.ed_name, 1)
        root.addLayout(row_name)

        # type
        row_type = QHBoxLayout()
        row_type.addWidget(QLabel("Type"))
        self.cb_type = QComboBox()
        self.cb_type.addItems(["product", "service", "hourly", "subscription"])
        t0 = (initial.get("item_type") or "service").strip()
        idx = self.cb_type.findText(t0)
        self.cb_type.setCurrentIndex(idx if idx >= 0 else 1)
        row_type.addWidget(self.cb_type, 1)
        root.addLayout(row_type)

        # quantity
        row_qty = QHBoxLayout()
        row_qty.addWidget(QLabel("Quantité"))
        self.spin_qty = QSpinBox()
        self.spin_qty.setRange(1, 1_000_000)
        self.spin_qty.setValue(int(initial.get("quantity") or 1))
        row_qty.addWidget(self.spin_qty, 1)
        root.addLayout(row_qty)

        # unit price
        row_price = QHBoxLayout()
        row_price.addWidget(QLabel("Prix unitaire"))
        self.ed_unit = QLineEdit()
        self.ed_unit.setPlaceholderText("ex: 49.99")
        if initial.get("unit_price") is not None:
            self.ed_unit.setText(str(initial.get("unit_price")))
        else:
            self.ed_unit.setText("0.00")
        row_price.addWidget(self.ed_unit, 1)
        root.addLayout(row_price)

        # buttons
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
        name = (self.ed_name.text() or "").strip()
        if not name:
            QMessageBox.warning(self, "Erreur", "Le nom est requis.")
            return

        unit_txt = (self.ed_unit.text() or "").strip()
        try:
            _ = Decimal(unit_txt)
        except (InvalidOperation, ValueError):
            QMessageBox.warning(self, "Erreur", "Le prix unitaire doit être un nombre (ex: 49.99).")
            return

        self.accept()

    def get_data(self) -> dict:
        unit_txt = (self.ed_unit.text() or "0").strip()
        unit = Decimal(unit_txt)

        return {
            "item_name": (self.ed_name.text() or "").strip(),
            "item_type": (self.cb_type.currentText() or "service").strip(),
            "quantity": int(self.spin_qty.value()),
            "unit_price": unit,
        }
