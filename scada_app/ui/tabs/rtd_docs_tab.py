from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel

from constants import (
    RTD_PULSE_WIDTH_S, RTD_PULSE_DOSE_DEFAULT, RTD_STEP_C0_DEFAULT,
    RTD_DEFAULT_SCENARIO,
)
from scenarios.loader import load_scenario, load_sensor
from ui.tabs._docs_helpers import (
    narrative as _base_narrative,
    equation as _equation,
    tip as _tip,
    section as _section,
    scroll_tab as _scroll_tab,
)


def _narrative(text: str) -> QLabel:
    """RTD docs content is written with inline HTML (<b>, <br>) -- unlike
    docs_tab.py's plain-text narratives, this always renders as rich text."""
    return _base_narrative(text, rich=True)


# ── Sub-tab builders ──────────────────────────────────────────────────────────
# Content adapted from docs/modules/rtd/fundamentals.md. Deliberately stops short of
# §5's exact hidden compartment-network values (f, phi_d, k_ex, gamma, N_m,
# N_c) -- those are the "verdad oculta" the student is meant to diagnose, not
# be handed. Everything below is either general theory (the analysis tools
# any RTD study needs, regardless of the equipment under test) or this
# simulator's own visible/instrument settings.

def _tab_user_guide() -> QScrollArea:
    diagram = _section(
        "Pestaña Diagram — Ejecutar el ensayo",
        _narrative(
            "La pestaña Diagram es el P&amp;ID interactivo del skid de CIP. Los "
            "controles del pie de página manejan la corrida:"
        ),
        _narrative(
            "•  <b>GO / STOP</b> — inicia o detiene la simulación. STOP también "
            "carga la corrida en la pestaña Table.<br>"
            "•  <b>RESET</b> — vuelve a operación normal: limpia gráficos, "
            "registro de eventos y la selección de reactor.<br>"
            "•  <b>Speed</b> — acelera la simulación (1× a 100×) para no esperar "
            "varios τ en tiempo real.<br>"
            "•  <b>Apply</b> — envía el caudal editado (recuadro L/min bajo "
            "P-104) al modelo en ejecución."
        ),
        _narrative(
            "<b>Panel CIP Protocol.</b> Con ningún reactor seleccionado el "
            "sistema está en <i>operación normal</i> (los tres reactores en "
            "línea, sin inyección posible). Los botones R-102 / R-103 / R-104 "
            "aíslan un reactor a la vez para lavado — el estado actual del "
            "sistema se muestra siempre en el panel."
        ),
        _narrative(
            "<b>Panel Tracer Injection.</b> Con un reactor aislado, el panel "
            f"permite un pulso de dosis ajustable (mg) o un escalón de "
            f"concentración ajustable (mg/L) — ver la pestaña "
            f"<b>Técnica Estímulo–Respuesta</b> para la teoría detrás de cada uno."
        ),
        _tip(
            "Haz clic sobre el cuerpo de cualquier reactor o sobre el círculo "
            "AT-101 en el diagrama para abrir su ficha técnica (geometría, "
            "caudal nominal, calibración del instrumento) — funciona con "
            "cualquier reactor, esté o no seleccionado para CIP."
        ),
    )

    graph = _section(
        "Pestaña Graph — Tendencias en vivo",
        _narrative(
            "Muestra la curva de absorbancia A(t) medida por AT-101 a medida "
            "que la simulación avanza — la señal cruda que exportarás para el "
            "análisis fuera del simulador."
        ),
        _narrative(
            "Usa <b>Window</b> para fijar cuántos segundos de historial se "
            "muestran y <b>Reset View</b> para restaurar los ejes por defecto."
        ),
    )

    table = _section(
        "Pestaña Table — Datos y exportación",
        _narrative(
            "Al presionar <b>STOP</b> la corrida completa se carga en la "
            "pestaña Table como una tabla tiempo–caudal–absorbancia."
        ),
        _narrative(
            "Usa <b>Export CSV</b> o <b>Export Excel</b> para guardar la serie "
            "y procesarla en la hoja de cálculo o herramienta de tu preferencia."
        ),
        _tip(
            "Flujo típico: selecciona un reactor, ajusta el caudal si "
            "corresponde y presiona Apply, presiona GO, inyecta el trazador "
            "(pulso o escalón), deja correr varios τ, presiona STOP y exporta "
            "desde la pestaña Table."
        ),
    )

    return _scroll_tab(diagram, graph, table)


