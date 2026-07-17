# PLAN.md — Módulo RTD: simulador de flujo no ideal (Experiencia 3)

> Documento de planificación para implementación asistida con Claude Code.
> Se apoya en la base existente del repositorio `scada-pfr-simulator`.
> Estado: propuesta inicial, pendiente de refinamiento contra el contexto del proyecto.

---

## 1. Objetivo

Extender el simulador SCADA existente con un **segundo escenario de laboratorio**: un ensayo de
trazador (estímulo–respuesta) sobre un lecho fijo con patologías hidrodinámicas ocultas, destinado
a la Experiencia 3 del curso de reactores (flujo no ideal, distribución de tiempos de residencia).

El estudiante debe poder:

1. Operar una columna empacada virtual (caudal ajustable).
2. Inyectar trazador en modo **pulso** o **escalón**.
3. Registrar la respuesta de un fotocolorímetro en línea (absorbancia vs. tiempo).
4. Exportar la serie temporal y el registro de eventos a CSV/Excel.
5. Reconstruir E(t), momentos, y ajustar los modelos de tanques en serie y de dispersión.
6. Diagnosticar la patología del equipo y emitir un informe de diagnóstico.

**No objetivo:** este módulo no simula reacción química ni balance de energía. El trazador es inerte
y el sistema es isotérmico. Toda la complejidad está en la hidrodinámica.

## 2. Restricción de diseño rectora

El motor MOL + upwind de primer orden usado para el PFR **no debe reutilizarse para este módulo**.
La difusión numérica del esquema upwind introduce una dispersión artificial del mismo orden de
magnitud que el fenómeno físico a medir, lo que impediría controlar el Péclet efectivo del escenario.

En su lugar, la verdad oculta se modela como una **red de compartimientos de mezcla perfecta**
(modelo combinado de Levenspiel): sistema de ODEs lineales, sin discretización espacial, sin
difusión numérica por construcción. Ver `FUNDAMENTS_EXP3.md` para la derivación completa.

## 3. Reuso de la base existente

| Componente | Acción |
|---|---|
| Backend FastAPI + uvicorn | Reusar sin cambios estructurales |
| Loop de integración segmentada | Reusar; el cambio de condición de borde ahora es la inyección de trazador |
| Clases de sensores y actuadores | Reusar; extender sensor con curva de calibración |
| Registro de eventos | Reusar; agregar eventos de inyección y costo |
| Pestaña de gráfico (Plotly.js) | Reusar; cambiar variables seleccionables |
| Pestaña de tabla + export CSV/Excel | Reusar sin cambios |
| Empaquetado PyInstaller | Reusar sin cambios |
| P&ID (SVG + overlay HTML) | **Nuevo** SVG; misma técnica de overlay |
| Motor de reacción (PFR/MOL) | **No se toca**; convive como escenario separado |

Se mantiene el principio de **lógica de paso propiedad de la unidad**: la clase del lecho es dueña de
su método de integración, independiente del PFR.

## 4. Modelo matemático (verdad oculta)

Red de compartimientos:

- **Camino principal**: cascada de `N_m` CSTRs, recibe `(1 − f)·Q`, ocupa `V·(1 − φ_d − φ_c)`.
- **Canal (bypass)**: cascada de `N_c` CSTRs, recibe `f·Q`, ocupa `V·φ_c` con **`φ_c = γ·f`**.
- **Zona muerta**: volumen `V·φ_d`, sin flujo neto, intercambia con el tanque `j` del camino
  principal a caudal `q_ex = k_ex · V_d`.
- **Salida**: mezcla en base a caudales, `C_out = f·C_Nc^c + (1 − f)·C_Nm`.

Vector de estado: `[C_1..C_Nm, C_1^c..C_Nc^c, C_d]` → dimensión `N_m + N_c + 1` (≈ 15).

Sistema **lineal y no rígido**. `RK45` es suficiente; `Radau` es aceptable por consistencia con el
resto del proyecto y no penaliza a esta escala.

Ecuaciones y unidades: ver `FUNDAMENTS_EXP3.md`, sección 5.

## 5. Arquitectura de módulos

```
src/
  models/
    packed_bed_rtd.py     # Clase PackedBedRTD: red de compartimientos, dueña de su integrador
  sensors/
    photocolorimeter.py   # Muestreo, Lambert-Beer, ruido, saturación de rango lineal
  scenarios/
    loader.py             # Carga y validación de escenarios JSON
    plants/
      planta_a.json
      planta_b.json
      planta_c.json
  api/
    rtd_routes.py         # Endpoints del escenario RTD
  economics/
    cost_tracker.py       # Costo por ensayo
static/
  pid_packed_bed.svg      # P&ID ISA 5.1 de la columna
  rtd.html / rtd.js       # Vista del escenario
```

### 5.1 `PackedBedRTD`

Responsabilidades:

- Construir la matriz del sistema a partir de `(f, φ_d, k_ex, γ, N_m, N_c, V, Q)`.
- Mantener el estado interno entre segmentos.
- `step(dt, c_in)`: integrar un segmento preservando el perfil interno; solo cambia la condición de borde.
- `set_flow(Q)`: recalcular caudales conservando el estado (integración segmentada).
- `outlet_concentration()`: devolver `C_out` exacta (uso interno; **no se expone al frontend**).

Notas de implementación:

- La inyección pulso es un **pulso rectangular de ancho finito** (`t_pulse` ≈ 1–2 s), no una delta
  ideal. Es lo físicamente honesto y, con `t_pulse ≪ τ`, indistinguible de la delta en la curva E.
- La zona muerta se acopla a un tanque intermedio `j` (p. ej. `j = N_m // 2`), no al primero ni al
  último, para que la cola no dependa de un artefacto de borde.
- Si `φ_d = 0`, el estado `C_d` se desacopla; manejar el caso sin división por cero. Ídem para el
  canal cuando `f = 0` (entonces `V_c = 0`).
- **`φ_c` no es un parámetro independiente: `φ_c = γ·f`.** Fijar `φ_c` constante introduce un defecto
  real: al anular el bypass (`f = 0`) el volumen del canal queda sin caudal y se convierte en una
  segunda zona muerta no declarada, de modo que el escenario "lecho sano" arroja `t̄_m < τ` sin que
  exista zona muerta. Con la proporcionalidad, `τ_c = γ·τ` y los roles quedan separados: `f` es
  cuánto caudal se desvía, `γ` es qué tan rápido es el canal. Ver `FUNDAMENTS_EXP3.md`, §5.5–5.6.

### 5.2 `Photocolorimeter`

Es la **frontera entre la verdad y el dato**. El motor conoce `C_out(t)` continua y exacta; el
estudiante solo ve lo que cruza esta capa:

1. Muestreo a período fijo (`dt_sample` ≈ 2–5 s).
2. Conversión Lambert-Beer: `A = ε·b·C`.
3. Ruido gaussiano aditivo con semilla del escenario (**reproducible** para efectos de calificación).
4. Saturación sobre el límite del rango lineal (`A_max`), si está habilitada.

Ningún endpoint debe filtrar concentraciones verdaderas ni parámetros ocultos. Verificar esto en los
tests: es el requisito de integridad más importante del módulo.

### 5.3 Escenario JSON

```json
{
  "id": "planta_a",
  "nombre": "Columna R-201, Línea A",
  "visible": {
    "V_L": 2.0,
    "Q_nominal_mL_s": 20.0,
    "epsilon_b": 0.85,
    "A_max": 1.2,
    "dt_sample_s": 2.0
  },
  "oculto": {
    "f": 0.15,
    "phi_d": 0.15,
    "k_ex_s": 0.002,
    "gamma": 0.30,
    "N_m": 12,
    "N_c": 2,
    "seed": 20260714
  },
  "costos": {
    "pulso": 12000,
    "escalon": 35000,
    "hora_planta": 8000,
    "presupuesto": 120000
  }
}
```

Los bloques `visible` y `oculto` deben estar **separados a nivel de esquema**, no solo por
convención, para que sea estructuralmente difícil filtrar el segundo.

