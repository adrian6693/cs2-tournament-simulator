from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
                                 QHeaderView, QPushButton, QHBoxLayout, QAbstractItemView)
from PySide6.QtCore import Qt
from core import storage, ranking
from ui.widgets.team_detail_dialog import TeamDetailDialog


class RankingPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.reload()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)

        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Clasificacion general")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Puntos acumulados por cada equipo en todos los torneos finalizados. "
                           "Haz click en un equipo para ver sus estadisticas y trofeos.")
        subtitle.setObjectName("pageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.reload)
        header_row.addWidget(refresh_btn)
        layout.addLayout(header_row)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["#", "Equipo", "Tag", "Torneos jugados", "Puntos"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.cellClicked.connect(self._on_cell_clicked)
        layout.addWidget(self.table)

    def reload(self):
        self.tournaments = storage.load_all_tournaments()
        self.teams = storage.load_teams()
        data = ranking.compute_global_ranking(self.tournaments, self.teams)

        self.table.setRowCount(0)
        for r in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            rank_item = QTableWidgetItem(str(r["rank"]))
            rank_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, rank_item)
            name_item = QTableWidgetItem(r["name"])
            name_item.setData(Qt.UserRole, r["team_id"])
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, QTableWidgetItem(r.get("tag", "")))
            count_item = QTableWidgetItem(str(r["tournaments"]))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, count_item)
            pts_item = QTableWidgetItem(f"{r['points']:.1f}")
            pts_item.setTextAlignment(Qt.AlignCenter)
            font = pts_item.font()
            font.setBold(True)
            pts_item.setFont(font)
            self.table.setItem(row, 4, pts_item)

        if not data:
            self.table.setRowCount(1)
            empty = QTableWidgetItem("Aun no hay torneos finalizados.")
            self.table.setItem(0, 1, empty)

    def _on_cell_clicked(self, row, col):
        item = self.table.item(row, 1)
        if not item:
            return
        team_id = item.data(Qt.UserRole)
        if not team_id:
            return
        team = next((t for t in self.teams if t.id == team_id), None)
        if not team:
            return
        dlg = TeamDetailDialog(team, self.tournaments, self)
        dlg.exec()
