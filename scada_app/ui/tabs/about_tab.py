from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QGroupBox,
)
from PyQt6.QtCore import Qt

from constants import APP_VERSION, APP_TITLE

_LINKEDIN = "https://www.linkedin.com/in/marcovillegasg/"
_EMAIL = "marco.villegas@usach.cl"
_AUTHOR = "Marco Villegas G."
_INSTITUTION = "Universidad de Santiago de Chile (USACH)"
_YEAR = "2026"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _body(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setOpenExternalLinks(True)
    lbl.setTextFormat(Qt.TextFormat.RichText)
    lbl.setTextInteractionFlags(
        Qt.TextInteractionFlag.TextBrowserInteraction
    )
    lbl.setStyleSheet("color:#eeeeec;font-size:12px;line-height:150%;")
    return lbl


def _section(title: str, *widgets) -> QGroupBox:
    box = QGroupBox(title)
    lay = QVBoxLayout(box)
    lay.setSpacing(8)
    for w in widgets:
        lay.addWidget(w)
    return box


class AboutTab(QWidget):
    """Project context, author/contact, license, citation and version history."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(14)

        # ── Header ────────────────────────────────────────────────────────────
        title = QLabel(APP_TITLE)
        title.setStyleSheet("color:#E95420;font-size:20px;font-weight:bold;")
        lay.addWidget(title)

        subtitle = QLabel(
            "An interactive SCADA simulator of a plug-flow reactor (PFR) for "
            "teaching chemical reaction kinetics."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color:#adadad;font-size:12px;")
        lay.addWidget(subtitle)

        # ── Sections ──────────────────────────────────────────────────────────
        lay.addWidget(_section(
            "Author & Contact",
            _body(
                f"<b>{_AUTHOR}</b><br>"
                "MSc in Chemical Engineering<br>"
                f"Professor, {_INSTITUTION}<br><br>"
                f"LinkedIn: <a style='color:#4fc3f7;' href='{_LINKEDIN}'>"
                "linkedin.com/in/marcovillegasg</a><br>"
                f"Email: <a style='color:#4fc3f7;' href='mailto:{_EMAIL}'>"
                f"{_EMAIL}</a>"
            ),
        ))

        lay.addWidget(_section(
            "About the Project",
            _body(
                "This application replaces a hands-on laboratory experience in a "
                "reaction-kinetics course. Students operate a virtual PFR running "
                "the saponification of ethyl acetate by sodium hydroxide "
                "(NaOH + EtAc → NaAc + EtOH): they set the feed flows and "
                "concentrations, choose a reactor temperature setpoint, and watch "
                "conversion, temperatures and outlet conductivity evolve in real "
                "time — then export the run for analysis.<br><br>"
                "The goal is to let students explore how temperature, residence "
                "time and feed composition govern conversion, and to read process "
                "instrumentation (temperature, conductivity) the way they would on "
                "a real SCADA panel — without the cost, time and safety constraints "
                "of the physical bench."
            ),
        ))

        lay.addWidget(_section(
            "Technology & Disclaimer",
            _body(
                "Built with <b>Python 3</b>, <b>PyQt6</b>, <b>pyqtgraph</b>, "
                "<b>NumPy</b> and <b>SciPy</b>. The reactor is integrated with the "
                "method of lines (RK45); the heat exchanger and sensors use "
                "lumped dynamic models.<br><br>"
                "<i>The models are simplified for teaching purposes. Results are "
                "illustrative and should not be taken as plant-accurate "
                "predictions.</i>"
            ),
        ))

        lay.addWidget(_section(
            "License",
            _body(
                "Free for academic and educational use. Please credit the author "
                "when reusing or adapting the simulator for teaching."
            ),
        ))

        lay.addWidget(_section(
            "How to Cite",
            _body(
                f"{_AUTHOR} ({_YEAR}). <i>{APP_TITLE}</i> [Software]. "
                f"{_INSTITUTION}."
            ),
        ))

        lay.addWidget(_section(
            f"What's New — v{APP_VERSION}",
            _body(
                "First stable release. Highlights:<br>"
                "• Dynamic PFR with realistic kinetics and reactor heat loss.<br>"
                "• Conductivity and temperature sensors with measurement noise.<br>"
                "• Live 2×2 graphs, data table with export, and admin debug view.<br>"
                "• Interactive P&ID with equipment dialogs and an event log.<br><br>"
                "See <b>CHANGELOG.md</b> for the full history."
            ),
        ))

        lay.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        scroll.setStyleSheet("QScrollArea{border:none;background:#1e2a35;}")
        root.addWidget(scroll)
