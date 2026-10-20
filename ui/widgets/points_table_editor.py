from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                                 QPushButton, QLabel, QSpinBox)
from core.models import PointsRange


class PointsTableEditor(QWidget):
    """Tabla editable: cada fila es un rango de posiciones (ej. 3-4) con sus puntos."""

    def __init__(self, points_table: list[PointsRange] = None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        info = QLabel("Define cuantos puntos gana cada posicion final del torneo.")
        info.setStyleSheet("color: #9aa1ad; font-size: 11.5px;")
        layout.addWidget(info)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Desde", "Hasta", "Puntos"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Añadir rango")
        add_btn.clicked.connect(self.add_row)
        del_btn = QPushButton("Eliminar seleccionado")
        del_btn.clicked.connect(self.remove_selected)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        if points_table:
            for pr in points_table:
                self.add_row(pr.pos_from, pr.pos_to, pr.points)

    def add_row(self, pos_from=1, pos_to=1, points=0):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, val in enumerate([pos_from, pos_to, points]):
            spin = QSpinBox()
            spin.setRange(0, 999)
            spin.setValue(val)
            self.table.setCellWidget(row, col, spin)

    def remove_selected(self):
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)

    def get_points_table(self) -> list[PointsRange]:
        result = []
        for row in range(self.table.rowCount()):
            pf = self.table.cellWidget(row, 0).value()
            pt = self.table.cellWidget(row, 1).value()
            pts = self.table.cellWidget(row, 2).value()
            result.append(PointsRange(pf, pt, pts))
        return result