def _tab_fundamentals() -> QScrollArea:
    age = _section(
        "Edad y Tiempo de Residencia",
        _narrative(
            "La <b>edad</b> de un elemento de fluido es el tiempo transcurrido "
            "desde que ingresó al sistema. La distribución de tiempos de "
            "residencia (RTD), E(t), es la densidad de probabilidad de las "
            "edades del fluido que <i>abandona</i> el equipo."
        ),
        _equation(
            "E(t) dt = fracción del caudal de salida con edad entre t y t+dt\n"
            "\n"
            "∫₀^∞ E(t) dt = 1        (normalización, E(t) ≥ 0,  unidades s⁻¹)"
        ),
        _narrative(
            "La RTD no es observable directamente — el interior del reactor es "
            "inaccesible. Se determina mediante un ensayo estímulo–respuesta "
            "con un trazador (ver siguiente pestaña)."
        ),
    )

    ideal = _section(
        "Los Dos Casos Límite Ideales",
        _narrative(
            "Todo equipo real cae en algún punto entre dos extremos de "
            "mezclado:"
        ),
        _equation(
            "Flujo pistón (RFP):   E(t) = δ(t − τ)          (todos igual edad)\n"
            "Tanque agitado (RTAC): E(t) = (1/τ) · e^(−t/τ)  (mezcla instantánea)"
        ),
        _narrative(
            "τ = V/Q es el <b>tiempo espacial nominal</b> — el tiempo de "
            "residencia que tendría el equipo si el flujo fuera perfectamente "
            "uniforme. El objetivo del ensayo es medir cuánto se aleja la RTD "
            "real de estos dos extremos, y por qué."
        ),
        _tip(
            "Al terminar tu ensayo, superpón mentalmente tu curva E(t) medida "
            "contra estas dos formas — ¿se parece más a un pico angosto (RFP) "
            "o a una exponencial decreciente (RTAC)?"
        ),
    )

    return _scroll_tab(age, ideal)


def _tab_stimulus_response(tau_s: float) -> QScrollArea:
    dtp_over_tau = RTD_PULSE_WIDTH_S / tau_s
    pulse = _section(
        "Inyección Tipo Pulso",
        _narrative(
            "Se introduce una masa m de trazador en un intervalo breve en "
            "t=0 y se registra C(t) a la salida. Como todo el trazador "
            "ingresó simultáneamente, la concentración de salida es "
            "proporcional a la distribución de edades:"
        ),
        _equation(
            "E(t) = C(t) / ∫₀^∞ C(t) dt\n"
            "\n"
            "Verificación por balance de materia:   m = Q · ∫₀^∞ C(t) dt"
        ),
        _narrative(
            "Un pulso ideal (delta de Dirac) es físicamente irrealizable — una "
            "jeringa entrega un <b>pulso rectangular</b> de ancho finito Δt_p. "
            f"La aproximación es válida cuando Δt_p ≪ τ; en la práctica, "
            f"Δt_p/τ &lt; 0.05 es suficiente."
        ),
        _tip(
            f"El pulso por defecto de este simulador usa Δt_p = "
            f"{RTD_PULSE_WIDTH_S:.1f} s contra un τ nominal de "
            f"{tau_s:.0f} s (Δt_p/τ ≈ {dtp_over_tau:.3f}) — bien dentro del "
            f"límite de 0.05, así que el pulso simulado es una buena "
            f"aproximación de la delta ideal."
        ),
    )

    step = _section(
        "Inyección Tipo Escalón",
        _narrative(
            "Se conmuta la alimentación desde C=0 a C=C₀ constante en t=0 y "
            "se registra la salida. La respuesta normalizada es la "
            "<b>distribución acumulada</b> F(t): la fracción del fluido que "
            "sale con edad menor que t."
        ),
        _equation(
            "F(t) = C_out(t) / C₀ = ∫₀^t E(t') dt'        (F(0)=0, F(∞)=1)"
        ),
        _narrative(
            "Pulso y escalón contienen la misma información — disponer de "
            "ambos permite una <b>verificación cruzada</b>: la derivada "
            "numérica de F (del escalón) debe reproducir la E medida "
            "directamente por pulso."
        ),
        _equation("E(t) = dF(t)/dt"),
        _tip(
            "La derivación numérica amplifica el ruido; la integración lo "
            "atenúa. Espera que la E reconstruida desde el escalón se vea más "
            "ruidosa que la E obtenida directamente del pulso."
        ),
    )

    return _scroll_tab(pulse, step)


