from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem
from PySide6.QtGui import QPen, QBrush, QColor, QFont
from PySide6.QtCore import Qt, Signal

BOX_W, BOX_H = 190, 58
ROW_GAP = 16
COL_GAP = 90


class _MatchBoxItem(QGraphicsRectItem):
    def __init__(self, match, x, y, team_name_fn, view):
        super().__init__(0, 0, BOX_W, BOX_H)
        self.match = match
        self.view = view
        self.setPos(x, y)
        self.setBrush(QBrush(QColor("#22262f")))
        self.setPen(QPen(QColor("#2d323c"), 1))
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        self._labels = []  # mantiene vivas las referencias Python (si no, PySide las destruye)

        name1 = team_name_fn(match.team1_id) if match.team1_id else ("BYE" if match.bye else "Por definir")
        name2 = team_name_fn(match.team2_id) if match.team2_id else ("BYE" if match.bye else "Por definir")
        win1 = match.winner_id == match.team1_id and match.team1_id is not None
        win2 = match.winner_id == match.team2_id and match.team2_id is not None

        self._add_row(name1, str(match.score1) if match.played else "-", 6, win1)
        self._add_row(name2, str(match.score2) if match.played else "-", BOX_H / 2 + 2, win2)

    def _add_row(self, name, score, y, is_winner):
        color = "#ffffff" if is_winner else "#9aa1ad"
        t = QGraphicsTextItem(self)
        self._labels.append(t)
        t.setDefaultTextColor(QColor(color))
        f = QFont("Segoe UI", 9)
        f.setBold(is_winner)
        t.setFont(f)
        max_chars = 20
        display = name if len(name) <= max_chars else name[:max_chars - 1] + "…"
        t.setPlainText(display)
        t.setPos(8, y)

        s = QGraphicsTextItem(self)
        self._labels.append(s)
        s.setDefaultTextColor(QColor(color))
        s.setFont(f)
        s.setPlainText(score)
        s.setPos(BOX_W - 26, y)

    def mousePressEvent(self, event):
        self.view.match_clicked.emit(self.match.id)
        super().mousePressEvent(event)


class BracketView(QGraphicsView):
    match_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setBackgroundBrush(QBrush(QColor("#15171c")))
        self.setFrameShape(QGraphicsView.NoFrame)

    def set_data(self, stage, team_name_fn):
        self._scene.clear()
        self._boxes = []
        matches_by_round = {}
        for m in stage.matches:
            matches_by_round.setdefault(m.round, []).append(m)
        rounds = sorted(matches_by_round.keys())
        if not rounds:
            return

        first_round_count = len(matches_by_round[rounds[0]])
        import math
        total_bracket_rounds = int(math.log2(first_round_count)) + 1 if first_round_count > 0 else 1

        for col_idx, rnd in enumerate(rounds):
            matches = sorted(matches_by_round[rnd], key=lambda m: m.slot)
            spacing = (BOX_H + ROW_GAP) * (2 ** col_idx)
            start_offset = (spacing / 2) - (BOX_H / 2)
            x = col_idx * (BOX_W + COL_GAP)
            for i, m in enumerate(matches):
                y = start_offset + i * spacing
                box = _MatchBoxItem(m, x, y, team_name_fn, self)
                self._scene.addItem(box)
                self._boxes.append(box)

            round_label = QGraphicsTextItem(self._round_name(rnd, total_bracket_rounds))
            round_label.setDefaultTextColor(QColor("#9aa1ad"))
            f = QFont("Segoe UI", 9)
            f.setBold(True)
            round_label.setFont(f)
            round_label.setPos(x, -28)
            self._scene.addItem(round_label)

        total_height = (BOX_H + ROW_GAP) * first_round_count
        total_width = len(rounds) * (BOX_W + COL_GAP)
        self._scene.setSceneRect(-20, -50, total_width + 40, total_height + 40)

    def _round_name(self, rnd, total_rounds):
        remaining = total_rounds - rnd
        if remaining == 0:
            return "FINAL"
        if remaining == 1:
            return "Semifinales"
        if remaining == 2:
            return "Cuartos de final"
        return f"Ronda {rnd}"
