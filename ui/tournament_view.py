from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
                                 QScrollArea, QGridLayout, QDialog, QSpinBox, QFormLayout,
                                 QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QFrame)
from PySide6.QtCore import Qt
from core import storage, tournament_logic as tl, standings
from ui.widgets.match_widget import MatchCard
from ui.widgets.bracket_view import BracketView

STAGE_TYPE_LABEL = {"round_robin": "Round Robin", "single_elim": "Eliminacion directa", "swiss": "Suizo"}


class _ResultDialog(QDialog):
    def __init__(self, match, name1, name2, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Resultado: {name1} vs {name2}")
        form = QFormLayout(self)
        self.spin1 = QSpinBox(); self.spin1.setRange(0, 99); self.spin1.setValue(match.score1)
        self.spin2 = QSpinBox(); self.spin2.setRange(0, 99); self.spin2.setValue(match.score2)
        form.addRow(f"{name1}:", self.spin1)
        form.addRow(f"{name2}:", self.spin2)
        btns = QHBoxLayout()
        ok = QPushButton("Guardar"); ok.setObjectName("primary")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancelar"); cancel.clicked.connect(self.reject)
        btns.addWidget(cancel); btns.addWidget(ok)
        form.addRow(btns)

    def values(self):
        return self.spin1.value(), self.spin2.value()


class TournamentView(QWidget):
    def __init__(self, tournament_id, on_back, parent=None):
        super().__init__(parent)
        self.tournament_id = tournament_id
        self.on_back = on_back
        self.layout_root = QVBoxLayout(self)
        self.layout_root.setContentsMargins(24, 20, 24, 20)
        self.reload()

    def _team_name(self, team_id):
        if not team_id:
            return "?"
        for t in self.tournament.teams:
            if t.id == team_id:
                return f"{t.name}" + (f" [{t.tag}]" if t.tag else "")
        return "?"

    def reload(self):
        self.tournament = storage.load_tournament(self.tournament_id)
        while self.layout_root.count():
            item = self.layout_root.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)   # desvincula inmediatamente para que no quede pintado encima
                w.deleteLater()
        self._build()

    def _build(self):
        t = self.tournament
        top = QHBoxLayout()
        back_btn = QPushButton("← Torneos")
        back_btn.clicked.connect(self.on_back)
        top.addWidget(back_btn)
        top.addStretch()
        status_map = {"setup": "En configuracion", "in_progress": "En curso", "finished": "Finalizado"}
        status_lbl = QLabel(status_map.get(t.status, t.status))
        status_lbl.setStyleSheet("color:#3fd17f; font-weight:600;" if t.status == "finished"
                                  else "color:#3ba7ff; font-weight:600;")
        top.addWidget(status_lbl)
        self.layout_root.addLayout(top)

        title = QLabel(t.name)
        title.setObjectName("pageTitle")
        self.layout_root.addWidget(title)
        subtitle = QLabel(f"{t.date}  ·  Importancia: {t.importance_label} (x{t.importance})  ·  "
                           f"{len(t.teams)} equipos")
        subtitle.setObjectName("pageSubtitle")
        self.layout_root.addWidget(subtitle)

        tabs = QTabWidget()
        for idx, stage in enumerate(t.stages):
            tabs.addTab(self._build_stage_tab(idx, stage), stage.name)
        if t.status == "finished":
            tabs.addTab(self._build_final_standings_tab(), "🏆 Clasificacion final")
        self.layout_root.addWidget(tabs)

    def _build_stage_tab(self, stage_idx, stage):
        t = self.tournament
        container = QWidget()
        layout = QVBoxLayout(container)

        info = QLabel(f"Formato: {STAGE_TYPE_LABEL.get(stage.type, stage.type)}"
                       + (f"  ·  BO{stage.config.get('bo', 1)}" if stage.config.get("bo", 1) > 1 else ""))
        info.setStyleSheet("color:#9aa1ad; font-size:12px;")
        header_row = QHBoxLayout()
        header_row.addWidget(info)
        header_row.addStretch()
        if stage.matches and not stage.finished:
            dice_btn = QPushButton("🎲 Aleatorizar resultados pendientes")
            dice_btn.clicked.connect(lambda: self._randomize_stage(stage_idx))
            header_row.addWidget(dice_btn)
        layout.addLayout(header_row)

        if not stage.matches:
            waiting = QLabel("Esta etapa aun no ha comenzado (esperando a que termine la etapa anterior).")
            waiting.setStyleSheet("color:#9aa1ad; font-style: italic; padding: 20px;")
            layout.addWidget(waiting)
            return container

        if stage.type == "single_elim":
            bracket = BracketView()
            bracket.setMinimumHeight(420)
            bracket.set_data(stage, self._team_name)
            bracket.match_clicked.connect(lambda mid, s=stage: self._open_result_dialog(s, mid))
            layout.addWidget(bracket)
        else:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            inner = QWidget()
            inner_layout = QVBoxLayout(inner)

            groups_cfg = stage.config.get("groups") if stage.type == "round_robin" else None
            if groups_cfg:
                live_standings = standings.group_standings_live(stage)
                for label in sorted(groups_cfg.keys()):
                    group_matches = [m for m in stage.matches if m.group == label]
                    glabel = QLabel(f"Grupo {label}")
                    glabel.setStyleSheet("font-weight:800; font-size:15px; margin-top:14px; color:#ff6a1a;")
                    inner_layout.addWidget(glabel)

                    inner_layout.addWidget(self._build_group_standings_table(live_standings.get(label, [])))
                    self._add_matches_by_round(inner_layout, group_matches, stage)
            else:
                self._add_matches_by_round(inner_layout, stage.matches, stage)

            inner_layout.addStretch()
            scroll.setWidget(inner)
            layout.addWidget(scroll)

        if stage.finished and self._is_actionable_finished_stage(stage_idx):
            btn_row = QHBoxLayout()
            btn_row.addStretch()
            if stage_idx + 1 < len(t.stages):
                btn = QPushButton(f"Cerrar etapa y pasar a {t.stages[stage_idx + 1].name} →")
            else:
                btn = QPushButton("Finalizar torneo y repartir puntos 🏆")
            btn.setObjectName("primary")
            btn.clicked.connect(lambda: self._close_stage(stage_idx))
            btn_row.addWidget(btn)
            layout.addLayout(btn_row)

        return container

    def _add_matches_by_round(self, parent_layout, matches, stage):
        matches_by_round = {}
        for m in matches:
            matches_by_round.setdefault(m.round, []).append(m)
        for rnd in sorted(matches_by_round.keys()):
            rlabel = QLabel(f"Ronda {rnd}")
            rlabel.setStyleSheet("font-weight:700; font-size:13px; margin-top:8px;")
            parent_layout.addWidget(rlabel)
            grid = QGridLayout()
            grid.setSpacing(10)
            col_count = 3
            for i, m in enumerate(sorted(matches_by_round[rnd], key=lambda x: x.slot)):
                card = MatchCard(m, self._team_name)
                card.result_saved.connect(lambda mid, s1, s2, s=stage: self._save_result(s, mid, s1, s2))
                grid.addWidget(card, i // col_count, i % col_count)
            parent_layout.addLayout(grid)

    def _build_group_standings_table(self, records):
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Equipo", "V", "D", "Dif."])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setFixedHeight(min(34 * (len(records) + 1), 220))
        for r in records:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(self._team_name(r["team_id"])))
            wins_item = QTableWidgetItem(str(r["wins"])); wins_item.setTextAlignment(Qt.AlignCenter)
            losses_item = QTableWidgetItem(str(r["losses"])); losses_item.setTextAlignment(Qt.AlignCenter)
            diff_item = QTableWidgetItem(f'{"+" if r["score_diff"] >= 0 else ""}{r["score_diff"]}')
            diff_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 1, wins_item)
            table.setItem(row, 2, losses_item)
            table.setItem(row, 3, diff_item)
        return table

    def _is_actionable_finished_stage(self, stage_idx):
        t = self.tournament
        stage = t.stages[stage_idx]
        if not stage.finished:
            return False
        if stage_idx + 1 < len(t.stages):
            return not t.stages[stage_idx + 1].matches
        return t.status != "finished"

    def _open_result_dialog(self, stage, match_id):
        match = next(m for m in stage.matches if m.id == match_id)
        if match.bye or not match.team1_id or not match.team2_id:
            return
        dlg = _ResultDialog(match, self._team_name(match.team1_id), self._team_name(match.team2_id), self)
        if dlg.exec() == QDialog.Accepted:
            s1, s2 = dlg.values()
            self._save_result(stage, match_id, s1, s2)

    def _save_result(self, stage, match_id, s1, s2):
        t = self.tournament
        real_stage = next(s for s in t.stages if s.id == stage.id)
        tl.record_result(real_stage, match_id, s1, s2)
        tl.advance_round_if_ready(real_stage)
        storage.save_tournament(t)
        self.reload()

    def _randomize_stage(self, stage_idx):
        t = self.tournament
        stage = t.stages[stage_idx]
        filled = tl.randomize_pending_matches(stage)
        storage.save_tournament(t)
        self.reload()
        if filled == 0:
            QMessageBox.information(self, "Nada que aleatorizar",
                                     "No hay partidos pendientes de resultado en esta etapa.")

    def _close_stage(self, stage_idx):
        t = self.tournament
        stage = t.stages[stage_idx]
        tl.finalize_stage_standings(stage)
        if stage_idx + 1 < len(t.stages):
            next_stage = t.stages[stage_idx + 1]
            advance_count = next_stage.config.get("advance_from_prev", len(stage.participants))
            next_stage.participants = tl.build_next_stage_participants(stage, advance_count)
            tl.start_stage(t, next_stage)
        else:
            tl.compute_final_standings(t)
        storage.save_tournament(t)
        self.reload()

    def _build_final_standings_tab(self):
        t = self.tournament
        w = QWidget()
        layout = QVBoxLayout(w)
        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["Posicion", "Equipo", "Puntos"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        for r in t.final_standings:
            row = table.rowCount()
            table.insertRow(row)
            pos_label = str(r["position_from"]) if r["position_from"] == r["position_to"] \
                else f"{r['position_from']}-{r['position_to']}"
            table.setItem(row, 0, QTableWidgetItem(pos_label))
            table.setItem(row, 1, QTableWidgetItem(self._team_name(r["team_id"])))
            pts_item = QTableWidgetItem(f"{r['points']:.1f}")
            font = pts_item.font(); font.setBold(True)
            pts_item.setFont(font)
            table.setItem(row, 2, pts_item)
        layout.addWidget(table)
        return w
