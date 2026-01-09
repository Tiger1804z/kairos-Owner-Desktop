# main.py
from __future__ import annotations

from pathlib import Path
import sys

from PyQt6.QtWidgets import QApplication

from ui.login_window import LoginWindow
from ui.dashboard_window import DashboardWindow


def main() -> int:
    app = QApplication(sys.argv)

    # Global stylesheet (QSS)
    qss_path = Path(__file__).parent / "ui" / "style.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    windows: dict[str, object] = {}

    def on_login_success(user) -> None:
        # 1) Ouvrir le tableau de bord FIRST (éviter le flash)
        dashboard = DashboardWindow(user)
        windows["dashboard"] = dashboard
        dashboard.show()

        # 2) ensuite fermer login
        login = windows.get("login")
        if login is not None:
            
            if hasattr(login, "fade_and_close"):
                login.fade_and_close()
            else:
                login.close()

            windows.pop("login", None)

    login = LoginWindow(on_login_success)
    windows["login"] = login
    login.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
