# FUNDAMENTS_EXP3.md — Fundamento matemático de la Experiencia 3

**Flujo no ideal: distribución de tiempos de residencia, modelos de flujo y diagnóstico
hidrodinámico de un lecho fijo.**

Documento de referencia interna. Base teórica para la construcción del simulador y para la posterior
redacción de la guía de estudiante.

---

## Nomenclatura

| Símbolo | Descripción | Unidad SI |
|---|---|---|
| $t$ | Tiempo | s |
| $V$ | Volumen total del recipiente (vacío interparticular disponible al flujo) | m³ |
| $Q$ | Caudal volumétrico de alimentación | m³·s⁻¹ |
| $\tau$ | Tiempo espacial nominal, $\tau = V/Q$ | s |
| $\bar{t}_m$ | Tiempo medio de residencia medido (primer momento de $E$) | s |
| $\theta$ | Tiempo adimensional, $\theta = t/\bar{t}_m$ | — |
| $C(t)$ | Concentración de trazador a la salida | mol·m⁻³ |
| $C_0$ | Concentración de trazador en la alimentación (escalón) | mol·m⁻³ |
| $m$ | Masa (o moles) de trazador inyectada (pulso) | mol |
| $E(t)$ | Función de distribución de tiempos de residencia | s⁻¹ |
| $E(\theta)$ | Distribución en tiempo adimensional | — |
| $F(t)$ | Distribución acumulada de tiempos de residencia | — |
| $\sigma^2$ | Varianza de la distribución (segundo momento central) | s² |
| $\sigma_\theta^2$ | Varianza adimensional, $\sigma_\theta^2 = \sigma^2/\bar{t}_m^2$ | — |
| $N$ | Número de tanques en serie (modelo de tanques en serie) | — |
| $D_{ax}$ | Coeficiente de dispersión axial | m²·s⁻¹ |
| $u$ | Velocidad intersticial media, $u = Q/A_t \varepsilon_L$ | m·s⁻¹ |
| $L$ | Longitud del lecho | m |
| $Pe$ | Número de Péclet, $Pe = uL/D_{ax}$ | — |
| $A$ | Absorbancia medida | — |
| $\varepsilon$ | Absortividad molar del trazador | m²·mol⁻¹ |
| $b$ | Paso óptico de la celda | m |
| $f$ | Fracción del caudal que circula por el canal (bypass) | — |
| $\gamma$ | Razón de tiempos del canal, $\tau_c/\tau$ (el canal es $1/\gamma$ veces más rápido) | — |
| $\varphi_c$ | Fracción del volumen ocupada por el canal, $\varphi_c = \gamma f$ | — |
| $\varphi_d$ | Fracción del volumen correspondiente a la zona muerta | — |
| $V_d$ | Volumen de la zona muerta, $V_d = \varphi_d V$ | m³ |
| $V_m$ | Volumen del camino principal, $V_m = V(1-\varphi_d-\varphi_c)$ | m³ |
| $N_m$ | Número de tanques del camino principal (verdad oculta) | — |
| $N_c$ | Número de tanques del canal (verdad oculta) | — |
| $v_m$ | Volumen de cada tanque del camino principal, $v_m = V_m/N_m$ | m³ |
| $v_c$ | Volumen de cada tanque del canal, $v_c = \varphi_c V/N_c$ | m³ |
| $k_{ex}$ | Coeficiente de intercambio con la zona muerta | s⁻¹ |
| $q_{ex}$ | Caudal de intercambio con la zona muerta, $q_{ex} = k_{ex} V_d$ | m³·s⁻¹ |
| $t_{obs}$ | Ventana de observación del ensayo | s |

> **Nota sobre unidades prácticas.** En el laboratorio se trabaja con L y mL·s⁻¹. Las ecuaciones son
> dimensionalmente homogéneas, de modo que basta usar un sistema consistente. El único punto de
> cuidado es $\varepsilon b$, que en la práctica se maneja como una constante de calibración
> agrupada con unidades de [absorbancia · (mol·m⁻³)⁻¹].

---

## 1. Planteamiento del problema

