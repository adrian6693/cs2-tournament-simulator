from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
                                 QSpinBox, QDoubleSpinBox, QPushButton, QStackedWidget, QWidget,
                                 QGroupBox, QFormLayout, QListWidget, QListWidgetItem, QCheckBox,
                                 QMessageBox, QDateEdit, QAbstractItemView, QFileDialog)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QDate
from core.models import Tournament, Stage, Team, new_id
from core import tournament_logic as tl, points as points_mod, storage
from ui.widgets.points_table_editor import PointsTableEditor

IMPORTANCE_PRESETS = [
    ("Local / Comunidad", 0.5),
    ("Regional", 1.0),
    ("Nacional", 1.5),
    ("Internacional", 2.5),
    ("Major / Elite", 4.0),
]

STAGE_TYPE_OPTIONS = [
    ("round_robin", "Round Robin (liga todos contra todos)"),
    ("single_elim", "Eliminacion directa"),
    ("swiss", "Sistema suizo"),
]


class StageConfigWidget(QGroupBox):
    def __init__(self, title):
        super().__init__(title)
        layout = QFormLayout(self)

        self.type_combo = QComboBox()
        for key, label in STAGE_TYPE_OPTIONS:
            self.type_combo.addItem(label, key)
        layout.addRow("Formato:", self.type_combo)

        self.bo_spin = QSpinBox()
        self.bo_spin.setRange(1, 5)
        self.bo_spin.setSingleStep(2)
        self.bo_spin.setValue(1)
        layout.addRow("Al mejor de (mapas):", self.bo_spin)

        self.double_round_check = QCheckBox("Ida y vuelta (doble round robin)")
        layout.addRow("", self.double_round_check)

        self.num_groups_spin = QSpinBox()
        self.num_groups_spin.setRange(1, 8)
        self.num_groups_spin.setValue(1)
        self.num_groups_spin.setSpecialValueText("Sin grupos (todos contra todos)")
        layout.addRow("Numero de grupos:", self.num_groups_spin)

        self.swiss_rounds_spin = QSpinBox()
        self.swiss_rounds_spin.setRange(0, 10)
        self.swiss_rounds_spin.setSpecialValueText("Automatico")
        layout.addRow("Rondas suizas:", self.swiss_rounds_spin)

        self.type_combo.currentIndexChanged.connect(self._update_visibility)
        self._update_visibility()

    def _update_visibility(self):
        t = self.type_combo.currentData()
        self.double_round_check.setVisible(t == "round_robin")
        self.num_groups_spin.setVisible(t == "round_robin")
        self.swiss_rounds_spin.setVisible(t == "swiss")

    def get_config(self):
        t = self.type_combo.currentData()
        config = {"bo": self.bo_spin.value()}
        if t == "round_robin":
            config["double_round"] = self.double_round_check.isChecked()
            config["num_groups"] = self.num_groups_spin.value()
        if t == "swiss" and self.swiss_rounds_spin.value() > 0:
            config["rounds"] = self.swiss_rounds_spin.value()
        return t, config