def _tab_measurement(sensor) -> QScrollArea:
    lambert = _section(
        "Cadena de Medición — Ley de Lambert–Beer",
        _narrative(
            "AT-101 no entrega concentración, entrega <b>absorbancia</b>. "
            "Para soluciones diluidas rige la ley de Lambert–Beer, donde el "
            "producto ε·b es la constante de calibración agrupada del "
            "instrumento:"
        ),
        _equation("A = ε · b · C"),
        _narrative(
            "La relación es lineal solo dentro de un rango acotado — sobre "
            "A_max el detector satura y la proporcionalidad se pierde. Esto "
            "impone una restricción de diseño experimental: la dosis debe "
            "superar el ruido del instrumento sin saturar el pico."
        ),
        _equation(
            f"ε·b (calibración AT-101) = {sensor.epsilon_b:.2f}  L/mg\n"
            f"Rango lineal                = 0 – {sensor.A_max:.2f}  AU\n"
            f"Período de muestreo         = {sensor.dt_sample_s:.1f}  s\n"
            f"Ruido de medición            ≈ {sensor.noise_std:.3f}  AU  (gaussiano)"
        ),
        _tip(
            f"Con la dosis de pulso por defecto ({RTD_PULSE_DOSE_DEFAULT:.0f} mg) "
            f"o el C0 de escalón por defecto ({RTD_STEP_C0_DEFAULT:.0f} mg/L) "
            "el pico de absorbancia queda cómodamente por debajo de A_max — "
            "si programas una dosis mucho mayor, revisa la curva del Graph "
            "tab en busca de saturación (un techo plano en el pico) antes de "
            "confiar en los datos exportados."
        ),
    )

    return _scroll_tab(lambert)


