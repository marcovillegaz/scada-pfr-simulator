# Manual del Estudiante — ChemEng SimLab

Guía de instalación y uso de **ChemEng SimLab**, el simulador SCADA que
reemplaza los laboratorios de ingeniería química de reacción (Experiencia 2,
reactor PFR) y de flujo no ideal (Experiencia 3, ensayo de trazador RTD/CIP).

---

## A.1 · Instalación

**Requisitos.** El software funciona únicamente en Windows.

1. Descarguen el archivo comprimido (`.zip`) desde el enlace que les
   entregue el docente.
2. Descompriman **por completo** la carpeta en su equipo (no ejecuten el
   `.exe` desde dentro del comprimido).
3. Ejecuten `ChemEng_SimLab.exe`, dentro de la carpeta descomprimida.
4. Si aparece la pantalla azul de Windows SmartScreen («Windows protegió tu
   PC»), es porque el programa no está firmado digitalmente, **no** porque
   sea peligroso. Hagan clic en «Más información» y luego en «Ejecutar de
   todas formas».

Si el programa no abre: verifiquen que descomprimieron la carpeta completa
(no solo el `.exe` suelto) y que están en Windows — no hay build para
macOS/Linux.

---

## A.2 · Recorrido de la interfaz

Al abrir el programa aparece la **pantalla de inicio**, con tres tarjetas:

| Tarjeta | Qué abre |
|---|---|
| **PFR — Saponification Reactor** | El reactor tubular (Experiencia 2) |
| **RTD — Experiencia 3** | El ensayo de trazador / CIP (Experiencia 3) |
| **About** | Autor, contacto, licencia e historial de versiones |

Cada módulo se abre en pantalla completa. El botón **«≡ Home»**, arriba a la
izquierda de cada módulo, siempre los devuelve a la pantalla de inicio — y al
hacerlo **detiene automáticamente** cualquier simulación en marcha, para que
no quede corriendo sin que la vean.

Dentro de cada módulo, la ventana se organiza en tres franjas:

```
┌────────────────────────────────────────────────────────┐  ← encabezado
│  ≡ Home │ [Diagram] [Graph] [Table] [Docs] (…)          │
├────────────────────────────────────────────────────────┤
│                                                          │
│              contenido de la pestaña activa             │  ← se estira
│                                                          │
├────────────────────────────────────────────────────────┤  ← pie
│  [GO/STOP]  [RESET]  Speed: ──  Status: …  Sim time: …  │
└────────────────────────────────────────────────────────┘
```

Las pestañas del encabezado son comunes a ambos módulos:

- **Diagram** — el P&ID interactivo: hagan clic en un equipo para ver su
  info; los parámetros editables aparecen como recuadros sobre el propio
  diagrama.
- **Graph** — gráficos en vivo de las variables de proceso.
- **Table** — tabla de datos del ensayo, con exportación CSV/Excel (ver
  §A.4).
- **Docs** — teoría y fundamentos del módulo, dentro de la misma app.
- **Admin** *(solo PFR)* — pestaña protegida por contraseña, con la vista
  completa de variables internas y su propia exportación. Pídanle la
  contraseña a su docente si la necesitan.

El pie de página también es común a ambos módulos:

| Control | Qué hace |
|---|---|
| **GO / STOP** | Inicia o detiene la simulación |
| **RESET** | Reinicia el motor y borra todos los gráficos/tablas |
| **Speed** | Multiplica la velocidad de la simulación respecto del tiempo real (útil para no esperar minutos reales por segundos de proceso) |
| **Status** | «Stopped / Running / Ready» |
| **Sim time** | Tiempo simulado transcurrido, en segundos |
| **Apply** | Envía al motor los valores que hayan editado en el diagrama |

**Importante:** editar un recuadro del diagrama (caudal, concentración,
consigna) no cambia nada hasta que aprieten **Apply**.

---

## A.3 · Módulo PFR (Experiencia 2)

Reactor tubular de saponificación (NaOH + acetato de etilo), con dos
corrientes de alimentación, intercambiador de calor con agua caliente
controlado por PID, y sensores con ruido realista (CT-101 conductividad,
TE-101/TE-102 temperatura).

**Parámetros editables en el diagrama** (recuadros sobre el P&ID, aplican
con el botón Apply del pie de página):

| Recuadro | Variable | Unidad |
|---|---|---|
| Qa0 | Caudal de alimentación A (NaOH) | mL/min |
| Ca0 | Concentración de alimentación A | mol/L |
| Qb0 | Caudal de alimentación B (EtAc) | mL/min |
| Cb0 | Concentración de alimentación B | mol/L |
| Consigna (T setpoint) | Temperatura objetivo del PID | °C |