### 5.4 API

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/rtd/start` | Inicia escenario, carga JSON, estado a cero |
| `POST` | `/rtd/flow` | Cambia `Q` (preserva estado interno) |
| `POST` | `/rtd/inject/pulse` | Inyecta pulso de dosis `m` |
| `POST` | `/rtd/inject/step` | Abre/cierra válvula de trazador (`C_0` constante) |
| `GET` | `/rtd/state` | Estado actual: `t`, `Q`, `A` medida, costo acumulado |
| `GET` | `/rtd/buffer` | Serie de mediciones desde `t_since` |
| `GET` | `/rtd/events` | Registro de eventos |
| `GET` | `/rtd/export` | CSV con timestamps, `A`, `Q`, eventos |

### 5.5 P&ID (SVG, ISA 5.1)

Elementos mínimos:

- Columna empacada vertical con relleno indicado.
- Alimentación de agua con `FIC`/`FIT` (caudal editable).
- Punto de inyección de trazador en la entrada: jeringa (pulso) y válvula de tres vías (escalón).
- `AIT` (analizador en línea, fotocolorímetro) en la salida.
- Descarga a drenaje.

Controles overlay: caudal (numérico), dosis de pulso (numérico), botón *Inyectar pulso*, switch de
escalón, lectura de absorbancia, costo acumulado / presupuesto.

### 5.6 Costo por ensayo

Cada acción incrementa un contador visible: pulso, escalón (mayor, consume más trazador) y tiempo de
planta. El costo acumulado se registra en el log de eventos y viaja al CSV, de modo que el informe
deba justificar el gasto. Al superar el presupuesto: advertencia, no bloqueo.

## 6. Fases de implementación

| Fase | Entregable | Criterio de término |
|---|---|---|
| 1 | `PackedBedRTD` + tests | Conservación de masa y momentos verificados (ver §7) |
| 2 | `Photocolorimeter` + escenarios JSON | Ruido reproducible por semilla; sin fuga de parámetros ocultos |
| 3 | Endpoints `/rtd/*` sobre el loop segmentado | Pulso y escalón operables vía API |
| 4 | P&ID SVG + overlay + vista | Ensayo completo operable desde el navegador |
| 5 | Contador de costos + export CSV | CSV contiene serie, eventos y costos |
| 6 | Calibración de escenarios | Firmas visibles pero no triviales (ver §8) |

## 7. Validación numérica (obligatoria, fase 1)

Tests que deben pasar antes de conectar cualquier interfaz:

1. **Conservación de trazador**: `∫ Q·C_out dt = m_inyectada` con tolerancia < 1 % integrando a
   `t → 10·τ`.
2. **Normalización**: `∫ E dt = 1` con la misma ventana.
3. **Primer momento sin patología**: con `f = 0`, `φ_d = 0` → `t̄_m = τ + Δt_p/2` dentro de 1 %.
   (El desplazamiento `Δt_p/2` proviene del ancho finito del pulso y es correcto, no un error.)
   **Este test detecta el defecto de `φ_c` constante descrito en §5.1.**
4. **Primer momento con zona muerta e integración completa**: con `k_ex > 0` y ventana larga
   (`10·τ`) → `t̄_m → τ`. Este test documenta que el "volumen muerto" medido es un **artefacto de
   truncamiento** de la ventana de observación, no una propiedad del modelo (ver
   `FUNDAMENTS_EXP3.md`, §7).
5. **Varianza sin patología**: con `f = 0`, `φ_d = 0` → `σ² ≈ τ²/N_m` dentro de 2 %. Nótese que
   `σ_θ² = σ²/t̄_m²` difiere de `1/N_m` en ~2 % por el desplazamiento del pulso; comparar contra `σ²`
   evita el falso negativo.
5b. **Reparto de volumen**: con `k_ex = 0` y ventana larga → `t̄_m = V(1−φ_d)/Q + Δt_p/2` para
   cualquier `f` y `γ` (ecuación 33 de `FUNDAMENTS_EXP3.md`). Es el test más sensible a errores en el
   reparto de volúmenes.
6. **Consistencia pulso–escalón**: la integral acumulada de la respuesta al pulso reproduce la
   respuesta al escalón normalizada, dentro del error de muestreo.
7. **Independencia de la integración segmentada**: un ensayo ejecutado en un solo segmento y el mismo
   ensayo interrumpido por un cambio de `Q` y vuelto al valor original deben coincidir mientras la
   condición de borde no cambie.

## 8. Calibración de escenarios (fase 6)

Rangos sugeridos como punto de partida, a ajustar con evidencia:

| Parámetro | Rango útil | Comentario |
|---|---|---|
| `f` | 0.10 – 0.25 | `f > 0.35` da curva bimodal de manual (trivial); `f < 0.08` es indetectable con ruido |
| `φ_d` | 0.10 – 0.25 | Se lee como `1 − t̄_m/τ` bajo ventana finita |
| `k_ex` | 0.001 – 0.005 s⁻¹ | Con `τ = 100 s`: cola de 5–10 `τ`. Mayor → la zona muerta se confunde con el camino principal |
| `N_m` | 10 – 15 | Lecho "sano" |
| `γ` | 0.25 – 0.40 | Fija la **posición** del hombro: `τ_c = γ·τ`. La **amplitud** la fija `f` |

Definir 3–4 plantas con dificultad graduada y patología dominante distinta (una canalización franca,
una zona muerta franca, una combinada) — mecanismo anti-copia equivalente al de la Experiencia 2.

Criterio de aceptación: la curva debe mostrar la firma **sin ser obvia**. Inspección visual de cada
escenario antes de liberarlo.

## 9. Decisiones abiertas

- **Escala temporal**: para que 3–5 ensayos quepan en una sesión de 2 h, `τ` debe ser de 2–4 min de
  tiempo real, o bien correr con factor de aceleración configurable. Decidir cuál.
- **Cambio de `Q` durante un ensayo**: el motor lo maneja correctamente, pero contamina el análisis
  del estudiante. Propuesta: permitirlo y dejar que el registro de eventos lo evidencie.
- **Índice `j` de acoplamiento de la zona muerta**: ¿fijo o parámetro del escenario?
- **Saturación del rango lineal**: ¿habilitada por defecto? Obliga a diseñar la dosis, pero agrega
  un modo de falla que puede frustrar sin aportar al objetivo central.

## 10. Referencias internas

- `FUNDAMENTS_EXP3.md` — fundamento matemático, nomenclatura y unidades.
- `curva_E_explicativo.html` — explicador interactivo para la sesión 1.
- Repositorio base: `scada-pfr-simulator`.
