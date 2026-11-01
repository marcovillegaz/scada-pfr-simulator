# ROADMAP — ChemEng SimLab v3

> **Estado:** aprobado (2026-10-31) · **Fecha:** 2026-10-29 · **Reemplaza a:** `ROADMAP_V2.md` (eliminado; sus 3 ítems pasan al [Backlog](#backlog)). Es el único roadmap del proyecto.
> **Rama de trabajo:** `v3` (a crear en F0.2) · **Meta:** v3.0.0 lista para la cohorte 2027-1

Cada fase es un plan ejecutable en Claude Code:

1. Entrar en plan mode y leer la sección de la fase.
2. Proponer el plan detallado tarea por tarea, respetando al agente dueño.
3. Ejecutar el ciclo de agentes para cada tarea (ver [Harness](#harness)).
4. Cerrar la fase solo cuando se cumplan **todos** sus criterios de salida.
5. Registrar el cierre en `CHANGELOG.md` y marcar las tareas aquí.

**Formato de tarea:** `ID · agente · descripción → hecho cuando`. Las tareas marcadas 👤 las ejecuta Marco.

---

## Contexto

El simulador v2.0.0 modela un PFR de banco (saponificación NaOH + EtAc) y un experimento RTD. La v3 lo
reencuadra como una **planta realista** siguiendo la lógica del caso BIOVALDÉS de la MC1 (empresa
ficticia, escala real, tags ISA, memorando, falla sembrada, tabla "real vs. simplificado").

**Caso de planta: EPIVALDÉS S.A.** (ficticia), filial de BIOVALDÉS en el Biobío. Produce epiclorhidrina
(ECH) desde la glicerina del biodiésel, 10 kt/año (escala análoga a la primera planta Epicerol de
Solvay en Tavaux). El PFR del simulador es el **prerreactor tubular R-200**:

> 2,3-diclorohidrina (DCH) + OH⁻ → ECH + Cl⁻ + H₂O, 2º orden. Sun, Xia y Xiang, *Chem. Eng. Trans.* 61 (2017):
> k₁ = 9,17·10¹² · exp(−76 150 / RT) L·mol⁻¹·min⁻¹. Fuente única: la engineer la audita antes de usarla (F3.1).

La reacción consecutiva ECH + OH⁻ → hidrólisis **queda fuera de la v3** y se documenta como módulo futuro.

**Principios**

- La física vive solo en `reactor_simulation/`. `scada_app/` compone y muestra.
- Los parámetros viven en `scenarios/*.json` con bloque `visible` / `oculto`. Solo el loader lee `oculto`.
- La UI lee el **escenario activo**, nunca `constants.py`, para valores físicos.
- Todo número nuevo (caudal, volumen, UA, k, λ) sale de un cálculo en Python (oráculo + test), revisado por `engineer`.
- Documentación en español; identificadores de código en inglés, como hoy.
- Cada simplificación se declara (tabla "real vs. simplificado").

## Estado de partida (hallazgos del 2026-10-29)

| Hallazgo | Dónde |
|---|---|
| Release 2.0.0 **sin commitear**; rama `exp3` 21 commits sobre `main`, sin upstream | git |
| No hay `CLAUDE.md`, agentes ni tests de UI | repo |
| `constants.py` carga `pfr_default` al importarse y la UI lee esas constantes, no el escenario activo | `scada_app/constants.py` |
| `PFREngine.set_scenario()` solo llama `reset()`; no reconstruye HX, PID ni sensores | `engine/pfr_engine.py` |
| `_ML_MIN` y unidades mL/min repetidas en 6 archivos; ejes, rangos y alarmas fijos | `ui/`, `workspaces/` |
| Alarmas absolutas (20/40 °C, X 0,20) y arranques fijos pensados para τ ≈ 2 min | `event_log_panel.py` |
| P&ID: SVG con el texto convertido a trazos; hitboxes en coordenadas normalizadas | `images/pfr/diagram.svg` |
| CSV/Excel exportan `to_dataframe()` (SI, campos internos); la tabla muestra otra cosa | `table_tab.py` |
| Conductividad: σ = a·C_NaOH + b (sin acetato ni T); los textos de la app dicen lo contrario | `sensor_dialog.py`, `docs_tab.py` |
| ΔHr soportado por el modelo pero vale 0 en el escenario | `pfr_default.json` |
| Contraseña de Admin `"12345"` en el código y en la documentación | `pfr_workspace.py` |
| El PFR no tiene bloque `oculto`; los dataclasses `**dict` rechazan claves nuevas | `scenarios/loader.py` |
| `sys.path.insert` en loader, engines y conftest, contra `CONVENTION.md` §4 | varios |
| `run_log` sin límite y con perfiles en cada tick | `data_store.py` |

**Patrón a reutilizar:** el módulo RTD. `scenarios/plants/planta_*.json` con `visible` / `oculto`;
`build_rtd_model()` como único lector de `oculto`; `RTDEngine.set_scenario()` → `reset()` →
`_init_objects()`; `tests/test_rtd_scenario_integrity.py` parametrizado.

---

## Harness

Cinco agentes en `.claude/agents/`. Ninguno llama a otros agentes: orquesta la sesión principal.
Cada uno parte sin contexto: lee `CLAUDE.md`, su sección de este ROADMAP y los handoffs relevantes de
`docs/handoffs/`, y al terminar escribe `docs/handoffs/<ID-tarea>-<agente>.md` (qué hizo / qué cambió / qué queda abierto).

| Agente | Alcance de escritura | No hace |
|---|---|---|
| `backend-dev` | `reactor_simulation/`, `scada_app/engine/`, `scada_app/scenarios/`, `tests/` (escribe también los tests: no hay `tester`) | UI ni imágenes |
| `frontend-dev` | `scada_app/ui/`, `scada_app/workspaces/`, `styles.py`, `images/`, textos de las docs dentro de la app | Física, engines ni loader |
| `engineer` | **Solo lectura.** Especifica cada cambio de modelo antes y lo audita después; emite veredicto (aprobado / con observaciones / rechazado); verifica con el `.venv` | Editar archivos |
| `writer` | `docs/`, `CHANGELOG.md`, marcas de este ROADMAP, ADRs, notas de diseño | Código |
| `cartographer` | `graphify-out/` y sus handoffs. Administra el grafo: lo consulta, entrega a los demás agentes un mapa de impacto filtrado y lo actualiza (`graphify update .`) | Código y docs |

**Ciclo por tarea:** `cartographer` (mapa de impacto) → `engineer` (especificación, si toca el modelo) →
`backend-dev` y/o `frontend-dev` → `engineer` (auditoría) → `cartographer` (`graphify update .` + reglas) → `writer`.

**Reglas que verifica el `cartographer` después de cada tarea:**

1. La física no vive en `scada_app/`.
2. Solo `scenarios/loader.py` lee `oculto`.
3. Sin `sys.path.insert` (tras F1.9).
4. La UI no importa constantes físicas de `constants.py` (tras F1.1).

**Verificación común antes de entregar:**

```powershell
.venv\Scripts\python.exe -m pytest
```

---

## Fase 0 — Release v2 y harness

**Objetivo:** partir de una base limpia y probar que un cambio trivial recorre el ciclo completo de agentes.

- [ ] **F0.1** · 👤 · Commitear el 2.0.0, etiquetar `v2.0.0`, integrar `exp3` en `main` y hacer push
      → `git status` limpio; `main` contiene el 2.0.0.
- [ ] **F0.1b** · frontend-dev + backend-dev · Hotfix 2.0.1 sobre `main` (ver [HOTFIX_2.0.1.md](HOTFIX_2.0.1.md)): export con solo `STUDENT_COLUMNS`, textos de conductividad corregidos, test del export; etiquetar `v2.0.1` y hacer push
      → el CSV/Excel no contiene `CA_out`, `CB_out` ni `X_out`; `main` contiene el 2.0.1.
- [ ] **F0.2** · 👤 · Crear la rama `v3` desde `main` (ya con el 2.0.1) → `git branch` la muestra y es la rama activa.
- [ ] **F0.3** · writer · `CLAUDE.md` del repo: stack, capas, comandos (pytest, build PyInstaller), reglas del harness
      → un agente nuevo puede orientarse leyéndolo.
- [ ] **F0.4** · writer · Definir los 5 agentes en `.claude/agents/` y `docs/handoffs/_plantilla.md`
      → los 5 aparecen en `/agents`.
- [ ] **F0.5** · backend-dev · Línea base: pytest en verde y test de regresión de conversión estacionaria
      (≈ 31 / 60 / 72 % a 20 / 40 / 50 °C, valores del README) → el test existe y pasa.
- [ ] **F0.6** · todos · Un cambio trivial (p. ej. corregir el comentario obsoleto "25 °C" de `status_card.py`) recorre el ciclo completo
      → handoffs de los 5 agentes en `docs/handoffs/`.

**Salida:** F0.1–F0.6 hechas.

## Fase 1 — Deuda que bloquea escenarios

**Objetivo:** que un escenario nuevo (otra escala, otras especies) funcione sin tocar la UI.

- [ ] **F1.1** · backend-dev + frontend-dev · La UI, los diálogos y el diagrama reciben el objeto escenario (como RTD) y dejan de leer constantes físicas
      → `constants.py` solo conserva identidad, timers y geometría de la escena.
- [ ] **F1.2** · backend-dev · `PFREngine.set_scenario()` reconstruye HX, PID y sensores (`reset()` → `_init_objects()`)
      → test que cambia de escenario y comprueba UA, ganancias y calibración nuevos.
- [ ] **F1.3** · backend-dev · Bloque `oculto` en el PFR, `build_pfr_model()` como único lector y test de integridad parametrizado (réplica de `test_rtd_scenario_integrity.py`)
      → el test pasa con ≥ 2 escenarios.
- [ ] **F1.4** · backend-dev · Módulo de unidades (caudal, concentración, temperatura de visualización) definido por escenario; elimina los 6 `_ML_MIN`
      → `grep _ML_MIN` sin resultados.
- [ ] **F1.5** · backend-dev + frontend-dev · Exportación CSV/Excel con las columnas y unidades que ve el estudiante; sin `X_out`, `CA_out` ni `CB_out`
      → test sobre las columnas exportadas.
- [ ] **F1.6** · frontend-dev · Ejes, rangos de los recuadros editables y ventanas de gráfico desde el escenario (bloque `display`)
      → un escenario con caudales en m³/h se muestra sin recortes.
- [ ] **F1.7** · backend-dev · Alarmas por escenario, con arranques escalados por τ
      → no hay falsas alarmas LOW_CONV al arrancar con τ de minutos.
- [ ] **F1.8** · backend-dev · Contraseña de Admin fuera del código y de la documentación (configuración externa)
      → `grep 12345` sin resultados.
- [ ] **F1.9** · backend-dev · Eliminar `sys.path.insert`; imports como paquete → pytest y el `.exe` siguen funcionando.
- [ ] **F1.10** · backend-dev · `run_log` acotado y perfiles solo bajo demanda → corrida larga sin crecimiento de memoria.
- [ ] **F1.11** · writer + frontend-dev · Corregir la deriva de `docs_tab.py`, `fundamentals.md`, `frontend.md` y `CONVENTION.md`
      (ΔHr, ruido de TE, `h_loss`, CFL, nombres de tags, §A.4/§A.5)
      → el `engineer` verifica cada afirmación contra el código.

**Salida:** pytest en verde; un segundo escenario PFR de prueba corre de punta a punta sin tocar `ui/`.

## Fase 2 — Modelo físico v3

**Objetivo:** un sensor y unos datos que el estudiante pueda criticar con rigor.

- [ ] **F2.1** · engineer · Especificación de la conductividad de Kohlrausch: σ = Σ λᵢ(T)·Cᵢ + b, con compensación de temperatura
      → documento con λ° por especie, rango de validez, cálculo en Python y fuentes.
- [ ] **F2.2** · backend-dev · Sensor de conductividad multiespecie en `reactor_simulation/sensors/`; especies y etiquetas por escenario (A / B / productos)
      → tests contra el oráculo del `engineer`; el escenario de banco reproduce el comportamiento previo dentro de tolerancia declarada.
- [ ] **F2.3** · backend-dev · ΔHr activable por escenario → test exotérmico existente + uno de escenario.
- [ ] **F2.4** · engineer · Documentar el origen de Ea = 46 kJ/mol y de k₀ del escenario de banco (las fuentes revisadas dan valores distintos: ≈ 46–61 kJ/mol)
      → nota en `fundamentals.md` con cita y rango.
- [ ] **F2.5** · engineer · Auditoría de la fase → veredicto sin hallazgos críticos.

**Salida:** F2.5 aprobada.

## Fase 3 — Escenario EPIVALDÉS R-200

**Objetivo:** un escenario de planta con falla sembrada, en la lógica BIOVALDÉS.

- [ ] **F3.1** · engineer · Auditar la cinética de Sun 2017 (k₁, Ea) contra otras fuentes (Tollini 2022, Carrà 1979, Åbo Akademi) y declarar la incertidumbre
      → informe con rango aceptable para la v3.
- [ ] **F3.2** · engineer · Oráculo de dimensionamiento en Python: Q (m³/h), L, D, τ, Re, UA necesario, conversión objetivo, 10 kt/año de ECH y balance de sodio
      → `docs/plant/r200_dimensionamiento.md` + script reproducible.
- [ ] **F3.3** · backend-dev · `scenarios/pfr/epivaldes_r200.json`: cinética en SI, geometría, intercambiador E-200 con UA dimensionado, PID TIC-200, sensor AT-215
      → test de integridad y de conversión de diseño.
- [ ] **F3.4** · backend-dev · Falla sembrada en `oculto`: deriva de +8 % en FT-202 (el caudalímetro de NaOH lee de menos y el lazo de razón inyecta exceso de OH⁻)
      → la falla se detecta en AT-215 y en el balance de Na; no aparece en `visible`.
- [ ] **F3.5** · backend-dev · Distractor: ensuciamiento de E-200 (apertura creciente de TV-200) que no explica la conductividad alta → test.
- [ ] **F3.6** · backend-dev + frontend-dev · Selector de escenario PFR; `pfr_default` se conserva como "planta piloto"
      → ambos escenarios seleccionables desde la interfaz.
- [ ] **F3.7** · writer · Tabla "real vs. simplificado" y memorando del caso (con el `engineer` revisando)
      → `docs/plant/epivaldes_caso.md`.
- [ ] **F3.8** · engineer · Auditoría de la fase → veredicto sin hallazgos críticos.

**Tags previstos (ISA):** FT-201 / FT-202 / FFIC-202, M-200, E-200, TT-200 / TIC-200 / TV-200, R-200,
TT-210…214, AT-215, PT-210. Tren aguas arriba y aguas abajo (hidrocloración, stripping C-300, GC de
laboratorio AT-310) como contexto del diagrama, no simulado.

**Salida:** F3.8 aprobada; el escenario corre estable en `pfr_workspace` sin tocar `ui/`.

## Fase 4 — UI de planta 2D

- [ ] **F4.1** · frontend-dev · P&ID nuevo con texto como `<text>` y tags por escenario; regenerar hitboxes
      → los tags se pueden cambiar sin rehacer el SVG.
- [ ] **F4.2** · frontend-dev · Perfil de temperatura y concentración a lo largo del tubo (usa `T_profile` / `C_profile` del snapshot)
      → gráfico visible en el Diagram o en Graph.
- [ ] **F4.3** · frontend-dev · La status card no muestra la conversión al estudiante (la calcula él a partir de los datos)
      → verificado en ambos escenarios.
- [ ] **F4.4** · frontend-dev + backend-dev · Registro de eventos con tags y unidades del escenario
      → exportación `.txt` con tags de planta.

**Salida:** recorrido completo de un estudiante simulado (GO → ajuste → STOP → exportar) en ambos escenarios.

## Fase 5 — Documentación y release v3.0.0

- [ ] **F5.1** · writer · `documentacion_es.md` (manual del estudiante), `fundamentals.md`, `CHANGELOG.md` y `build.md` actualizados
      → el `engineer` verifica cada número.
- [ ] **F5.2** · backend-dev · Actualizar `ChemEng_SimLab.spec` (`datas` con los escenarios y SVG nuevos) y construir el `.exe`
      → el ejecutable corre sin Python instalado.
- [ ] **F5.3** · 👤 · Piloto con al menos una persona voluntaria en un equipo de estudiante → informe de hallazgos en `docs/handoffs/`.
- [ ] **F5.4** · 👤 · Congelar v3.0.0 (tag), al menos dos semanas antes de la primera sesión de la Exp 2.

**Salida:** `v3.0.0` etiquetada y piloto sin bloqueantes.

---

## Visión de largo plazo — Planta integrada BIOVALDÉS–EPIVALDÉS

El simulador pasa a ser **una sola planta simulada**. Cada sector es el escenario de una experiencia o de
un módulo y los sectores se conectan por las corrientes reales del proceso.

| Sector | Proceso | Módulo / experiencia | Estado |
|---|---|---|---|
| S1 Biodiésel | Transesterificación de aceite con metanol en CSTR en serie y separadores (caso MC1 BIOVALDÉS) | Módulo CSTR en serie (futuro); conecta con la MC1 | Nuevo |
| S2 Glicerina | Refinado de la glicerina cruda: neutralización, recuperación de metanol, columnas de intercambio iónico o adsorción | **Exp 3 RTD** (columnas empacadas actuales reubicadas en este sector) | Existe el modelo; falta reencuadrarlo |
| S3 Hidrocloración | Glicerina + HCl → DCH, catalizada por ácido carboxílico (etapa 1 del proceso Epicerol) | Módulo futuro (cinética catalizada, fase gas) | Nuevo |
| S4 Epiclorhidrina | Prerreactor tubular R-200 (DCH + NaOH → ECH) y stripping | **Exp 2 PFR** (Fase 3); después, módulo de reacciones en serie | Fase 3 |
| S5 Patente Epicerol | Lectura técnica de la patente de Solvay y de US 9422256: diagrama de bloques y condiciones; base de verdad del caso | Insumo de `engineer` y `writer`: `docs/plant/epicerol_patente.md` | Investigación |

**Antes de la Fase 7**, `engineer` y `writer` producen `docs/plant/vision.md` con el balance de materia
global (biodiésel → glicerina → DCH → ECH a 10 kt/año), para que las escalas de los sectores sean
coherentes. Todo número sale de un cálculo en Python.

### Fase 6 — 3D de planta (condicionada)

- **Entrada:** v3.0.0 usada por una cohorte y evaluada; Fase 7 con el mapa de planta funcionando.
- [ ] **F6.1** · frontend-dev · Spike técnico: Qt Quick 3D frente a QWebEngine + three.js, medido en peso del `.exe`,
      rendimiento y compatibilidad en los equipos de los estudiantes → informe con recomendación.
- [ ] **F6.2** · frontend-dev · Vista 3D de solo lectura que consume `EngineSnapshot`; recorrido por sectores
      → el SCADA 2D sigue siendo el respaldo obligatorio y funciona sin la vista 3D.
- [ ] **F6.3** · 👤 · Prueba en los equipos reales y decisión de uso en clase.

### Fase 7 — Arquitectura de planta

- [ ] **F7.1** · writer · ADR: ¿los sectores se acoplan dinámicamente o solo comparten el contexto narrativo y la base de corrientes?
      Recomendación inicial: solo contexto, sin co-simulación → ADR aceptado por Marco.
- [ ] **F7.2** · backend-dev · Registro de módulos (ex ítem 1 de `ROADMAP_V2`); `app.py` y `HomeScreen` leen el registro
      → agregar un módulo no toca `app.py`.
- [ ] **F7.3** · backend-dev · Escenario `plant/*.json` que declara sectores, corrientes entre ellos y tags con prefijo de área (100 / 200 / 300…).
- [ ] **F7.4** · frontend-dev · Pantalla de inicio como mapa de planta navegable por sector.

### Fase 8 — Reencuadre de RTD en S2

- [ ] **F8.1** · engineer + writer · Definir el rol de las columnas en el refinado de glicerina (coordinar con la decisión abierta del curso sobre el tren de la Exp 3).
- [ ] **F8.2** · backend-dev + frontend-dev · `planta_a/b/c` pasan a ser columnas del sector S2, con tags de área → tests de integridad intactos.

### Fase 9 — Sectores nuevos S1 y S3

Cada sector sigue el ciclo `engineer` (especificación y oráculo) → `backend-dev` → `frontend-dev` → `writer`.

- [ ] **F9.1** · S1 Biodiésel: CSTR en serie con transesterificación (cinética y escala del caso MC1).
- [ ] **F9.2** · S3 Hidrocloración de glicerina (cinética catalizada y fase gas; requiere nuevo modelo en `models/`).

---

## Backlog

- **Módulo "Selectividad: reacciones en serie"** (A + B → R, R + B → S; hidrólisis de ECH). `writer` y `engineer`
  escriben `docs/modules/series/design.md` con:
  - parámetros de Sun 2017 para la hidrólisis (Ea₂ = 32 kJ/mol, dato débil; contrastar con Tollini 2022);
  - el argumento PFR frente a CSTR en selectividad;
  - el sensor: la conductividad mide la conversión del álcali pero **no la selectividad**; esta requiere GC fuera de línea.
- **Docs en la app con fuente única** (ex ítem 2 de `ROADMAP_V2`): un solo `.md` para las pestañas Docs y para `docs/modules/*/fundamentals.md`, con separación visible/oculto explícita.
- **Variedad de escenarios PFR** (ex ítem 3 de `ROADMAP_V2`): cubierta por la Fase 3.
- **Pruebas de UI** (pytest-qt): hoy no existen; evaluar tras la Fase 4.

## Decisiones abiertas

| # | Decisión | Quién | Bloquea |
|---|---|---|---|
| 1 | Fuente y rango aceptable de los parámetros de Sun 2017 (F3.1) | engineer → Marco | F3.3 |
| 2 | Origen declarado de Ea = 46 kJ/mol del escenario de banco (F2.4) | engineer → Marco | F5.1 |
| 3 | Acoplamiento entre sectores de planta (F7.1) | Marco | Fase 7 |
| 4 | Tecnología 3D (F6.1) | Marco, tras el spike | F6.2 |
| 5 | Tren de columnas de la Exp 3 (decisión del curso) | Marco | Fase 8 |

## Fuentes consultadas (2026-10-29)

- Sun, Xia, Xiang (2017), *Chem. Eng. Trans.* 61 — https://www.aidic.it/cet/17/61/298.pdf
- Patente US 9422256 (ECH desde glicerol) — condiciones de τ y temperatura.
- Biodiesel Magazine, planta Vinythai (100 kt/año) y Solvay Epicerol Tavaux (10 kt/año al inicio).
- Tollini et al. (2022), hidrólisis de ECH y glicidol — https://doi.org/10.1039/d2re00191h (texto completo no leído).
- Los valores marcados como débiles o de fuente única deben pasar por F3.1 antes de usarse.
