from __future__ import annotations

import sys
import os

# Add scada_app directory to path so sibling imports work
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication

from app import MainWindow
from styles import SCADA_DARK


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(SCADA_DARK)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
