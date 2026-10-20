from PySide6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel, QSpinBox,
                                 QPushButton, QSizePolicy)
from PySide6.QtCore import Signal, Qt
from ui.style import ACCENT, GREEN, TEXT_DIM, BORDER


class MatchCard(QFrame):
    result_saved = Signal(str, int, int)  # match_id, score1, score2

    def __init__(self, match, team_name_fn, parent=None):
        super().__init__(parent)
        self.match = match
        self.team_name_fn = team_name_fn
        self.setObjectName("card")
        self.setStyleSheet(f"QFrame#card {{ border-radius: 8px; }}")
        self.setMinimumWidth(230)
        self._build()

    def _team_label(self, team_id, bo_won=False):
        name = self.team_name_fn(team_id) if team_id else "BYE"
        lbl = QLabel(name)
        lbl.setStyleSheet(f"font-size: 12.5px; font-weight: {'700' if bo_won else '500'}; "
                           f"color: {'#ffffff' if bo_won else TEXT_DIM};")
        return lbl

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        header = QLabel(f"Ronda {self.match.round}" + ("  ·  BYE" if self.match.bye else
                         (f"  ·  BO{self.match.bo}" if self.match.bo > 1 else "")))
        header.setStyleSheet(f"font-size: 10px; color: {TEXT_DIM}; font-weight: 600;")
        layout.addWidget(header)

        if self.match.bye:
            row = QHBoxLayout()
            row.addWidget(self._team_label(self.match.winner_id, True))
            lbl = QLabel("Pasa directo")
            lbl.setStyleSheet(f"color: {GREEN}; font-size: 11px;")
            row.addStretch()
            row.addWidget(lbl)
            layout.addLayout(row)
            return

        if self.match.team1_id is None or self.match.team2_id is None:
            lbl = QLabel("Pendiente de rivales")
            lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11.5px; font-style: italic;")
            layout.addWidget(lbl)
            return

        self.spin1 = QSpinBox(); self.spin1.setRange(0, 99); self.spin1.setValue(self.match.score1)
        self.spin2 = QSpinBox(); self.spin2.setRange(0, 99); self.spin2.setValue(self.match.score2)
        self.spin1.setFixedWidth(64); self.spin2.setFixedWidth(64)

        row1 = QHBoxLayout()
        row1.addWidget(self._team_label(self.match.team1_id, self.match.winner_id == self.match.team1_id))
        row1.addStretch()
        row1.addWidget(self.spin1)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(self._team_label(self.match.team2_id, self.match.winner_id == self.match.team2_id))
        row2.addStretch()
        row2.addWidget(self.spin2)
        layout.addLayout(row2)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton("Jugado ✓" if not self.match.played else "Actualizar")
        save_btn.setStyleSheet(f"padding: 3px 10px; font-size: 11px; "
                                f"{'border-color:' + ACCENT + ';color:' + ACCENT if self.match.played else ''}")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _save(self):
        self.result_saved.emit(self.match.id, self.spin1.value(), self.spin2.value())
