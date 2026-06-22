from __future__ import annotations

import sys
import os

# Add scada_app directory to path so sibling imports work
sys.path.insert(0, os.path.dirname(__file__))

# Silence Qt SVG renderer warnings about complex path data
os.environ.setdefault("QT_LOGGING_RULES", "qt.svg.warning=false")

from PyQt6.QtWidgets import QApplication

from app import MainWindow
from styles import SCADA_DARK


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(SCADA_DARK)

    window = MainWindow()
    window.show()

    # Self-test hook: when SCADA_SELFTEST is set, build the window then quit.
    # Used to verify a frozen build boots and resolves its bundled assets.
    if os.environ.get("SCADA_SELFTEST"):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, app.quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
