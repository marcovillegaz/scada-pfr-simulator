# Mejoras propuestas a ChemEng SimLab (módulo PFR) — para revisar

> **Fecha:** 2026-10-29 (para revisión el 2026-10-30) · **Origen:** redacción de las guías de la Exp 2 (curso Lab de Cinética de Reactores, PL06/PL07).
> **Alcance:** todo lo que surgió al leer el código con ojos de estudiante y de docente. **No se modificó ningún archivo de la app.** Lo bloqueante está en [`HOTFIX_2.0.1.md`](HOTFIX_2.0.1.md).
> **Prioridad:** 🔴 bloquea la entrega a estudiantes · 🟠 recomendada para 2026-2 · 🟡 mejora para 2027-1.

## Resumen

| # | Prioridad | Tema | Dónde |
|---|---|---|---|
| 1 | 🔴 | La exportación CSV/Excel incluye variables internas (`CA_out`, `CB_out`, `X_out`…) | `table_tab.py`, `data_store.py` |
| 2 | 🔴 | Textos de conductividad contradicen el modelo (σ "sube" con la conversión) | `sensor_dialog.py`, `docs_tab.py` |
| 3 | 🔴 | La pestaña Docs imprime los valores reales de A y B | `docs_tab.py` 291–295 |
| 4 | 🟠 | El registro de eventos no se exporta y RESET lo borra | `table_tab.py`, `event_log_panel.py` |
| 5 | 🟠 | El diálogo R-101 muestra el volumen del reactor | `reactor_dialog.py` 42 |
| 6 | 🟠 | Limitación estructural del PID: ¿se puede sintonizar de verdad? | `pfr_engine.py`, `fundamentals.md` §10 |
| 7 | 🟠 | El sensor no satura en su rango declarado (0–20 mS/cm) | `conductivity.py` |
| 8 | 🟠 | `T_setpoint` no está en las columnas de estudiante | `log_table_model.py` |
| 9 | 🟠 | Errores numéricos en `docs/modules/pfr/fundamentals.md` | docs |
| 10 | 🟡 | Otros textos inexactos en la app | varios |
| 11 | 🟡 | Idioma: Docs en inglés (PFR) frente a español (RTD) | `docs_tab.py` |
| 12 | 🟡 | Versiones y coherencia del repo | `pyproject.toml`, `constants.py` |
| 13 | 🟡 | Ayudas opcionales (reset a valores por defecto, plantilla de calibración) | UI |

---

## 1. 🔴 Exportación con variables internas

**Qué pasa.** `TableTab.update_on_stop` guarda `data_store.to_dataframe()`, que exporta **todos los campos escalares** de `EngineSnapshot`: `CA_out`, `CB_out`, `X_out`, `velocity`, `Q_in`, `T_setpoint`. La tabla en pantalla solo muestra `STUDENT_COLUMNS`, pero **Export CSV/Excel escribe el DataFrame completo**.

**Efecto en el curso.** El estudiante puede leer `CA_out` y `X_out` verdaderos (sin ruido) y saltarse la calibración (E2-P1) y la inferencia de concentración. Rompe el diseño de la experiencia.

**Propuesta.** Exportar solo las columnas de `STUDENT_COLUMNS`, con los mismos encabezados y escalas que la tabla. Dejar el DataFrame completo para la exportación de la pestaña Admin. Agregar un test que verifique que el CSV de estudiante no contiene `Ca_out`, `Cb_out` ni `Xa_out`.

## 2. 🔴 Textos de conductividad

Ver `HOTFIX_2.0.1.md` §1–2. El código usa σ = 156·C_A + 1,6 con C_A = NaOH residual: σ **baja** al avanzar la reacción. Los textos dicen lo contrario y los consejos también.

## 3. 🔴 Valores de A y B visibles

`docs_tab.py` (291–295) imprime `A = 156` y `B = 1.6` (mS/cm). La guía pide que el estudiante **construya** la calibración. Propuesta: ocultar A y B (como ya hace `sensor_dialog.py` con "factory-calibrated") y no mostrar `CT101_NOISE_STD` (0,05 mS/cm). Alternativa: mostrarlos como "valores nominales del fabricante" para que el estudiante compare. Decisión de Marco.

