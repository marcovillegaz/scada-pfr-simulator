from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QStackedWidget
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import Qt

from constants import APP_NAME, APP_TITLE, PFR_MODULE_NAME, RTD_MODULE_NAME
from ui.home_screen import HomeScreen
from ui.about_view import AboutView
from workspaces.pfr_workspace import PFRWorkspace
from workspaces.rtd_workspace import RTDWorkspace

# Preferred size mirrors the old fixed-size window (kept as a comfortable
# default); minimum size is what a 1366×768 laptop with 125% Windows scaling
# can actually offer without clipping the footer controls.
_PREFERRED_W = 1240
_PREFERRED_H = 808
_MIN_W = 960
_MIN_H = 640


class MainWindow(QMainWindow):
    """Thin app shell: owns the window chrome (title, sizing, F11 fullscreen)
    and a QStackedWidget of pages — Home, each simulation workspace, and the
    shared About view. Simulation-specific logic lives in the workspaces
    under scada_app/workspaces/.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(_MIN_W, _MIN_H)
        self._fullscreen = False

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._home = HomeScreen()
        self._pfr = PFRWorkspace()
        self._rtd = RTDWorkspace()
        self._about = AboutView()

        self._idx_home = self._stack.addWidget(self._home)
        self._idx_pfr  = self._stack.addWidget(self._pfr)
        self._idx_rtd  = self._stack.addWidget(self._rtd)
        self._idx_about = self._stack.addWidget(self._about)

        self._home.pfr_requested.connect(self._show_pfr)
        self._home.rtd_requested.connect(self._show_rtd)
        self._home.about_requested.connect(self._show_about)
        self._pfr.home_requested.connect(self._show_home)
        self._rtd.home_requested.connect(self._show_home)
        self._about.home_requested.connect(self._show_home)

        self._stack.setCurrentIndex(self._idx_home)
        self._fit_to_screen()

    # ── Navigation ─────────────────────────────────────────────────────────────
    # Each page also owns its own in-page module-name label (top-right of the
    # PFR/RTD workspace headers); this keeps the OS window title consistent
    # with it instead of frozen on APP_TITLE while inside a module.

    def _show_home(self) -> None:
        self._stack.setCurrentIndex(self._idx_home)
        self.setWindowTitle(APP_TITLE)

    def _show_pfr(self) -> None:
        self._stack.setCurrentIndex(self._idx_pfr)
        self.setWindowTitle(f"{APP_NAME} — {PFR_MODULE_NAME}")

    def _show_rtd(self) -> None:
        self._stack.setCurrentIndex(self._idx_rtd)
        self.setWindowTitle(f"{APP_NAME} — {RTD_MODULE_NAME}")

    def _show_about(self) -> None:
        self._stack.setCurrentIndex(self._idx_about)
        self.setWindowTitle(APP_TITLE)

    # ── Sizing: fit the available screen instead of a hard-locked size ──────────

    def _fit_to_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(_PREFERRED_W, _PREFERRED_H)
            return

        avail = screen.availableGeometry()
        w = min(_PREFERRED_W, avail.width())
        h = min(_PREFERRED_H, avail.height())
        self.resize(w, h)
        self.move(
            avail.x() + (avail.width() - w) // 2,
            avail.y() + (avail.height() - h) // 2,
        )
        # Screen is smaller than our preferred size — maximize to reclaim
        # every available pixel instead of leaving the window cramped.
        if avail.width() < _PREFERRED_W or avail.height() < _PREFERRED_H:
            self.showMaximized()

    # ── Full-screen toggle (F11) ──────────────────────────────────────────────

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_F11:
            if self._fullscreen:
                self.showNormal()
                self._fullscreen = False
            else:
                self.showFullScreen()
                self._fullscreen = True
        else:
            super().keyPressEvent(event)
