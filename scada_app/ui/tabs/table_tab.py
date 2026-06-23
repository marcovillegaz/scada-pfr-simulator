from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, QFileDialog,
    QLabel,
)
from PyQt6.QtCore import Qt

from engine.data_store import DataStore
from models.log_table_model import LogTableModel


class TableTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._df = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._status_lbl = QLabel("Run the simulation and press STOP to load data.")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_lbl)

        self._model = LogTableModel()
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(False)
        layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        self._btn_csv   = QPushButton("Export CSV")
        self._btn_excel = QPushButton("Export Excel")
        self._btn_csv.setEnabled(False)
        self._btn_excel.setEnabled(False)
        self._btn_csv.clicked.connect(self._export_csv)
        self._btn_excel.clicked.connect(self._export_excel)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_csv)
        btn_row.addWidget(self._btn_excel)
        layout.addLayout(btn_row)

    def update_on_stop(self, data_store: DataStore) -> None:
        snapshots = list(data_store.run_log)
        self._model.set_snapshots(snapshots)
        self._df = data_store.to_dataframe()
        n = len(snapshots)
        self._status_lbl.setText(f"{n} rows logged.")
        enabled = n > 0
        self._btn_csv.setEnabled(enabled)
        self._btn_excel.setEnabled(enabled)
        self._table.resizeColumnsToContents()

    def _export_csv(self) -> None:
        if self._df is None or self._df.empty:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "reactor_data.csv", "CSV files (*.csv)")
        if path:
            self._df.to_csv(path, index=False)

    def _export_excel(self) -> None:
        if self._df is None or self._df.empty:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Excel", "reactor_data.xlsx", "Excel files (*.xlsx)")
        if path:
            self._df.to_excel(path, index=False)