Un balance de materia global establece *cuánto* fluido atraviesa un equipo, pero no informa **cuánto
tiempo permaneció cada elemento de fluido en su interior**. En un reactor real, dos elementos que
ingresan simultáneamente pueden abandonar el equipo en instantes muy distintos: uno puede encontrar
un camino preferencial de baja resistencia y otro quedar retenido en una región de estancamiento.

Esta distribución de tiempos condiciona directamente la conversión alcanzable, y su desviación
respecto de los patrones ideales constituye la base del **diagnóstico hidrodinámico** de un equipo
industrial.

### 1.1 Edad y tiempo medio de residencia

Se denomina **edad** de un elemento de fluido al tiempo transcurrido desde su ingreso al sistema. La
**distribución de tiempos de residencia** (RTD) es la función de densidad de probabilidad de las
edades del fluido que abandona el equipo:

$$E(t)\,dt = \text{fracción del caudal de salida con edad comprendida entre } t \text{ y } t+dt$$

Por tratarse de una densidad de probabilidad, satisface la condición de normalización

$$\int_0^{\infty} E(t)\,dt = 1 \tag{1}$$

con $E(t) \geq 0$ y unidades de s⁻¹.

### 1.2 Los casos límite ideales

Los dos reactores ideales corresponden a los extremos del espectro de mezclado:

**Reactor de flujo pistón (RFP).** Todos los elementos de fluido permanecen exactamente el mismo
tiempo. La distribución degenera en una delta de Dirac:

$$E(t) = \delta(t - \tau) \tag{2}$$

**Reactor de tanque agitado continuo (RTAC).** La mezcla es instantánea y perfecta, de modo que la
probabilidad de que un elemento abandone el reactor en el siguiente instante es independiente de su
edad. Esta propiedad de "falta de memoria" conduce a una distribución exponencial:

$$E(t) = \frac{1}{\tau}\,e^{-t/\tau} \tag{3}$$

Todo equipo real presenta una distribución intermedia. El objeto del ensayo es **medir esa
distribución** y **cuantificar su desviación** respecto del comportamiento esperado.

---

## 2. Medición experimental: técnica estímulo–respuesta

La RTD no es observable directamente: el interior del equipo es inaccesible. Se determina mediante un
experimento de estímulo–respuesta con un **trazador**, una sustancia que debe cumplir tres
condiciones: ser inerte (no reacciona ni se adsorbe), ser detectable a baja concentración, y poseer
propiedades de transporte similares a las del fluido de proceso.

### 2.1 Inyección tipo pulso

Se introduce una masa $m$ de trazador en un intervalo muy breve en $t=0$ y se registra $C(t)$ a la
salida. Puesto que todo el trazador ingresó simultáneamente, la concentración de salida es
proporcional a la distribución de edades. Aplicando la condición de normalización (1):

$$\boxed{\;E(t) = \frac{C(t)}{\displaystyle\int_0^{\infty} C(t)\,dt}\;} \tag{4}$$

El denominador admite además una verificación independiente por balance de materia:

$$m = Q \int_0^{\infty} C(t)\,dt \tag{5}$$

Si la masa recuperada por la ecuación (5) difiere apreciablemente de la inyectada, se concluye que el
trazador no es inerte (adsorción sobre el empaque) o que la ventana de observación truncó una
fracción no despreciable de la curva. Ambas conclusiones son relevantes para el diagnóstico.

> **Sobre la idealidad del pulso.** Una delta de Dirac es físicamente irrealizable: una jeringa
> entrega un pulso rectangular de ancho finito $\Delta t_p$. La aproximación es válida cuando
> $\Delta t_p \ll \tau$; en la práctica, $\Delta t_p / \tau < 0{,}05$ resulta suficiente.

### 2.2 Inyección tipo escalón

Se conmuta la alimentación desde $C=0$ a $C=C_0$ constante en $t=0$ y se registra la salida. La
respuesta normalizada corresponde a la **distribución acumulada**:

