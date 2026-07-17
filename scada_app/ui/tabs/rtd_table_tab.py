from __future__ import annotations

import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, QFileDialog,
    QLabel,
)
from PyQt6.QtCore import Qt

from engine.data_store import DataStore
from models.log_table_model import LogTableModel, RTD_COLUMNS


class RTDTableTab(QWidget):
    """Student data table + CSV/Excel export for the RTD run.

    Mirrors TableTab's structure and reuses LogTableModel directly (it's
    generic over any snapshot type via getattr()). DataStore.to_dataframe()
    is PFR-specific (hardcodes EngineSnapshot's fields), so this tab builds
    its own dataframe from RTD_COLUMNS instead of touching that shared
    method -- avoids risking a behavior change to the already-shipped PFR
    export path for a one-off column list.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._df = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._status_lbl = QLabel("Run the experiment and press STOP to load data.")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_lbl)

        self._model = LogTableModel(columns=RTD_COLUMNS)
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
        self._df = self._to_dataframe(snapshots)
        n = len(snapshots)
        self._status_lbl.setText(f"{n} rows logged.")
        enabled = n > 0
        self._btn_csv.setEnabled(enabled)
        self._btn_excel.setEnabled(enabled)
        self._table.resizeColumnsToContents()

    @staticmethod
    def _to_dataframe(snapshots: list) -> pd.DataFrame:
        if not snapshots:
            return pd.DataFrame()
        rows = [
            {header: getattr(s, attr) for attr, header, _scale in RTD_COLUMNS}
            for s in snapshots
        ]
        return pd.DataFrame(rows)

    def _export_csv(self) -> None:
        if self._df is None or self._df.empty:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "rtd_data.csv", "CSV files (*.csv)")
        if path:
            self._df.to_csv(path, index=False)

    def _export_excel(self) -> None:
        if self._df is None or self._df.empty:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Excel", "rtd_data.xlsx", "Excel files (*.xlsx)")
        if path:
            self._df.to_excel(path, index=False)