Hagan clic sobre cualquier equipo del diagrama (reactor, intercambiador,
controlador de temperatura, sensores) para abrir su ventana de información
con más detalle y, en algunos casos, ganancias del PID ajustables.

**Alarmas.** El sistema marca alarma de temperatura ALTA/BAJA y de
conversión BAJA con histéresis (no se dispara y se apaga con el mismo
valor exacto, para evitar parpadeo) — revisen el registro de eventos en la
pestaña Diagram.

**Flujo de trabajo típico:**
1. Ajusten Qa0/Ca0, Qb0/Cb0 y la consigna de temperatura si el ensayo lo
   requiere, y presionen **Apply**.
2. **GO** para iniciar. Usen **Speed** para acelerar si necesitan llegar
   a estado estacionario.
3. Observen la pestaña **Graph** (temperatura y consigna, % de válvula,
   caudales, conductividad) mientras corre.
4. **STOP** cuando terminen el ensayo.
5. **Table** para revisar/exportar los datos (ver §A.4). **RESET** antes de
   empezar un ensayo nuevo.

---

## A.4 · Módulo RTD / CIP (Experiencia 3)

Ensayo de trazador sobre tres reactores empacados en paralelo (R-102,
R-103, R-104), enmarcado como validación **CIP** (Clean-In-Place): aíslan
un reactor para "lavarlo" e inyectan trazador para leer su curva de
lavado a través del fotocolorímetro AT-101.

**Panel CIP PROTOCOL** (barra lateral): un botón por reactor (**R-102**,
**R-103**, **R-104**). Al seleccionar uno, el diagrama cambia a la vista
CIP de ese reactor y la inyección queda habilitada; sin ningún reactor
seleccionado, el sistema está en operación normal y no se puede inyectar.

**Panel TRACER INJECTION** (barra lateral), habilitado solo con un reactor
seleccionado:

| Control | Qué hace |
|---|---|
| **Dose (mg)** + **Inject Pulse** | Inyecta un pulso rectangular de la dosis indicada |
| **C0 (mg/L)** + **Start Step** / **Stop Step** | Abre/cierra la alimentación de trazador a concentración constante |

El caudal (**Q**, recuadro editable en el diagrama, en L/min) también se
aplica con el botón **Apply** del pie de página, igual que en PFR.

**Flujo de trabajo típico:**
1. Seleccionen el reactor a ensayar en el panel CIP PROTOCOL.
2. Ajusten el caudal si corresponde y presionen **Apply**.
3. **GO** para iniciar la corrida.
4. Elijan modo **pulso** (dosis + Inject Pulse) o **escalón** (C0 + Start
   Step, luego Stop Step cuando quieran cerrar la inyección).
5. Usen **Speed** para acelerar — τ (tiempo medio de residencia) puede ser
   de varios minutos de tiempo real por ensayo.
6. Dejen correr hasta que la señal vuelva al ruido de base, **STOP**, y
   exporten los datos (ver §A.4 más abajo — la sección siguiente aplica a
   ambos módulos).
7. **RESET** antes de un ensayo nuevo, o seleccionen otro reactor para
   cambiar de columna.

La pestaña **Docs** de este módulo cubre la teoría (E(t), momentos,
modelos de un parámetro) sin revelar los parámetros ocultos del lecho —
esa es justamente la incógnita que deben diagnosticar con los datos
exportados.

---

## A.5 · Datos y exportación (ambos módulos)

Al detener la corrida (**STOP**), la pestaña **Table** carga la serie
temporal completa como una tabla, una fila por muestra. Los botones
**Export CSV** y **Export Excel**, debajo de la tabla, guardan esos mismos
datos en el formato elegido para procesarlos en su herramienta de hoja de
cálculo.

**Registro de eventos.** La pestaña **Diagram** de cada módulo mantiene un
registro (scroll) de eventos del ensayo — inicio/fin de corrida, cambios de
parámetros, alarmas — útil para reconstruir la secuencia de lo que
hicieron al escribir el informe.

**Flujo de trabajo típico (resumen):** configuren → **GO** → dejen correr
(acelerando si hace falta) hasta que la señal vuelva al ruido de base →
**STOP** → exporten los datos → procesen en Excel/Python: conversión o
normalización, momentos, ajuste de modelos, contraste modelo–dato.

---

## Créditos

Ver la pestaña **About** dentro de la aplicación para autor, contacto,
licencia y cómo citar el software.
