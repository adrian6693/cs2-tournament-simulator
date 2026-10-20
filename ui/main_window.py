from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, QStackedWidget
from PySide6.QtCore import Qt
from ui.tournaments_list import TournamentsListPage
from ui.team_manager import TeamManagerPage
from ui.ranking_view import RankingPage
from ui.tournament_view import TournamentView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CS2 Tournament Manager")
        self.resize(1180, 760)

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- Sidebar ---
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(0)

        title = QLabel("CS2 MANAGER")
        title.setObjectName("appTitle")
        subtitle = QLabel("Torneos & Clasificacion")
        subtitle.setObjectName("appSubtitle")
        side_layout.addWidget(title)
        side_layout.addWidget(subtitle)

        self.nav_buttons = {}
        for key, label in [("tournaments", "🏆  Torneos"), ("teams", "👥  Equipos"),
                            ("ranking", "📊  Clasificacion")]:
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setFixedHeight(42)
            btn.clicked.connect(lambda checked, k=key: self._switch_page(k))
            side_layout.addWidget(btn)
            self.nav_buttons[key] = btn
        side_layout.addStretch()
        root_layout.addWidget(sidebar)

        # --- Content stack ---
        self.stack = QStackedWidget()
        root_layout.addWidget(self.stack, 1)

        self.tournaments_page = TournamentsListPage()
        self.tournaments_page.open_tournament.connect(self._open_tournament)
        self.teams_page = TeamManagerPage()
        self.ranking_page = RankingPage()

        self.stack.addWidget(self.tournaments_page)   # index 0
        self.stack.addWidget(self.teams_page)          # index 1
        self.stack.addWidget(self.ranking_page)        # index 2
        self.tournament_view = None

        self._switch_page("tournaments")

    def _switch_page(self, key):
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)
        index = {"tournaments": 0, "teams": 1, "ranking": 2}[key]
        self.stack.setCurrentIndex(index)
        if key == "tournaments":
            self.tournaments_page.reload()
        elif key == "ranking":
            self.ranking_page.reload()

    def _open_tournament(self, tournament_id):
        if self.tournament_view is not None:
            self.stack.removeWidget(self.tournament_view)
            self.tournament_view.setParent(None)
            self.tournament_view.deleteLater()
        self.tournament_view = TournamentView(tournament_id, self._back_to_tournaments)
        self.stack.addWidget(self.tournament_view)
        self.stack.setCurrentWidget(self.tournament_view)
        for btn in self.nav_buttons.values():
            btn.setChecked(False)

    def _back_to_tournaments(self):
        self._switch_page("tournaments")
        # tras cerrar un torneo, la clasificacion global puede haber cambiado
        self.ranking_page.reload()
