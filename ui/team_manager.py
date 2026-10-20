from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                                 QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QAbstractItemView)
from PySide6.QtCore import Qt, Signal
from core import storage
from core.models import Team, new_id
from ui.widgets.team_detail_dialog import TeamDetailDialog


class TeamManagerPage(QWidget):
    teams_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.teams: list[Team] = []
        self._build()
        self.reload()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("Equipos")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Roster global de equipos disponibles para inscribir en torneos. "
                           "Haz click en un equipo para ver sus estadisticas y trofeos.")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        form_row = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nombre del equipo")
        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText("Tag (opcional, ej. NAVI)")
        self.tag_edit.setFixedWidth(140)
        add_btn = QPushButton("+ Añadir equipo")
        add_btn.setObjectName("primary")
        add_btn.clicked.connect(self._add_team)
        form_row.addWidget(self.name_edit)
        form_row.addWidget(self.tag_edit)
        form_row.addWidget(add_btn)
        layout.addLayout(form_row)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Equipo", "Tag", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.cellClicked.connect(self._on_cell_clicked)
        layout.addWidget(self.table)

    def reload(self):
        self.teams = storage.load_teams()
        self.table.setRowCount(0)
        for t in self.teams:
            row = self.table.rowCount()
            self.table.insertRow(row)
            name_item = QTableWidgetItem(t.name)
            name_item.setData(Qt.UserRole, t.id)
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(t.tag))
            del_btn = QPushButton("Eliminar")
            del_btn.setObjectName("danger")
            del_btn.clicked.connect(lambda checked=False, tid=t.id: self._delete_team(tid))
            self.table.setCellWidget(row, 2, del_btn)

    def _on_cell_clicked(self, row, col):
        if col == 2:
            return
        item = self.table.item(row, 0)
        if not item:
            return
        team_id = item.data(Qt.UserRole)
        team = next((t for t in self.teams if t.id == team_id), None)
        if not team:
            return
        tournaments = storage.load_all_tournaments()
        dlg = TeamDetailDialog(team, tournaments, self)
        dlg.exec()

    def _add_team(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Falta el nombre", "Escribe el nombre del equipo.")
            return
        team = Team(id=new_id(), name=name, tag=self.tag_edit.text().strip())
        self.teams.append(team)
        storage.save_teams(self.teams)
        self.name_edit.clear()
        self.tag_edit.clear()
        self.reload()
        self.teams_changed.emit()

    def _delete_team(self, team_id):
        confirm = QMessageBox.question(self, "Eliminar equipo",
                                        "¿Seguro que quieres eliminar este equipo del roster? "
                                        "No afectara a torneos ya jugados.")
        if confirm != QMessageBox.Yes:
            return
        self.teams = [t for t in self.teams if t.id != team_id]
        storage.save_teams(self.teams)
        self.reload()
        self.teams_changed.emit()