**Observación para los Fundamentos.** A = 156 es casi igual a λ(OH⁻) − λ(CH₃COO⁻) ≈ 198 − 41 = 157 mS/cm por mol/L: el modelo representa la **mezcla en reacción** (Na⁺ espectador). Un patrón de NaOH puro en agua tendría pendiente cercana a λ(Na⁺) + λ(OH⁻) ≈ 248. En el simulador esa diferencia no aparece (modelo único); los Fundamentos la declaran como limitación. Si en 2027-1 se quiere que la calibración "con NaOH solo" salga sesgada a propósito (v3, E2-P1), este es el punto de partida.

## 4. 🟠 Registro de eventos no exportable

Las guías piden segmentar las series "con el registro de eventos". Hoy ese registro vive solo en la barra lateral, **no se exporta** y **RESET lo borra**. Propuesta:
- Exportarlo como segunda hoja del Excel (y como un segundo CSV `*_events.csv`), con `Time (s)`, texto y nivel.
- O, mínimo, agregar una columna `event` en la tabla exportada con el texto del evento en la fila en que ocurre.
- Registrar también los cambios de ganancias del PID (hoy `add_event` se llama desde `pfr_workspace.py` para parámetros de alimentación y setpoint; verificar que el diálogo PID también deja evento).

Mientras no exista, la guía indica copiar las marcas a mano.

## 5. 🟠 El diálogo R-101 muestra el volumen

`reactor_dialog.py` línea 42: `("Volume", f"{V * 1e6:.2f} mL …")` entrega 410,37 mL. La decisión de diseño es que **el estudiante calcule el volumen** desde L y D. Opciones:
- (a) Dejar la fila: el estudiante calcula y **verifica** contra el diálogo (la guía lo permite hoy, porque L y D están ahí). Es lo más simple.
- (b) Quitar la fila "Volume" y dejar L, D y sección.
Recomendación: (a), y que el CE pida el cálculo con otra geometría (así está en PL07).

## 6. 🟠 PID: la limitación estructural frente al objetivo E2-P3

`docs/modules/pfr/fundamentals.md` §10 afirma que la variable controlada es `T_reactor = (T_in + T_out)/2`, que el tiempo muerto de ~120 s produce un sobreimpulso de 5–7 °C y que **no se reduce retocando Kp** (constante en un rango de 12× de Kp).

**Problema para el curso.** E2-P3 pide "sintonizar el PID y justificar el criterio de ajuste". Si el sobreimpulso no depende de la ganancia, la actividad pierde sentido o, peor, el estudiante concluye que "el PID no importa". Antes de cerrar la guía de la Exp 2 conviene **ejecutar el simulador y medir** sobreimpulso, tiempo de estabilización y offset para un barrido de (Kp, Ki, Kd) con un escalón 25 → 35 °C.

Posibles salidas, según lo que muestre el barrido:
1. Si hay un efecto real de Ki o de Kp bajos (p. ej., menos oscilación al bajar la ganancia), la actividad funciona: solo hay que redactar la guía para que el estudiante lo encuentre (hoy la guía no promete que se elimine el sobreimpulso).
2. Si no hay efecto: reformular E2-P3 como "diagnosticar por qué la sintonía no basta" (tiempo muerto), con un criterio de comparación claro.
3. Si se quiere sintonía efectiva: agregar un segundo lazo o permitir controlar `T_in` (cambio de modelo, versión mayor).

Pendiente de Marco: correr el barrido y decidir.

## 7. 🟠 El sensor no satura en su rango

`sensor_dialog.py` declara "Range 0–20 mS/cm" y "Valid range 0–0.1 mol/L", pero `ConductivitySensor.measure` solo hace `max(0, σ + ruido)`: no hay techo. Con A = 156 y B = 1,6, el techo de 20 mS/cm corresponde a C_A ≈ 0,118 mol/L. Propuestas:
- Saturar la lectura en el rango declarado (para que "rango" sea una propiedad que el estudiante descubra, E2-P1).
- Opcional (🟡): agregar una leve no linealidad por encima de 0,1 mol/L, para que "extrapolar" tenga consecuencias.
Efecto en tests: `test_sensors.py` usa parámetros por defecto del constructor; habría que agregar un parámetro `range_max`.