def _tab_moments_diagnosis(reactor) -> QScrollArea:
    tau_s = reactor.V_L / (reactor.Q_nominal_L_min / 60.0)

    first = _section(
        "Primer Momento — Tiempo Medio de Residencia",
        _equation(
            "t̄_m = ∫₀^∞ t·E(t) dt   ≈   Σᵢ tᵢ·Cᵢ·Δt / Σᵢ Cᵢ·Δt   (regla trapezoidal)"
        ),
        _narrative(
            "Para un recipiente cerrado en el que todo el volumen participa "
            "del flujo, la teoría establece t̄_m = τ = V/Q, "
            "<b>independientemente</b> de cuán complejo sea el patrón de flujo "
            "interno. Este es el primer y más potente diagnóstico: comparar el "
            "τ calculado desde geometría/caudal contra el t̄_m medido con el "
            "trazador."
        ),
        _equation(
            "t̄_m < τ   →   existe volumen que el flujo no está recorriendo\n"
            "φ_d ≈ 1 − t̄_m / τ        (estimación de la fracción de volumen muerto)"
        ),
        _tip(
            f"τ = V/Q para el reactor bajo CIP en este simulador es "
            f"{tau_s:.0f} s ({tau_s / 60:.2f} min) — el mismo para los tres "
            f"reactores por diseño. Compáralo contra el t̄_m que calcules de "
            f"tu propia curva exportada."
        ),
    )

    second = _section(
        "Segundo Momento — Varianza",
        _equation(
            "σ² = ∫₀^∞ (t − t̄_m)² · E(t) dt        σ_θ² = σ² / t̄_m²"
        ),
        _narrative(
            "La varianza mide el <b>ancho</b> de la distribución, es decir, el "
            "grado de mezclado axial. σ_θ²=0 para el RFP ideal, σ_θ²=1 para "
            "el RTAC ideal."
        ),
        _tip(
            "El segundo momento pondera por (t−t̄_m)² y es extremadamente "
            "sensible a la cola de la distribución — justo donde la señal es "
            "más débil y el ruido relativo es peor. Truncar la cola "
            "demasiado pronto subestima σ² sistemáticamente."
        ),
    )

    signatures = _section(
        "Lectura Cualitativa — Firmas Hidrodinámicas",
        _narrative(
            "Antes de ajustar ningún modelo, la <i>forma</i> de E(t) ya "
            "permite un diagnóstico directo:"
        ),
        _narrative(
            "•  <b>Pico u hombro a t ≪ τ</b> — cortocircuito / canalización: "
            "una fracción del caudal atraviesa con residencia mínima.<br>"
            "•  <b>Cola más lenta que la exponencial de τ</b> — zona de "
            "estancamiento con intercambio lento.<br>"
            "•  <b>Curva bimodal</b> — dos caminos en paralelo con tiempos "
            "muy distintos; canalización severa.<br>"
            "•  <b>t̄_m &lt; τ</b> — volumen muerto (ver arriba).<br>"
            "•  <b>Curva unimodal angosta centrada en τ</b> — comportamiento "
            "cercano a flujo pistón, dispersión moderada."
        ),
    )

    return _scroll_tab(first, second, signatures)


def _tab_one_parameter_models() -> QScrollArea:
    tanks = _section(
        "Modelo de Tanques en Serie",
        _narrative(
            "Representa el equipo real como N RTAC ideales e iguales en "
            "cascada. La varianza adimensional se relaciona directamente con "
            "N, así que el ajuste es explícito — no requiere regresión no "
            "lineal:"
        ),
        _equation("σ_θ² = 1/N        →        N = t̄_m² / σ²"),
        _narrative(
            "N=1 es el RTAC ideal; N→∞ es el RFP ideal. Un lecho fijo en buen "
            "estado presenta N típicamente entre 10 y 30; un valor "
            "anormalmente bajo sugiere mezclado excesivo o patologías."
        ),
    )

    dispersion = _section(
        "Modelo de Dispersión Axial",
        _narrative(
            "Representa el equipo como flujo pistón con un término difusivo "
            "superpuesto que agrupa todos los mecanismos de mezclado axial. "
            "El único parámetro es el número de Péclet:"
        ),
        _equation("Pe = uL / D_ax        (Pe→∞: RFP ideal,  Pe→0: mezcla completa)"),
        _narrative(
            "Para condiciones de recipiente cerrado–cerrado (alimentación y "
            "descarga por tubería, como en este skid), la relación entre "
            "varianza y Péclet es implícita y se resuelve numéricamente:"
        ),
        _equation("σ_θ² = 2/Pe − (2/Pe²)·(1 − e^(−Pe))"),
        _narrative(
            "Para desviaciones pequeñas (σ_θ² ≪ 1) esto se reduce a "
            "σ_θ² ≈ 2/Pe, dando la equivalencia aproximada Pe ≈ 2N — una "
            "verificación interna útil entre ambos ajustes."
        ),
    )

    limits = _section(
        "Límite de los Modelos de Un Parámetro",
        _narrative(
            "Ambos modelos asumen dispersión <b>homogénea</b>, distribuida a "
            "lo largo de todo el equipo. Ninguno contempla flujo en paralelo "
            "ni regiones estancadas."
        ),
        _narrative(
            "Frente a una patología estructural (canalización + zona muerta), "
            "ambos ajustan el ancho global de la distribución pero <b>no "
            "reproducen</b> ni el hombro temprano ni la cola prolongada — la "
            "familia de curvas que generan es unimodal por construcción. "
            "Detectar <i>dónde</i> falla el ajuste y explicar <i>por qué</i> "
            "vale más que el número N o Pe en sí."
        ),
    )

    return _scroll_tab(tanks, dispersion, limits)