$$\boxed{\;F(t) = \frac{C_{out}(t)}{C_0} = \int_0^{t} E(t')\,dt'\;} \tag{6}$$

$F(t)$ responde a la pregunta: *¿qué fracción del fluido que sale posee una edad menor que $t$?*. Es
monótona creciente, con $F(0)=0$ y $F(\infty)=1$.

### 2.3 Relación entre ambas técnicas y verificación cruzada

De (6) se desprende inmediatamente

$$E(t) = \frac{dF(t)}{dt} \tag{7}$$

Ambas inyecciones contienen, por tanto, la misma información. Disponer de las dos permite una
**verificación cruzada**: la derivada numérica de la curva $F$ obtenida por escalón debe reproducir
la curva $E$ obtenida por pulso.

La comparación tiene además un contenido metodológico propio: la derivación numérica **amplifica** el
ruido de medición, mientras que la integración lo **atenúa**. Es previsible que la $E$ reconstruida
desde el escalón resulte más ruidosa que la obtenida directamente del pulso.

### 2.4 Cadena de medición: ley de Lambert–Beer

El fotocolorímetro no entrega concentración sino **absorbancia**. Para soluciones diluidas rige la
ley de Lambert–Beer:

$$A = \varepsilon\, b\, C \tag{8}$$

donde el producto $\varepsilon b$ constituye la constante de calibración del instrumento. La relación
es lineal únicamente dentro de un rango acotado: por sobre un valor $A_{max}$ el detector satura y la
proporcionalidad se pierde. Esto impone una **restricción de diseño experimental**: la dosis de
trazador debe ser suficiente para superar el ruido del instrumento, pero no tanto como para saturar
el pico de la respuesta.

---

## 3. Momentos de la distribución

Caracterizada $E(t)$, se extraen sus momentos estadísticos.

### 3.1 Primer momento: tiempo medio de residencia

$$\bar{t}_m = \int_0^{\infty} t\,E(t)\,dt \tag{9}$$

Para datos discretos muestreados a intervalo $\Delta t$, se evalúa numéricamente (regla del trapecio
o de Simpson):

$$\bar{t}_m \approx \frac{\sum_i t_i\, C_i\, \Delta t}{\sum_i C_i\, \Delta t} \tag{10}$$

**Resultado fundamental.** Para un recipiente cerrado en el que la totalidad del volumen participa
del flujo, la teoría establece

$$\bar{t}_m = \tau = \frac{V}{Q} \tag{11}$$

independientemente de cuán complejo sea el patrón de flujo interno. La ecuación (11) es la base del
primer y más potente diagnóstico: se compara el $\tau$ calculado a partir de la geometría y el caudal
medido con el $\bar{t}_m$ obtenido del trazador. Una discrepancia

$$\bar{t}_m < \tau \tag{12}$$

indica la existencia de volumen que el flujo no está recorriendo, y permite estimar la fracción de
volumen muerto como

$$\varphi_d \approx 1 - \frac{\bar{t}_m}{\tau} \tag{13}$$

La sección 7 discute una sutileza importante respecto del alcance de esta interpretación.

### 3.2 Segundo momento: varianza

$$\sigma^2 = \int_0^{\infty} (t-\bar{t}_m)^2\,E(t)\,dt \tag{14}$$

y su forma adimensional

$$\sigma_\theta^2 = \frac{\sigma^2}{\bar{t}_m^2} \tag{15}$$

La varianza mide el **ancho** de la distribución, es decir, el grado de mezclado axial. Sus valores de
referencia son $\sigma_\theta^2 = 0$ para el RFP ideal y $\sigma_\theta^2 = 1$ para el RTAC ideal.
Este es el parámetro que alimenta ambos modelos de ajuste de la sección 4.

> **Advertencia numérica.** El segundo momento pondera por $(t-\bar{t}_m)^2$ y es, por tanto,
> extremadamente sensible a la cola de la distribución, justamente donde la señal es débil y la
> relación señal/ruido es peor. Truncar la cola prematuramente **subestima** sistemáticamente
> $\sigma^2$.

### 3.3 Lectura cualitativa de la curva: firmas hidrodinámicas

Antes de cualquier ajuste, la forma de $E(t)$ admite un diagnóstico directo:

| Observación | Interpretación física |
|---|---|
| Pico o hombro a $t \ll \tau$ | **Cortocircuito o canalización**: una fracción del caudal atraviesa el equipo con residencia mínima |
| Cola de decaimiento más lento que la exponencial de $\tau$ | **Zona de estancamiento** con intercambio lento con el flujo principal |
| Curva bimodal | Dos caminos en paralelo con tiempos característicos claramente distintos; canalización severa |
| $\bar{t}_m < \tau$ | Volumen muerto (ver §7) |
| Curva unimodal, angosta, centrada en $\tau$ | Comportamiento próximo al flujo pistón con dispersión moderada |

---

## 4. Modelos de un parámetro

Ambos modelos comprimen la totalidad de la curva $E$ en un único número que cuantifica el
alejamiento respecto del flujo pistón.

### 4.1 Modelo de tanques en serie

Se representa el equipo real mediante $N$ RTAC ideales iguales dispuestos en cascada. La distribución
resultante es

$$E(\theta) = \frac{N\,(N\theta)^{N-1}}{(N-1)!}\;e^{-N\theta}, \qquad \theta = \frac{t}{\bar{t}_m} \tag{16}$$

que corresponde a una distribución gamma. Sus casos límite son $N=1$ (RTAC ideal) y $N \to \infty$
(RFP ideal).

La propiedad que hace útil al modelo es la relación directa entre la varianza y el parámetro:

$$\sigma_\theta^2 = \frac{1}{N} \quad \Longrightarrow \quad \boxed{\;N = \frac{\bar{t}_m^2}{\sigma^2}\;} \tag{17}$$

El ajuste es, por tanto, explícito: no requiere regresión no lineal. Un lecho fijo en buen estado
presenta $N$ elevado (típicamente 10–30); un valor anormalmente bajo sugiere mezclado excesivo o la
presencia de patologías.

### 4.2 Modelo de dispersión axial

Se representa el equipo como un flujo pistón sobre el que se superpone un término difusivo que
agrupa todos los mecanismos de mezclado axial:

$$\frac{\partial C}{\partial t} = -u\,\frac{\partial C}{\partial z} + D_{ax}\,\frac{\partial^2 C}{\partial z^2} \tag{18}$$

En forma adimensional, con $z^* = z/L$, el único parámetro es el **número de Péclet**:

$$Pe = \frac{u L}{D_{ax}} \tag{19}$$

que expresa la razón entre transporte convectivo y dispersivo. Sus límites son $Pe \to \infty$ (RFP
ideal) y $Pe \to 0$ (mezcla completa).

Para condiciones de contorno de **recipiente cerrado–cerrado** (las aplicables a una columna con
alimentación y descarga por tubería), la relación entre la varianza medida y el Péclet es:

$$\sigma_\theta^2 = \frac{2}{Pe} - \frac{2}{Pe^{2}}\left(1 - e^{-Pe}\right) \tag{20}$$

La ecuación (20) es implícita en $Pe$ y debe resolverse numéricamente (Solver de Excel, bisección o
Newton–Raphson).

### 4.3 Equivalencia entre ambos modelos

Ambos modelos describen el mismo fenómeno —desviación respecto del flujo pistón— con imágenes físicas
distintas. Para desviaciones pequeñas ($\sigma_\theta^2 \ll 1$), la ecuación (20) se reduce a
$\sigma_\theta^2 \approx 2/Pe$, y comparando con (17):

$$Pe \approx 2N \tag{21}$$

La consistencia entre ambos ajustes constituye una verificación interna del procesamiento de datos.

### 4.4 Alcance y limitación de los modelos de un parámetro

Ambos modelos asumen que la no idealidad corresponde a una **dispersión homogénea distribuida a lo
largo del equipo**. Ninguno contempla flujo en paralelo ni regiones estancadas.

En consecuencia, frente a una patología estructural (canalización + zona muerta), ambos modelos
ajustan el **ancho** global de la distribución pero **no reproducen** ni el hombro temprano ni la
cola prolongada. La familia de curvas generada por la ecuación (16) es unimodal por construcción y no
puede representar una respuesta bimodal.

Detectar *dónde* falla el ajuste y explicar *por qué* constituye un resultado de mayor valor
diagnóstico que la mera obtención de un valor de $N$.

---

## 5. Modelo de compartimientos (verdad oculta del simulador)

Cuando la no idealidad no es dispersión distribuida sino una patología localizada, se recurre a los
**modelos combinados** de Levenspiel: representar el equipo real como una red de elementos ideales
conectados en serie y en paralelo, con intercambio entre regiones.

Para el lecho fijo con canalización que constituye el caso de estudio, la red consta de tres
elementos: un **camino principal** (cascada de $N_m$ tanques), un **canal** de bypass (cascada corta
de $N_c$ tanques con volumen reducido) y una **zona muerta** que intercambia con el camino principal.

### 5.1 Reparto de caudal y volumen

$$Q_m = (1-f)\,Q \qquad Q_c = f\,Q \tag{22}$$

$$\varphi_c = \gamma\,f \tag{23a}$$

$$V_m = V\,(1-\varphi_d-\varphi_c), \qquad V_c = \varphi_c V, \qquad V_d = \varphi_d V \tag{23b}$$

> **Sobre la ecuación (23a).** El volumen del canal debe escalar con el caudal que transporta. Si se
> fija $\varphi_c$ como constante independiente de $f$, al anular el bypass ($f \to 0$) ese volumen
> queda sin caudal y se transforma en una **segunda zona de estancamiento no declarada**: el caso
> "lecho sano" arrojaría entonces $\bar{t}_m < \tau$ sin que exista zona muerta, contradiciendo la
> ecuación (11). La proporcionalidad (23a) elimina el defecto y separa limpiamente los dos roles:
> $f$ cuantifica **cuánto** caudal se desvía y $\gamma$ cuantifica **qué tan rápido** es el canal.

$$v_m = \frac{V_m}{N_m}, \qquad v_c = \frac{V_c}{N_c}, \qquad q_{ex} = k_{ex}\,V_d \tag{24}$$

### 5.2 Balances de trazador

Cada compartimiento es un RTAC. El balance de materia sobre el trazador (acumulación = entrada −
salida) es lineal y de primer orden en todos los casos.

**Canal**, para $k = 1,\dots,N_c$, con $C_0^{\,c} \equiv C_{in}(t)$:

$$v_c\,\frac{dC_k^{\,c}}{dt} = f\,Q\left(C_{k-1}^{\,c} - C_k^{\,c}\right) \tag{25}$$

**Camino principal**, para $i = 1,\dots,N_m$, con $C_0 \equiv C_{in}(t)$ y acoplamiento de la zona
muerta en el tanque $j$:

$$v_m\,\frac{dC_i}{dt} = (1-f)\,Q\left(C_{i-1} - C_i\right) + \delta_{ij}\;q_{ex}\left(C_d - C_i\right) \tag{26}$$

donde $\delta_{ij}$ es la delta de Kronecker.

**Zona muerta** (sin flujo neto; solo intercambio):

$$V_d\,\frac{dC_d}{dt} = q_{ex}\left(C_j - C_d\right) \tag{27}$$

**Concentración de salida.** Los dos caminos confluyen. La mezcla se pondera por **caudales**, no por
concentraciones:

$$C_{out} = f\,C_{N_c}^{\,c} + (1-f)\,C_{N_m} \tag{28}$$

### 5.3 Condición de borde según el tipo de inyección

$$C_{in}(t) = \begin{cases}
C_p, & 0 \leq t < \Delta t_p \quad \text{(pulso rectangular)}\\[4pt]
0, & t \geq \Delta t_p
\end{cases}
\qquad\qquad
C_{in}(t) = \begin{cases}
0, & t < 0\\[4pt]
C_0, & t \geq 0 \quad \text{(escalón)}
\end{cases} \tag{29}$$

La dosis del pulso es $m = f\!\cdot\!Q\,C_p\Delta t_p + (1-f)Q\,C_p\Delta t_p = Q\,C_p\,\Delta t_p$.

### 5.4 Estructura del sistema

El vector de estado es

$$\mathbf{y} = \left[C_1,\dots,C_{N_m},\;C_1^{\,c},\dots,C_{N_c}^{\,c},\;C_d\right]^{T} \in \mathbb{R}^{N_m+N_c+1} \tag{30}$$

En el caso límite $f = 0$ se tiene $V_c = 0$ y la cascada del canal se desacopla; la implementación
debe contemplar esa singularidad.

Con $N_m = 12$ y $N_c = 2$, el sistema tiene 15 estados: dos órdenes de magnitud menos que un PFR
discretizado por el método de líneas. El sistema es **lineal, de coeficientes constantes y no
rígido** mientras $k_{ex}$ y $Q/v$ se mantengan dentro de rangos comparables.

> **Nota de implementación.** Este modelo se resuelve mediante ODEs y no requiere discretización
> espacial. Un esquema upwind de primer orden aplicado a la ecuación (18) introduciría **difusión
> numérica** del mismo orden de magnitud que el fenómeno físico bajo estudio, lo que impediría
> controlar el Péclet efectivo del escenario. La formulación por compartimientos evita este problema
> por construcción.

### 5.5 Origen de las firmas

La estructura de la red explica directamente las firmas de la tabla de §3.3:

- **Hombro temprano.** El canal posee un tiempo característico
  $$\tau_c = \frac{V_c}{Q_c} = \frac{\gamma f V}{f\,Q} = \gamma\,\tau \ll \tau \tag{31}$$
  Nótese que la **posición** del hombro queda fijada por $\gamma$ y es independiente de $f$; lo que
  $f$ controla es su **amplitud**, es decir, la fracción de trazador que emerge tempranamente.

- **Pico principal.** El camino principal con $N_m \approx 12$ produce una distribución angosta
  centrada cerca de $\tau$: el comportamiento del lecho en buen estado.

- **Cola prolongada.** La zona muerta libera su contenido con una constante de tiempo
  $$\tau_d = \frac{V_d}{q_{ex}} = \frac{1}{k_{ex}} \tag{32}$$
  que para valores pequeños de $k_{ex}$ puede alcanzar 5–10 veces $\tau$.

### 5.6 Verificación analítica del modelo

La consistencia interna de la red se comprueba con el primer momento. El tiempo medio de residencia
resultante de la mezcla de ambos caminos, ponderado por caudal, debe reproducir el tiempo espacial
del volumen efectivamente barrido:

$$\bar{t}_m = f\,\tau_c + (1-f)\,\tau_m = f\,\gamma\tau + (1-f)\,\frac{V(1-\varphi_d-\gamma f)}{(1-f)Q} = \frac{V(1-\varphi_d)}{Q} \tag{33}$$

resultado independiente de $f$ y de $\gamma$, como exige la ecuación (11) aplicada al volumen que el
flujo recorre. Al integrar sobre una ventana infinita y con $k_{ex}>0$, la zona muerta se incorpora y
se recupera $\bar{t}_m = \tau$ (ver §7).

Esta identidad constituye el test numérico más importante de la implementación: cualquier error en el
reparto de volúmenes se manifiesta como una discrepancia en el primer momento.

---

## 6. Cadena de contaminación de la medición

El simulador reproduce deliberadamente las capas que un experimento real superpone sobre la curva
$E(t)$ teórica:

| Capa | Efecto sobre la medición |
|---|---|
| Ancho finito del pulso ($\Delta t_p$) | Ensanchamiento leve; despreciable si $\Delta t_p \ll \tau$ |
| Muestreo discreto ($\Delta t$) | Error de cuadratura en los momentos |
| Calibración ($\varepsilon b$) | Requiere conversión $A \to C$; error sistemático si la constante es imprecisa |
| Ruido del detector | Afecta severamente el segundo momento y la derivación numérica de $F$ |
| Saturación del rango lineal | Distorsión del pico; pérdida de la proporcionalidad de (8) |
| Ventana de observación finita ($t_{obs}$) | Truncamiento de la cola; sesgo en $\bar{t}_m$ y $\sigma^2$ |

El trabajo del estudiante consiste en el **camino inverso**: remover estas capas hasta recuperar los
momentos y, a partir de ellos, el diagnóstico.

---

## 7. Sobre la interpretación del volumen muerto

Corresponde precisar el alcance de la ecuación (13), punto que suele generar confusión y que conviene
tener resuelto antes de la discusión con estudiantes.

Si $k_{ex} > 0$, la zona muerta **sí** comunica con el flujo principal. En consecuencia, el primer
momento verdadero de $E(t)$, integrado hasta $t \to \infty$, es exactamente

$$\bar{t}_m^{\,\infty} = \tau = \frac{V}{Q} \tag{34}$$

**incluida la zona muerta**. La ecuación (11) se cumple sin excepción para un recipiente cerrado.

¿Por qué, entonces, el ensayo arroja $\bar{t}_m < \tau$? Porque **todo experimento es finito**. La
contribución de la zona muerta a $\bar{t}_m$ se encuentra distribuida sobre una cola de duración
$\sim 1/k_{ex}$, con amplitud que rápidamente cae por debajo del límite de detección del
instrumento. En rigor, lo que se mide es un momento truncado:

$$\bar{t}_m^{\,obs} = \frac{\displaystyle\int_0^{t_{obs}} t\,C(t)\,dt}{\displaystyle\int_0^{t_{obs}} C(t)\,dt} \;<\; \tau \tag{35}$$

De modo que **el "volumen muerto" medido es, estrictamente, un artefacto de la ventana de
observación**. Lejos de ser un defecto del método, esta es exactamente la situación industrial: nadie
mantiene un fotocolorímetro registrando durante diez tiempos de residencia para cerrar un balance.

La consecuencia práctica es doble y merece figurar en la discusión del informe:

1. La fracción de volumen muerto reportada **depende de la ventana de observación**. Dos equipos de
   diagnóstico con protocolos distintos reportarán números distintos sobre el mismo equipo.
2. Una zona con $k_{ex}$ suficientemente pequeño es **operacionalmente** volumen muerto, aunque
   matemáticamente no lo sea: si su constante de tiempo excede la escala de operación de la planta,
   ese volumen no contribuye a la conversión. El diagnóstico correcto no es "hay volumen inaccesible"
   sino "hay volumen cuya escala de intercambio es incompatible con la operación".

---

## 8. Secuencia de procesamiento de datos

Resumen del procedimiento que ejecutará el estudiante sobre el archivo exportado:

1. **Conversión.** Aplicar (8) para obtener $C(t)$ a partir de $A(t)$; verificar que el pico no haya
   saturado.
2. **Normalización.** Integrar numéricamente $\int C\,dt$ y aplicar (4) para obtener $E(t)$.
3. **Verificación de balance.** Comprobar (5): masa recuperada frente a masa inyectada.
4. **Momentos.** Evaluar (10) y (14)–(15).
5. **Diagnóstico por comparación.** Contrastar $\bar{t}_m$ con $\tau = V/Q$; aplicar (13).
6. **Ajuste de modelos.** Obtener $N$ por (17) y $Pe$ resolviendo (20); verificar la consistencia
   aproximada con (21).
7. **Contraste modelo–experimento.** Superponer la curva del modelo de tanques en serie (16) sobre la
   curva $E$ experimental; identificar las regiones de discrepancia.
8. **Verificación cruzada.** Derivar numéricamente la curva $F$ del escalón según (7) y comparar con
   la $E$ del pulso.
9. **Lectura de firmas.** Aplicar la tabla de §3.3.
10. **Diagnóstico y recomendación.**

---

## Referencias

- Levenspiel, O. *Chemical Reaction Engineering*, 3ª ed., Wiley. Caps. 11–14 (RTD, modelo de
  dispersión, modelo de tanques en serie, modelos combinados).
- Fogler, H. S. *Elements of Chemical Reaction Engineering*, 4ª ed., Prentice Hall. Caps. 13–14
  (Distribuciones de tiempos de residencia; modelos de reactores no ideales).
- Cholette, A.; Cloutier, L. *Mixing efficiency determinations for continuous flow systems*, Can. J.
  Chem. Eng., 1959. (Modelo original de zona muerta con bypass.)
