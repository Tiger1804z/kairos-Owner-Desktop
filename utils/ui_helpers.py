from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox


def show_error(parent, title: str, message: str) -> None:
    """Affiche une boîte de dialogue d'erreur"""
    QMessageBox.critical(parent, title, message)

def show_success(parent, title: str, message: str) -> None:
    """Affiche une boîte de dialogue de succès"""
    QMessageBox.information(parent, title, message)
    
    



def show_confirm(parent, title: str, message: str) -> bool:
    reply = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
                                 
    )
    return reply == QMessageBox.StandardButton.Yes




class WaitCursor:
    """Context manager pour afficher un curseur  en sablier pendant une opération
         usage:
         with WaitCursor():
              rows= list_transactions(business_id) # un apelle qui peut prendre du temps
    
    """
    
    """ s'execute au debut du bloc with et active le sablier"""
    def __enter__(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents()  # force l'affichage du curseur sinon il n'apparait pas sur les opérations rapides

    """ s'execute à la fin du bloc with et rétablit le curseur normal"""
    def __exit__(self, exc_type, exc_val, exc_tb):
        QApplication.restoreOverrideCursor()
        return False # dit a python de ne pas  supprimer l'exception si une exception a été levée dans le bloc with pour la gerer normalement 