from __future__ import annotations

import calendar

import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMessageBox,
)

from db.transaction_repo import get_stats

class StatsMixin:
    # ─── ONGLET STATS ────────────────────────────────────────────────

    def build_stats_tab(self) -> QWidget:
        """Construit le widget de l'onglet stats (appelé une fois à l'initialisation)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # barre du haut avec le bouton refresh
        top = QHBoxLayout()
        
        self.btn_stats_refresh = QPushButton(" 🔄️ Rafraîchir")
        self.btn_stats_refresh.setObjectName("btnNeutral")
        self.btn_stats_refresh.clicked.connect(self.refresh_stats)
        
        self.lbl_stats_income = QLabel("Revenus: -")
        self.lbl_stats_expense = QLabel("Dépenses: -")
        self.lbl_stats_balance = QLabel("Balance: -")
        self.lbl_stats_balance.setStyleSheet("font-weight: bold;")
        
        top.addWidget(self.btn_stats_refresh)
        top.addStretch(1)
        top.addWidget(self.lbl_stats_income)
        top.addWidget(self.lbl_stats_expense)
        top.addWidget(self.lbl_stats_balance)
        layout.addLayout(top)
        
        # matlplotlib 2 graphiques empilés
        fig = Figure(figsize=(8, 6), tight_layout=True)
        fig.patch.set_facecolor("#1e1e1e") 
        self._stats_ax_bar = fig.add_subplot(211) # graphique barres mensuel
        self._stats_ax_pie = fig.add_subplot(212) # graphique camembert catégories
        for ax in [self._stats_ax_bar, self._stats_ax_pie]:
            ax.set_facecolor("#2b2b2b")
        
        self._stats_canvas = FigureCanvasQTAgg(fig)
        layout.addWidget(self._stats_canvas, 1)
        
        return tab
    
    def refresh_stats(self) -> None:
        if not self.selected_business_id:
            self._stats_ax_bar.clear()
            self._stats_ax_pie.clear()
            self._stats_canvas.draw()
            self.lbl_stats_income.setText("Revenus: -")
            self.lbl_stats_expense.setText("Dépenses: -")
            self.lbl_stats_balance.setText("Balance: -")
            self.lbl_stats_balance.setStyleSheet("font-weight: bold;")
            return
        
        try:
            stats = get_stats(self.selected_business_id)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
            return

        # mise à jour des labels de revenus, dépenses, balance
        self.lbl_stats_income.setText(f"Revenus: {self._fmt_money(stats.total_income)} $")
        self.lbl_stats_expense.setText(f"Dépenses: {self._fmt_money(stats.total_expense)} $")
        bal_color = "#81c784" if stats.balance >= 0 else "#e57373"
        self.lbl_stats_balance.setText(f"Balance: {self._fmt_money(stats.balance)} $")
        self.lbl_stats_balance.setStyleSheet(f"font-weight: bold; color: {bal_color};")
        
        # graphique barres revenus/dépenses mensuel
        
        ax = self._stats_ax_bar
        ax.clear()
        ax.set_facecolor("#2b2b2b")
        if stats.monthly:
            month_labels = [f"{calendar.month_abbr[m[1]]}\n{m[0]}" for m in stats.monthly]
            incomes = [float(m[2]) for m in stats.monthly]
            expenses = [float(m[3]) for m in stats.monthly]
            
            xs = list(range(len(month_labels)))
            w = 0.35
            ax.bar([x - w / 2 for x in xs], incomes,  w, label="Revenus",  color="#4caf50")
            ax.bar([x + w / 2 for x in xs], expenses, w, label="Dépenses", color="#f44336")
            ax.set_xticks(xs)
            ax.set_xticklabels(month_labels, fontsize=7, color="#cccccc")
            ax.tick_params(colors="#cccccc")
            ax.legend(fontsize=8, labelcolor="#cccccc", loc="upper left",
                facecolor="#2b2b2b", edgecolor="#555", framealpha=0.8)
            for spine in ax.spines.values():
                spine.set_edgecolor("#555")
        else:
            ax.text(0.5, 0.5, "Aucune transaction (12 derniers mois)",
                    ha="center", va="center", transform=ax.transAxes, color="#888")

        ax.set_title("Revenus vs Dépenses - 12 derniers mois", fontsize=9, color="#cccccc")

        # graphique camembert catégories
        ax2 = self._stats_ax_pie
        ax2.clear()
        ax2.set_facecolor("#2b2b2b")

        expense_cats = [
            (cat, float(total))
            for cat, typ, total in stats.by_category
            if typ == "expense"
        ]

        if expense_cats:
            cat_labels = [c[0] for c in expense_cats]
            cat_values = [c[1] for c in expense_cats]

            # Regrouper les petites tranches (< 3%) dans "Autres" sinon le camembert devient illisible
            total = sum(cat_values)
            main_labels, main_values, autres = [], [], 0.0
            for lbl, val in zip(cat_labels, cat_values):
                if val / total >= 0.03:
                    main_labels.append(lbl)
                    main_values.append(val)
                else:
                    autres += val
            if autres > 0:
                main_labels.append("Autres")
                main_values.append(autres)

            _, _, autotexts = ax2.pie(
                main_values, labels=main_labels, autopct="%1.1f%%",
                startangle=90, textprops={"fontsize": 7, "color": "#cccccc"},
                labeldistance=1.15,
            )
            for at in autotexts:
                at.set_color("#ffffff")
        else:
            ax2.text(0.5, 0.5, "Aucune dépense catégorisée",
                     ha="center", va="center", transform=ax2.transAxes, color="#888")


        ax2.set_title("Dépenses par catégorie", fontsize=9, color="#cccccc")

        self._stats_canvas.draw()
        self.set_status("📊 Statistiques chargées.")
