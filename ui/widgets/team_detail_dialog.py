from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
                                 QScrollArea, QWidget, QSizePolicy)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from core import storage, team_stats

TROPHY_SIZE = 56


class _StatBox(QFrame):
    def __init__(self, label, value):
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        val = QLabel(str(value))
        val.setStyleSheet("font-size: 20px; font-weight: 800; color:#ff6a1a;")
        val.setAlignment(Qt.AlignCenter)
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 10.5px; color:#9aa1ad;")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        layout.addWidget(val)
        layout.addWidget(lbl)


class TeamDetailDialog(QDialog):
    def __init__(self, team, tournaments, parent=None):
        super().__init__(parent)
        self.setWindowTitle(team.name)
        self.resize(480, 560)
        stats = team_stats.compute_team_stats(team.id, tournaments)

        layout = QVBoxLayout(self)

        header = QVBoxLayout()
        name = QLabel(team.name)
        name.setStyleSheet("font-size: 20px; font-weight: 800;")
        header.addWidget(name)
        if team.tag:
            tag = QLabel(f"[{team.tag}]")
            tag.setStyleSheet("color:#9aa1ad; font-size: 12px;")
            header.addWidget(tag)
        layout.addLayout(header)

        # ---------- Trofeos ----------
        trophies_title = QLabel("🏆 Trofeos")
        trophies_title.setStyleSheet("font-weight:700; font-size:13px; margin-top:8px;")
        layout.addWidget(trophies_title)

        if stats["trophies"]:
            trophy_scroll = QScrollArea()
            trophy_scroll.setWidgetResizable(True)
            trophy_scroll.setFixedHeight(TROPHY_SIZE + 46)
            trophy_inner = QWidget()
            trophy_row = QHBoxLayout(trophy_inner)
            trophy_row.setContentsMargins(2, 2, 2, 2)
            for tr in stats["trophies"]:
                trophy_row.addWidget(self._build_trophy_item(tr))
            trophy_row.addStretch()
            trophy_scroll.setWidget(trophy_inner)
            layout.addWidget(trophy_scroll)
        else:
            empty = QLabel("Este equipo aun no ha ganado ningun torneo.")
            empty.setStyleSheet("color:#9aa1ad; font-size:11.5px; font-style: italic;")
            layout.addWidget(empty)

        # ---------- Estadisticas ----------
        stats_title = QLabel("📊 Estadisticas")
        stats_title.setStyleSheet("font-weight:700; font-size:13px; margin-top:14px;")
        layout.addWidget(stats_title)

        grid = QGridLayout()
        grid.setSpacing(8)
        cells = [
            ("Torneos jugados", stats["tournaments_played"]),
            ("Torneos ganados", stats["tournaments_won"]),
            ("Podios (top 3)", stats["podiums"]),
            ("Puntos totales", f'{stats["total_points"]:.1f}'),
            ("Partidos (V-D)", f'{stats["matches_won"]}-{stats["matches_lost"]}'),
            ("% victorias", f'{stats["win_rate"]}%'),
        ]
        for i, (label, value) in enumerate(cells):
            grid.addWidget(_StatBox(label, value), i // 3, i % 3)
        layout.addLayout(grid)

        # ---------- Historial ----------
        hist_title = QLabel("Historial de torneos")
        hist_title.setStyleSheet("font-weight:700; font-size:13px; margin-top:14px;")
        layout.addWidget(hist_title)

        hist_scroll = QScrollArea()
        hist_scroll.setWidgetResizable(True)
        hist_inner = QWidget()
        hist_layout = QVBoxLayout(hist_inner)
        if stats["history"]:
            for h in stats["history"]:
                row = QFrame()
                row.setObjectName("card")
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(10, 6, 10, 6)
                left = QLabel(f'{h["tournament_name"]}  ·  {h["date"]}')
                left.setStyleSheet("font-size:11.5px;")
                right = QLabel(f'Pos. {h["position_label"]}  ·  {h["points"]:.1f} pts')
                right.setStyleSheet("font-size:11.5px; color:#3fd17f; font-weight:600;")
                row_layout.addWidget(left)
                row_layout.addStretch()
                row_layout.addWidget(right)
                hist_layout.addWidget(row)
        else:
            lbl = QLabel("Sin torneos finalizados todavia.")
            lbl.setStyleSheet("color:#9aa1ad; font-size:11.5px; font-style: italic;")
            hist_layout.addWidget(lbl)
        hist_layout.addStretch()
        hist_scroll.setWidget(hist_inner)
        layout.addWidget(hist_scroll)

    def _build_trophy_item(self, trophy):
        box = QVBoxLayout()
        container = QWidget()
        container.setLayout(box)
        container.setFixedWidth(TROPHY_SIZE + 20)

        img_label = QLabel()
        img_label.setFixedSize(TROPHY_SIZE, TROPHY_SIZE)
        img_label.setAlignment(Qt.AlignCenter)
        path = storage.trophy_image_path(trophy["image_filename"]) if trophy["image_filename"] else None
        if path:
            pix = QPixmap(path)
            if not pix.isNull():
                pix = pix.scaled(TROPHY_SIZE, TROPHY_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(pix)
            else:
                img_label.setText("🏆")
                img_label.setStyleSheet("font-size: 28px;")
        else:
            img_label.setText("🏆")
            img_label.setStyleSheet("font-size: 28px;")
        img_label.setToolTip(f'{trophy["tournament_name"]} ({trophy["date"]})')

        name_lbl = QLabel(trophy["tournament_name"])
        name_lbl.setStyleSheet("font-size: 9px; color:#9aa1ad;")
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setWordWrap(True)
        name_lbl.setFixedWidth(TROPHY_SIZE + 16)

        box.addWidget(img_label, alignment=Qt.AlignCenter)
        box.addWidget(name_lbl)
        return container