def _tab_diagnosis_framework() -> QScrollArea:
    compartments = _section(
        "Más Allá de un Parámetro — Modelos Combinados",
        _narrative(
            "Cuando la no idealidad no es dispersión distribuida sino una "
            "patología localizada, la literatura (Levenspiel; Cholette &amp; "
            "Cloutier) recurre a <b>modelos combinados</b>: representar el "
            "equipo como una red de elementos ideales en serie y en paralelo, "
            "con intercambio entre regiones — típicamente un camino "
            "principal, un canal de bypass (canalización) y una zona muerta "
            "que intercambia lentamente con el camino principal."
        ),
        _narrative(
            "Este simulador implementa internamente una red de ese tipo como "
            "la <b>verdad oculta</b> de cada columna — es, literalmente, lo "
            "que tu ensayo de trazador está tratando de diagnosticar. Sus "
            "parámetros no se muestran en ninguna parte de la interfaz: el "
            "trabajo consiste en inferir la <i>naturaleza</i> del defecto "
            "(¿cortocircuito?, ¿zona muerta?, ¿ambos?) a partir de la forma "
            "de la curva medida, usando las firmas cualitativas y los "
            "modelos de la pestaña anterior — no en recuperar números "
            "exactos que el simulador nunca expone."
        ),
        _tip(
            "Un hombro temprano fija su posición según qué tan rápido es el "
            "canal de bypass, y su amplitud según cuánto caudal se desvía por "
            "él; una cola larga tiene una constante de tiempo asociada al "
            "intercambio con la zona muerta. Son dos efectos independientes "
            "— pueden aparecer juntos, por separado, o ninguno."
        ),
    )

    contamination = _section(
        "Cadena de Contaminación de la Medición",
        _narrative(
            "Un experimento real superpone varias capas de error sobre la "
            "curva E(t) teórica — el simulador las reproduce deliberadamente:"
        ),
        _narrative(
            "•  <b>Ancho finito del pulso</b> — ensanchamiento leve, "
            "despreciable si Δt_p ≪ τ.<br>"
            "•  <b>Muestreo discreto</b> — error de cuadratura en los "
            "momentos.<br>"
            "•  <b>Calibración (ε·b)</b> — error sistemático si la constante "
            "es imprecisa.<br>"
            "•  <b>Ruido del detector</b> — afecta severamente el segundo "
            "momento y la derivación numérica de F.<br>"
            "•  <b>Saturación del rango lineal</b> — distorsiona el pico.<br>"
            "•  <b>Ventana de observación finita</b> — trunca la cola, sesga "
            "t̄_m y σ²."
        ),
        _narrative(
            "Tu trabajo es el camino inverso: remover estas capas hasta "
            "recuperar los momentos y, a partir de ellos, el diagnóstico."
        ),
    )

    sequence = _section(
        "Secuencia de Procesamiento de Datos",
        _narrative(
            "Procedimiento a ejecutar sobre el archivo exportado desde la "
            "pestaña Table:"
        ),
        _narrative(
            "1. <b>Conversión</b> — aplicar A=ε·b·C para obtener C(t); "
            "verificar que el pico no haya saturado.<br>"
            "2. <b>Normalización</b> — integrar ∫C dt y obtener E(t).<br>"
            "3. <b>Verificación de balance</b> — masa recuperada vs. "
            "inyectada.<br>"
            "4. <b>Momentos</b> — t̄_m y σ².<br>"
            "5. <b>Diagnóstico por comparación</b> — t̄_m vs. τ=V/Q.<br>"
            "6. <b>Ajuste de modelos</b> — N por tanques en serie, Pe por "
            "dispersión; verificar Pe≈2N.<br>"
            "7. <b>Contraste modelo–experimento</b> — superponer la curva "
            "del modelo de tanques sobre la E experimental; identificar "
            "dónde discrepan.<br>"
            "8. <b>Verificación cruzada</b> — derivar F del escalón y "
            "comparar con la E del pulso.<br>"
            "9. <b>Lectura de firmas</b> — aplicar la tabla de firmas "
            "cualitativas.<br>"
            "10. <b>Diagnóstico y recomendación</b>."
        ),
        _tip(
            "El fundamento matemático completo — incluyendo la derivación "
            "del modelo de compartimientos y la interpretación del volumen "
            "muerto (§7) — está disponible para el docente en "
            "docs/modules/rtd/fundamentals.md."
        ),
    )

    return _scroll_tab(compartments, contamination, sequence)


