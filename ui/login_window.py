
from __future__ import annotations

from PyQt6.QtCore import Qt, QPropertyAnimation
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QGraphicsOpacityEffect,
    
)

from db.auth_repo import authenticate , AuthError, AuthUser
from PyQt6.QtGui import QPixmap, QIcon

class LoginWindow(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success

        # =========================
        # Window config
        # =========================
        self.setWindowTitle("Owner Desktop - Login")
        self.setMinimumWidth(420)
        
        icon = QIcon("assets/kairos_logo(3).png")
        if not icon.isNull():
            self.setWindowIcon(icon)

        # =========================
        # Main layout
        # =========================
        layout = QVBoxLayout()
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        # =========================
        # Logo
        # =========================
        logo_label = QLabel()
        pixmap = QPixmap("assets/kairos_logo(3).png")

        logo_label.setPixmap(
            pixmap.scaled(
                96,
                96,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setContentsMargins(0, 6, 0, 6)

        layout.addWidget(logo_label)
        layout.addSpacing(8)

        # =========================
        # Title
        # =========================
        title = QLabel("Owner Desktop")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(title)

        subtitle = QLabel("Veuillez vous connecter pour continuer")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        layout.addSpacing(12)

        # =========================
        # Inputs
        # =========================
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        layout.addSpacing(10)

        # =========================
        # Login button
        # =========================
        self.login_button = QPushButton("Se connecter")
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)

        # =========================
        # Finalize layout
        # =========================
        self.setLayout(layout)

        # UX : Enter triggers login
        self.email_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)
        
    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Champs requis", "Veuillez entrer votre email et mot de passe.")
            return
        
        self.login_button.setEnabled(False)
        try:
            user = authenticate(email, password)
            QMessageBox.information(self, "Succès", f"Bienvenue, {user.email} ! 👋")
            self.on_login_success(user)
            self.fade_and_close()
        except AuthError as e:
            msg = str(e)
            if msg =="USER_INACTIVE":
                 QMessageBox.warning(self, "Compte inactif", "Ce compte est désactivé.")
            else:
                QMessageBox.warning(self, "Erreur", "Identifiants invalides.")
        except Exception as e:
             QMessageBox.critical(self, "Erreur serveur", str(e))
        finally:
            self.login_button.setEnabled(True)
    
    def fade_and_close(self):
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(220)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.finished.connect(self.close)

        self._fade_anim = anim  # garder une référence
        anim.start()