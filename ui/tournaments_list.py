from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
                                 QScrollArea, QGridLayout, QMessageBox, QDialog)
from PySide6.QtCore import Qt, Signal
from core import storage
from ui.tournament_wizard import TournamentWizard

STATUS_LABEL = {"setup": "En configuracion", "in_progress": "En curso", "finished": "Finalizado"}
STATUS_COLOR = {"setup": "#9aa1ad", "in_progress": "#3ba7ff", "finished": "#3fd17f"}


class TournamentCard(QFrame):
    clicked = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, tournament, parent=None):
        super().__init__(parent)
        self.tournament_id = tournament.id
        self.setObjectName("card")
        self.setFixedHeight(140)
        self.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)

        top_row = QHBoxLayout()
        name = QLabel(tournament.name)
        name.setStyleSheet("font-size: 15px; font-weight: 700;")
        top_row.addWidget(name)
        top_row.addStretch()
        status = QLabel(STATUS_LABEL.get(tournament.status, tournament.status))
        status.setStyleSheet(f"color: {STATUS_COLOR.get(tournament.status, '#fff')}; font-weight: 600; font-size: 11px;")
        top_row.addWidget(status)
        layout.addLayout(top_row)

        info = QLabel(f"{tournament.date}  ·  {tournament.importance_label} (x{tournament.importance})")
        info.setStyleSheet("color:#9aa1ad; font-size:11.5px;")
        layout.addWidget(info)

        stages_txt = " → ".join(s.name for s in tournament.stages)
        stages_lbl = QLabel(stages_txt)
        stages_lbl.setStyleSheet("color:#9aa1ad; font-size:11.5px;")
        layout.addWidget(stages_lbl)

        layout.addStretch()
        bottom = QHBoxLayout()
        teams_lbl = QLabel(f"{len(tournament.teams)} equipos")
        teams_lbl.setStyleSheet("font-size:11.5px;")
        bottom.addWidget(teams_lbl)
        bottom.addStretch()
        del_btn = QPushButton("Eliminar")
        del_btn.setObjectName("danger")
        del_btn.setFixedHeight(24)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.tournament_id))
        bottom.addWidget(del_btn)
        layout.addLayout(bottom)

    def mousePressEvent(self, event):
        self.clicked.emit(self.tournament_id)
        super().mousePressEvent(event)


class TournamentsListPage(QWidget):
    open_tournament = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.reload()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Torneos")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Crea y gestiona tus torneos de CS2.")
        subtitle.setObjectName("pageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        new_btn = QPushButton("+ Nuevo torneo")
        new_btn.setObjectName("primary")
        new_btn.clicked.connect(self._open_wizard)
        header.addWidget(new_btn)
        layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid = QGridLayout(self.grid_container)
        self.grid.setSpacing(14)
        self.scroll.setWidget(self.grid_container)
        layout.addWidget(self.scroll)

    def reload(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        tournaments = storage.load_all_tournaments()
        tournaments.sort(key=lambda t: t.date, reverse=True)

        if not tournaments:
            empty = QLabel("Aun no has creado ningun torneo. Pulsa '+ Nuevo torneo' para empezar.")
            empty.setStyleSheet("color:#9aa1ad; padding: 30px;")
            self.grid.addWidget(empty, 0, 0)
            return

        cols = 3
        for i, t in enumerate(tournaments):
            card = TournamentCard(t)
            card.clicked.connect(self.open_tournament.emit)
            card.delete_requested.connect(self._delete_tournament)
            self.grid.addWidget(card, i // cols, i % cols)

    def _open_wizard(self):
        all_teams = storage.load_teams()
        if not all_teams or len(all_teams) < 2:
            QMessageBox.information(self, "Faltan equipos",
                                     "Primero crea al menos 2 equipos en la pestaña 'Equipos'.")
            return
        wizard = TournamentWizard(all_teams, self)
        if wizard.exec() == QDialog.Accepted and wizard.result_tournament:
            storage.save_tournament(wizard.result_tournament)
            self.reload()
            self.open_tournament.emit(wizard.result_tournament.id)

    def _delete_tournament(self, tournament_id):
        confirm = QMessageBox.question(self, "Eliminar torneo",
                                        "¿Seguro que quieres eliminar este torneo? Esta accion no se puede deshacer.")
        if confirm != QMessageBox.Yes:
            return
        storage.delete_tournament(tournament_id)
        self.reload()