## 8. 🟠 `T_setpoint` fuera de las columnas de estudiante

`STUDENT_COLUMNS` no incluye `T_setpoint`, que es una **entrada del operador** (no un dato oculto). Para segmentar por cambio de setpoint, el estudiante hoy tiene que deducirlo de la respuesta de `T_in`. Propuesta: agregarlo a `STUDENT_COLUMNS` (y a la exportación). También conviene exportar temperaturas en °C además de K, o al menos advertirlo en el encabezado (la guía ya lo advierte).

## 9. 🟠 Errores en `docs/modules/pfr/fundamentals.md`

Verificados en Python con los parámetros de `pfr_default.json`:

| Línea | Dice | Valor correcto |
|---|---|---|
| §11, `Qa0`, `Qb0` | 1,667×10⁻⁶ m³/s "(0.1 mL/s)" | 1,667×10⁻⁶ m³/s = **1,667 mL/s = 100 mL/min** |
| §8 | "u ≈ 0.02 m/s" | u = Q/A_c = 3,333×10⁻⁶ / 1,963×10⁻⁵ = **0,170 m/s** |
| §8 | "CFL ≈ 0.024" | CFL = u·Δt/Δz = 0,170 · 0,5 / 0,418 = **0,20** (sigue ≪ 1 en la práctica de RK45 adaptativo, pero el número es otro) |
| §10 | "tiempo muerto ~120 s" | coincide con τ = L/u = **123 s** ✔ |

## 10. 🟡 Otros textos inexactos

- `reactor_dialog.py` 49: "Rate law: rA = k(T) · CA_in · CB_in". Debe ser `CA · CB` (concentraciones locales, no de entrada).
- `docs_tab.py` 188–190 (consejo): "Raise T_setpoint… observe the increase in Xa on the Graph tab". La pestaña Graph **no muestra Xa** (está oculto a propósito). Reemplazar por "observe how the outlet conductivity changes".
- `docs_tab.py` 56: consejo sobre velocidad `u`; el estudiante no ve `u` (oculto). Verificar.
- Rotulado de tanques: los comentarios del motor dicen **TK-101 (NaOH)** y **TK-102 (EtAc)**; la guía usa esos rótulos. Confirmar que el P&ID de `images/` los muestra igual (el borrador de PL06 mencionaba TK-102/TK-103).
- `hx_dialog.py`: describe dos intercambiadores (E-101/E-102) pero el motor usa un nodo agrupado; ya lo aclara el texto. Revisar que el P&ID dibuje lo mismo.

## 11. 🟡 Idioma de la documentación en la app

El módulo RTD tiene la documentación en español; el PFR, en inglés. La cohorte es hispanohablante. Propuesta: traducir `docs_tab.py` (PFR) o hacer el idioma configurable. Afecta a la guía (que cita nombres de pestañas en inglés: Diagram, Graph, Table, Docs).

## 12. 🟡 Versiones y coherencia del repo

- `pyproject.toml` dice `version = "1.0.0"`; `constants.py` dice `APP_VERSION = "2.0.0"`. Alinear.
- El `README`/`CHANGELOG` deberían registrar el hotfix 2.0.1 y la política de exportación de estudiante.
- Agregar un test de humo que cargue `pfr_default.json` y verifique que el **estudiante no ve** `k0`, `Ea`, `A`, `B` en `docs_tab` (según decisión del punto 3).

## 13. 🟡 Ayudas opcionales (a decidir; algunas reducen el aprendizaje)

- **Botón "Reset to defaults"** para parámetros (no solo RESET de la corrida): útil para volver al punto de partida entre fases.
- **Plantilla de planilla** (CSV vacío con encabezados) para la calibración: ayuda, pero la guía quiere que el estudiante decida la estructura.
- **Indicador de estado estacionario** en la UI: **no recomendado**, porque quita E2-P2 (segmentar).
- **Seed de ruido por grupo** (para que los dos grupos tengan registros de ruido distintos): ayuda a detectar copia entre grupos, no es urgente.
