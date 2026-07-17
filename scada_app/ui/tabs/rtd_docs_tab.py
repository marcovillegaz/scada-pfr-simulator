from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QGroupBox,
)
from PyQt6.QtCore import Qt


def _body(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setTextFormat(Qt.TextFormat.RichText)
    lbl.setStyleSheet("color:#eeeeec;font-size:12px;line-height:150%;")
    return lbl


def _section(title: str, *widgets) -> QGroupBox:
    box = QGroupBox(title)
    lay = QVBoxLayout(box)
    lay.setSpacing(8)
    for w in widgets:
        lay.addWidget(w)
    return box


class RTDDocsTab(QWidget):
    """In-app documentation for the RTD (Experiencia 3) module.

    Deliberately a summary/how-to, not the full derivation -- the complete
    mathematical treatment lives in docs/FUNDAMENTS_EXP3.md as an instructor
    reference. This tab orients the student on what the experiment is and
    how to run it, mirroring AboutTab's section-card layout.
    """

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

        title = QLabel("RTD — Experiencia 3: Flujo No Ideal")
        title.setStyleSheet("color:#E95420;font-size:20px;font-weight:bold;")
        lay.addWidget(title)

        subtitle = QLabel(
            "Ensayo de trazador estímulo-respuesta sobre un lecho fijo con "
            "patologías hidrodinámicas ocultas."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color:#adadad;font-size:12px;")
        lay.addWidget(subtitle)

        lay.addWidget(_section(
            "Objetivo",
            _body(
                "Diagnosticar el estado hidrodinámico de la columna R-201 mediante "
                "un ensayo de trazador: inyectar una perturbación conocida (pulso o "
                "escalón) en la entrada y registrar la respuesta de absorbancia en "
                "el fotocolorímetro AIT-201 a la salida.<br><br>"
                "El equipo puede tener canalización (cortocircuito de una fracción "
                "del caudal) y/o zonas muertas (volumen estancado). Ninguno de estos "
                "defectos es visible directamente — solo se infieren a partir de la "
                "forma de la curva medida."
            ),
        ))

        lay.addWidget(_section(
            "Procedimiento",
            _body(
                "1. Ajustar el caudal Q en el diagrama (recuadro bajo FIC-101) y "
                "presionar <b>Apply</b>.<br>"
                "2. Presionar <b>GO</b> para iniciar el registro.<br>"
                "3. Inyectar un <b>pulso</b> (dosis en mol) o iniciar un "
                "<b>escalón</b> (concentración C0) desde el panel de inyección.<br>"
                "4. Observar la curva de absorbancia en la pestaña <b>Graph</b>.<br>"
                "5. Presionar <b>STOP</b> y exportar la serie desde la pestaña "
                "<b>Table</b> (CSV o Excel) para su análisis fuera del simulador."
            ),
        ))

        lay.addWidget(_section(
            "Qué mide el sensor",
            _body(
                "AIT-201 no entrega concentración: entrega absorbancia, muestreada "
                "a intervalo fijo y con ruido de medición, siguiendo la ley de "
                "Lambert-Beer (A = ε·b·C). La conversión a concentración y la "
                "reconstrucción de la curva E(t) son responsabilidad del estudiante "
                "al procesar los datos exportados."
            ),
        ))

        lay.addWidget(_section(
            "Análisis esperado",
            _body(
                "A partir de la serie exportada: normalizar la curva para obtener "
                "E(t), calcular sus momentos (tiempo medio de residencia, "
                "varianza), compararlos contra el comportamiento ideal "
                "(τ = V/Q), y ajustar los modelos de tanques en serie y de "
                "dispersión axial. El fundamento matemático completo — "
                "incluyendo el modelo de compartimientos, la interpretación del "
                "volumen muerto y la deducción de cada ecuación — está disponible "
                "para el docente en <b>docs/FUNDAMENTS_EXP3.md</b>."
            ),
        ))

        lay.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        scroll.setStyleSheet("QScrollArea{border:none;background:#1e2a35;}")
        root.addWidget(scroll)