class TournamentWizard(QDialog):
    def __init__(self, all_teams: list[Team], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo torneo")
        self.resize(640, 560)
        self.all_teams = all_teams
        self.result_tournament = None

        self.stack = QStackedWidget()
        self.pages = [self._page_basic(), self._page_stages(), self._page_teams(), self._page_points()]
        for p in self.pages:
            self.stack.addWidget(p)

        self.step_label = QLabel()
        self.step_label.setStyleSheet("color:#9aa1ad; font-size:11px;")

        nav = QHBoxLayout()
        self.back_btn = QPushButton("Atras")
        self.back_btn.clicked.connect(self._go_back)
        self.next_btn = QPushButton("Siguiente")
        self.next_btn.setObjectName("primary")
        self.next_btn.clicked.connect(self._go_next)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        nav.addWidget(cancel_btn)
        nav.addStretch()
        nav.addWidget(self.step_label)
        nav.addWidget(self.back_btn)
        nav.addWidget(self.next_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)
        layout.addLayout(nav)
        self._refresh_nav()

    # ---------------- Paso 1: datos basicos ----------------
    def _page_basic(self):
        w = QWidget()
        form = QFormLayout(w)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ej: Copa Primavera 2026")
        form.addRow("Nombre del torneo:", self.name_edit)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form.addRow("Fecha:", self.date_edit)

        self.importance_combo = QComboBox()
        for label, mult in IMPORTANCE_PRESETS:
            self.importance_combo.addItem(f"{label}  (x{mult})", (label, mult))
        self.importance_combo.setCurrentIndex(1)
        form.addRow("Importancia:", self.importance_combo)

        self.custom_mult = QDoubleSpinBox()
        self.custom_mult.setRange(0.1, 20.0)
        self.custom_mult.setSingleStep(0.1)
        self.custom_mult.setValue(1.0)
        self.custom_mult.setVisible(False)
        form.addRow("Multiplicador personalizado:", self.custom_mult)

        self.importance_combo.currentIndexChanged.connect(self._sync_custom_mult)

        trophy_row = QHBoxLayout()
        self.trophy_path = None
        self.trophy_preview = QLabel()
        self.trophy_preview.setFixedSize(40, 40)
        self.trophy_preview.setStyleSheet("border:1px solid #2d323c; border-radius:6px;")
        self.trophy_preview.setAlignment(Qt.AlignCenter)
        self.trophy_preview.setText("🏆")
        trophy_btn = QPushButton("Subir imagen de trofeo (opcional)")
        trophy_btn.clicked.connect(self._pick_trophy_image)
        trophy_row.addWidget(self.trophy_preview)
        trophy_row.addWidget(trophy_btn)
        trophy_row.addStretch()
        form.addRow("Trofeo del campeon:", trophy_row)

        return w

    def _pick_trophy_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Elige una imagen de trofeo", "",
                                               "Imagenes (*.png *.jpg *.jpeg *.webp *.gif)")
        if not path:
            return
        self.trophy_path = path
        pix = QPixmap(path)
        if not pix.isNull():
            pix = pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.trophy_preview.setPixmap(pix)
            self.trophy_preview.setText("")

    def _sync_custom_mult(self):
        _, mult = self.importance_combo.currentData()
        self.custom_mult.setValue(mult)

    # ---------------- Paso 2: etapas ----------------
    def _page_stages(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        row = QHBoxLayout()
        row.addWidget(QLabel("Numero de etapas:"))
        self.num_stages_combo = QComboBox()
        self.num_stages_combo.addItem("Una etapa", 1)
        self.num_stages_combo.addItem("Dos etapas (fase de grupos + final)", 2)
        row.addWidget(self.num_stages_combo)
        row.addStretch()
        layout.addLayout(row)

        self.stage1_widget = StageConfigWidget("Etapa 1")
        layout.addWidget(self.stage1_widget)

        self.stage2_widget = StageConfigWidget("Etapa 2")
        layout.addWidget(self.stage2_widget)

        adv_row = QHBoxLayout()
        adv_row.addWidget(QLabel("Equipos que avanzan de la etapa 1 a la etapa 2:"))
        self.advance_spin = QSpinBox()
        self.advance_spin.setRange(2, 64)
        self.advance_spin.setValue(4)
        adv_row.addWidget(self.advance_spin)
        adv_row.addStretch()
        self.advance_row_widget = QWidget()
        self.advance_row_widget.setLayout(adv_row)
        layout.addWidget(self.advance_row_widget)

        layout.addStretch()

        self.num_stages_combo.currentIndexChanged.connect(self._update_stage2_visibility)
        self._update_stage2_visibility()
        return w

    def _update_stage2_visibility(self):
        two_stages = self.num_stages_combo.currentData() == 2
        self.stage2_widget.setVisible(two_stages)
        self.advance_row_widget.setVisible(two_stages)

    # ---------------- Paso 3: equipos y seeding ----------------
    def _page_teams(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        info = QLabel("Selecciona los equipos que participan y ordenalos por seed "
                       "(el primero de la lista es el cabeza de serie nº1). "
                       "Usa los botones para reordenar.")
        info.setWordWrap(True)
        info.setStyleSheet("color:#9aa1ad; font-size:11.5px;")
        layout.addWidget(info)

        cols = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(QLabel("Equipos disponibles:"))
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        for t in self.all_teams:
            item = QListWidgetItem(f"{t.name} [{t.tag}]" if t.tag else t.name)
            item.setData(Qt.UserRole, t.id)
            self.available_list.addItem(item)
        left.addWidget(self.available_list)
        add_btn = QPushButton("Añadir al torneo →")
        add_btn.clicked.connect(self._add_teams_to_seed)
        left.addWidget(add_btn)
        cols.addLayout(left)

        right = QVBoxLayout()
        right.addWidget(QLabel("Orden de seed (1º = mejor):"))
        self.seed_list = QListWidget()
        right.addWidget(self.seed_list)
        btn_row = QHBoxLayout()
        up_btn = QPushButton("↑ Subir")
        up_btn.clicked.connect(lambda: self._move_seed(-1))
        down_btn = QPushButton("↓ Bajar")
        down_btn.clicked.connect(lambda: self._move_seed(1))
        remove_btn = QPushButton("Quitar")
        remove_btn.clicked.connect(self._remove_seed)
        btn_row.addWidget(up_btn); btn_row.addWidget(down_btn); btn_row.addWidget(remove_btn)
        right.addLayout(btn_row)
        cols.addLayout(right)

        layout.addLayout(cols)
        return w

    def _add_teams_to_seed(self):
        for item in self.available_list.selectedItems():
            tid = item.data(Qt.UserRole)
            already = [self.seed_list.item(i).data(Qt.UserRole) for i in range(self.seed_list.count())]
            if tid in already:
                continue
            new_item = QListWidgetItem(item.text())
            new_item.setData(Qt.UserRole, tid)
            self.seed_list.addItem(new_item)

    def _move_seed(self, delta):
        row = self.seed_list.currentRow()
        new_row = row + delta
        if row < 0 or new_row < 0 or new_row >= self.seed_list.count():
            return
        item = self.seed_list.takeItem(row)
        self.seed_list.insertItem(new_row, item)
        self.seed_list.setCurrentRow(new_row)

    def _remove_seed(self):
        row = self.seed_list.currentRow()
        if row >= 0:
            self.seed_list.takeItem(row)

    # ---------------- Paso 4: puntos ----------------
    def _page_points(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel("Reparto de puntos por posicion final:"))
        self.points_editor = PointsTableEditor()
        layout.addWidget(self.points_editor)
        regen_btn = QPushButton("Generar plantilla segun nº de equipos")
        regen_btn.clicked.connect(self._regen_points)
        layout.addWidget(regen_btn)
        return w

    def _regen_points(self):
        n = max(self.seed_list.count(), 2)
        table = points_mod.default_points_table(n)
        self.points_editor.table.setRowCount(0)
        for pr in table:
            self.points_editor.add_row(pr.pos_from, pr.pos_to, pr.points)

    # ---------------- Navegacion ----------------
    def _refresh_nav(self):
        idx = self.stack.currentIndex()
        total = self.stack.count()
        self.step_label.setText(f"Paso {idx + 1} de {total}")
        self.back_btn.setEnabled(idx > 0)
        self.next_btn.setText("Crear torneo" if idx == total - 1 else "Siguiente")
        if idx == total - 1 and self.points_editor.table.rowCount() == 0:
            self._regen_points()

    def _go_back(self):
        self.stack.setCurrentIndex(self.stack.currentIndex() - 1)
        self._refresh_nav()

    def _go_next(self):
        idx = self.stack.currentIndex()
        if not self._validate_page(idx):
            return
        if idx == self.stack.count() - 1:
            self._finish()
            return
        self.stack.setCurrentIndex(idx + 1)
        self._refresh_nav()

    def _validate_page(self, idx):
        if idx == 0 and not self.name_edit.text().strip():
            QMessageBox.warning(self, "Falta el nombre", "Ponle un nombre al torneo.")
            return False
        if idx == 2 and self.seed_list.count() < 2:
            QMessageBox.warning(self, "Faltan equipos", "Añade al menos 2 equipos al torneo.")
            return False
        if idx == 2 and self.num_stages_combo.currentData() == 2:
            if self.advance_spin.value() >= self.seed_list.count():
                QMessageBox.warning(self, "Revisa el nº de clasificados",
                                     "El numero de equipos que avanzan debe ser menor que el total.")
                return False
        if idx == 2:
            type1, _ = self.stage1_widget.get_config()
            if type1 == "round_robin" and self.stage1_widget.num_groups_spin.value() > 1:
                num_groups = self.stage1_widget.num_groups_spin.value()
                if num_groups > self.seed_list.count() // 2:
                    QMessageBox.warning(self, "Demasiados grupos",
                                         "Con ese numero de equipos, algun grupo se quedaria con menos "
                                         "de 2 equipos. Reduce el numero de grupos en la Etapa 1.")
                    return False
            if self.num_stages_combo.currentData() == 2:
                type2, _ = self.stage2_widget.get_config()
                if type2 == "round_robin" and self.stage2_widget.num_groups_spin.value() > 1:
                    num_groups2 = self.stage2_widget.num_groups_spin.value()
                    if num_groups2 > self.advance_spin.value() // 2:
                        QMessageBox.warning(self, "Demasiados grupos",
                                             "Con los equipos que avanzan a la Etapa 2, algun grupo se "
                                             "quedaria con menos de 2 equipos. Reduce el numero de grupos.")
                        return False
        return True

    def _finish(self):
        label, _ = self.importance_combo.currentData()
        importance = self.custom_mult.value()

        t = Tournament(id=new_id(), name=self.name_edit.text().strip(),
                        date=self.date_edit.date().toString("yyyy-MM-dd"),
                        importance=importance, importance_label=label, status="in_progress")

        seed_team_ids = [self.seed_list.item(i).data(Qt.UserRole) for i in range(self.seed_list.count())]
        t.teams = [tm for tm in self.all_teams if tm.id in seed_team_ids]
        t.teams.sort(key=lambda tm: seed_team_ids.index(tm.id))

        type1, config1 = self.stage1_widget.get_config()
        stage1 = Stage(id=new_id(), name="Etapa 1", type=type1, config=config1, participants=seed_team_ids)
        t.stages.append(stage1)

        if self.num_stages_combo.currentData() == 2:
            type2, config2 = self.stage2_widget.get_config()
            stage2 = Stage(id=new_id(), name="Etapa 2", type=type2, config=config2, participants=[])
            stage2.config["advance_from_prev"] = self.advance_spin.value()
            t.stages.append(stage2)

        t.points_table = self.points_editor.get_points_table()
        tl.start_stage(t, stage1)

        if self.trophy_path:
            t.trophy_image = storage.copy_trophy_image(self.trophy_path, t.id)

        self.result_tournament = t
        self.accept()