# ── RTDDocsTab ──────────────────────────────────────────────────────────────

class RTDDocsTab(QWidget):
    """In-app documentation for the RTD (Experiencia 3) module.

    Structurally mirrors ui/tabs/docs_tab.py's PFR docs (a QTabWidget of
    section-card sub-tabs), sourced from docs/modules/rtd/fundamentals.md. Deliberately
    teaches the general RTD analysis toolkit (moments, one-parameter models,
    the compartment-model *concept*) without exposing this simulator's hidden
    per-reactor parameters -- those stay behind Scenario's visible/oculto
    split (see scenarios/loader.py) no matter how much theory surrounds them.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)

        header = QWidget()
        hlay = QVBoxLayout(header)
        hlay.setContentsMargins(18, 14, 18, 10)
        hlay.setSpacing(4)

        title = QLabel("RTD — Experiencia 3: Flujo No Ideal")
        title.setStyleSheet("color:#E95420;font-size:18px;font-weight:bold;")
        hlay.addWidget(title)

        subtitle = QLabel(
            "Ensayo de trazador estímulo-respuesta sobre un lecho fijo con "
            "patologías hidrodinámicas ocultas."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color:#adadad;font-size:12px;")
        hlay.addWidget(subtitle)
        vlay.addWidget(header)

        scenario = load_scenario(RTD_DEFAULT_SCENARIO)
        reactor = scenario.visible.reactor
        sensor = load_sensor()
        tau_s = reactor.V_L / (reactor.Q_nominal_L_min / 60.0)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #1e2a35;
            }
            QTabBar::tab {
                background: #262626;
                color: #adadad;
                padding: 6px 16px;
                font-size: 12px;
                border: none;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected {
                color: #E95420;
                border-bottom: 2px solid #E95420;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                color: #eeeeec;
            }
        """)

        tabs.addTab(_tab_user_guide(),                        "User Guide")
        tabs.addTab(_tab_fundamentals(),                       "Fundamentos")
        tabs.addTab(_tab_stimulus_response(tau_s),             "Estímulo–Respuesta")
        tabs.addTab(_tab_measurement(sensor),                  "Medición")
        tabs.addTab(_tab_moments_diagnosis(reactor),           "Momentos y Diagnóstico")
        tabs.addTab(_tab_one_parameter_models(),               "Modelos de Un Parámetro")
        tabs.addTab(_tab_diagnosis_framework(),                "Compartimientos y Datos")

        vlay.addWidget(tabs)
