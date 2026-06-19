# PFR Dynamic Simulation — Model Specification

> **Propósito:** Este documento describe la matemática del modelo dinámico de un PFR isotérmico (con pérdidas de calor) para guiar la implementación en la aplicación existente. El estado actual del modelo ignora la difusión axial y discretiza el espacio mediante el método de líneas (MOL) con diferencias upwind.

---

## 1. Supuestos del modelo

| Supuesto | Detalle |
|---|---|
| Sin difusión axial | `D_ax = 0`, `λ_ax = 0` |
| Flujo pistón ideal | Perfil radial plano, velocidad uniforme `u` |
| Densidad y Cp constantes | Fluido incompresible, propiedades evaluadas a temperatura de referencia |
| Reactor aislado con pérdidas | No hay intercambio con chaqueta (`U_jacket = 0`), solo pérdidas globales por pared |
| Control de temperatura en entrada | `T_in(t)` es impuesta externamente por un controlador PID + HX previo al reactor |
| Cinética de orden n en A | `(-r_A) = k0 · exp(-Ea / R·T) · CA^n` |

---

## 2. Modelo matemático

### 2.1 Balance de masa (componente A)

El balance diferencial sobre un volumen de control diferencial `dz` da:

```
∂CA/∂t = -u · ∂CA/∂z - (-rA)
```

Donde:
- `CA(z, t)` — concentración de A [mol/m³]
- `u` — velocidad superficial del fluido [m/s]
- `(-rA)` — tasa de reacción (consumo de A) [mol/m³·s]

### 2.2 Balance de energía con pérdidas

El reactor está aislado perfectamente en su pared lateral **excepto** por un término de pérdidas globales `Q_loss`. El balance es:

```
ρ·cp · ∂T/∂t = -ρ·cp·u · ∂T/∂z + (-ΔHr)·(-rA) - U_loss·a_s·(T - T_amb)
```

Donde:
- `T(z, t)` — temperatura del fluido en la posición z [K]
- `ΔHr` — calor de reacción [J/mol] (negativo si exotérmica)
- `U_loss` — coeficiente global de pérdidas de calor [W/m²·K]
- `a_s` — área específica de pérdida por unidad de volumen [m²/m³] = `4/d_t` para tubo
- `T_amb` — temperatura ambiente (sumidero de las pérdidas) [K]
- `ρ` — densidad del fluido [kg/m³]
- `cp` — calor específico [J/kg·K]

> **Nota de diseño:** El término `U_loss · a_s` puede agruparse en un único parámetro escalar `h_loss = U_loss · (4/d_t)` [W/m³·K] para simplificar la implementación. Si `h_loss = 0` el reactor es perfectamente aislado.

**Forma compacta con `h_loss`:**

```
ρ·cp · ∂T/∂t = -ρ·cp·u · ∂T/∂z + (-ΔHr)·(-rA) - h_loss·(T - T_amb)
```

### 2.3 Cinética de reacción (Arrhenius)

```
k(T)   = k0 · exp(-Ea / (R · T))
(-rA)  = k(T) · CA^n
```

Donde:
- `k0` — factor pre-exponencial [unidades dependen de orden n]
- `Ea` — energía de activación [J/mol]
- `R` — constante de gas ideal = 8.314 [J/mol·K]
- `n` — orden de reacción [-]

---

## 3. Condiciones de borde e iniciales

### Condiciones de borde (inlet, z = 0)

```
CA(0, t) = CA_in(t)      # concentración de entrada (controlable)
T(0, t)  = T_in(t)       # temperatura de entrada (impuesta por PID + HX)
```

> **Importante:** En un sistema hiperbólico puro (sin difusión axial), las condiciones de borde se aplican **solo en el inlet**. No hay condición en `z = L`. La salida es un resultado, no una condición.

### Condición inicial (t = 0)

```
CA(z, 0) = CA_ss(z)      # perfil de estado estacionario, o uniforme = CA_in_0
T(z, 0)  = T_ss(z)       # perfil SS, o uniforme = T_in_0
```

Para arranque desde reposo usar perfiles uniformes:

```python
CA_init = np.full(N, params['CA_in'])
T_init  = np.full(N, params['T_in'])
```

---

## 4. Discretización espacial — método de líneas (MOL)

Se divide el reactor en `N` nodos igualmente espaciados:

```
dz = L / N
z_i = i · dz,    i = 0, 1, ..., N-1
```

Los términos convectivos se aproximan con **diferencias upwind de primer orden** (upwind obligatorio para sistemas hiperbólicos, garantiza estabilidad):

```
∂CA/∂z |_i  ≈  (CA[i] - CA[i-1]) / dz    para i = 1, ..., N-1
∂T/∂z  |_i  ≈  (T[i]  - T[i-1])  / dz    para i = 1, ..., N-1
```

Para el nodo inlet (`i = 0`) se usa el valor de borde directamente:

```
∂CA/∂z |_0  ≈  (CA[0] - CA_in) / dz
∂T/∂z  |_0  ≈  (T[0]  - T_in)  / dz
```

Esto transforma el sistema de PDEs en un sistema de `2·N` ODEs en el tiempo:

```
dCA[i]/dt = -u · (CA[i] - CA[i-1]) / dz  -  rA[i]
dT[i]/dt  = -u · (T[i]  - T[i-1])  / dz
            + (-dHr) · rA[i] / (rho · cp)
            - h_loss · (T[i] - T_amb) / (rho · cp)
```

Con `CA[-1] ≡ CA_in` y `T[-1] ≡ T_in` para el nodo 0.

---

## 5. Integración temporal

### Método recomendado

Usar `scipy.integrate.solve_ivp` con método `Radau` (A-estable, apto para sistemas stiff). La cinética Arrhenius puede hacer el sistema stiff cuando `Ea/RT >> 1`.

### Integración por segmentos (para cambios de parámetros en tiempo real)

Cuando el usuario modifica un parámetro (`CA_in`, `T_in`, `u`, etc.), **no se reinicia la simulación**. Se preserva el estado actual `y(t)` como condición inicial del siguiente segmento:

```
Segmento k:  solve_ivp( rhs, [t_k, t_k + Δt], y_k, params=params_k )
             → y_{k+1} = sol.y[:, -1]

Segmento k+1: solve_ivp( rhs, [t_{k+1}, t_{k+1} + Δt], y_{k+1}, params=params_{k+1} )
```

Esto es físicamente correcto: los perfiles espaciales internos del reactor evolucionan causalmente desde el estado previo.

### Criterio CFL (referencia para integrador explícito)

Si se usa un integrador explícito liviano en lugar de Radau, debe cumplirse:

```
CFL = u · Δt / Δz ≤ 1
→  Δt_max = Δz / u = (L/N) / u
```

Con `Radau` el solver maneja el paso internamente y no hay restricción CFL.

---

## 6. Implementación de referencia (`pfr_rhs`)

```python
import numpy as np

def pfr_rhs(t, y, params):
    N      = params['N']
    CA     = y[:N]
    T      = y[N:]

    u      = params['u']          # velocidad [m/s]
    dz     = params['L'] / N      # paso espacial [m]
    CA_in  = params['CA_in']      # concentración inlet [mol/m³]  ← cambiable
    T_in   = params['T_in']       # temperatura inlet [K]         ← impuesta por PID
    T_amb  = params['T_amb']      # temperatura ambiente [K]
    h_loss = params['h_loss']     # coef. pérdidas globales [W/m³·K]
    k0     = params['k0']
    Ea     = params['Ea']
    R      = 8.314
    dHr    = params['dHr']        # calor de reacción [J/mol]
    rho    = params['rho']        # densidad [kg/m³]
    cp     = params['cp']         # calor específico [J/kg·K]
    n      = params['n']          # orden de reacción

    # Cinética
    k   = k0 * np.exp(-Ea / (R * T))
    rA  = k * np.maximum(CA, 0.0) ** n   # np.maximum evita CA negativo por error numérico

    # Gradientes espaciales — upwind
    dCA_dz = np.empty(N)
    dT_dz  = np.empty(N)

    dCA_dz[0] = (CA[0] - CA_in) / dz
    dT_dz[0]  = (T[0]  - T_in)  / dz

    dCA_dz[1:] = (CA[1:] - CA[:-1]) / dz
    dT_dz[1:]  = (T[1:]  - T[:-1])  / dz

    # ODEs
    dCA_dt = -u * dCA_dz - rA
    dT_dt  = (-u * dT_dz
              + (-dHr) * rA / (rho * cp)
              - h_loss * (T - T_amb) / (rho * cp))

    return np.concatenate([dCA_dt, dT_dt])
```

### Clase simulador

```python
from scipy.integrate import solve_ivp

class PFRSimulator:
    def __init__(self, params):
        self.params = params.copy()
        N = params['N']
        self.state = np.concatenate([
            np.full(N, params['CA_in']),
            np.full(N, params['T_in'])
        ])
        self.t = 0.0

    def step(self, dt_sim: float) -> dict:
        """Avanza dt_sim segundos de tiempo de proceso."""
        sol = solve_ivp(
            pfr_rhs,
            [self.t, self.t + dt_sim],
            self.state,
            args=(self.params,),
            method='Radau',
            rtol=1e-4,
            atol=1e-6,
        )
        self.state = sol.y[:, -1]
        self.t += dt_sim
        return self._build_output()

    def update_params(self, updates: dict):
        """Actualiza parámetros sin reiniciar el estado interno."""
        self.params.update(updates)

    def _build_output(self) -> dict:
        N  = self.params['N']
        CA = self.state[:N]
        T  = self.state[N:]
        CA_in = self.params['CA_in']
        return {
            't':          self.t,
            'z':          np.linspace(0, self.params['L'], N).tolist(),
            'CA_profile': CA.tolist(),
            'T_profile':  T.tolist(),
            'CA_out':     float(CA[-1]),
            'T_out':      float(T[-1]),
            'X_out':      float(1.0 - CA[-1] / CA_in) if CA_in > 0 else 0.0,
        }
```

---

## 7. Parámetros del modelo

| Parámetro | Símbolo | Unidad | Descripción | Modificable en RT |
|---|---|---|---|---|
| `N` | — | — | Número de nodos espaciales (recomendado 50–100) | No |
| `L` | L | m | Largo del reactor | No |
| `u` | u | m/s | Velocidad superficial del fluido | Sí |
| `CA_in` | C_A,in | mol/m³ | Concentración de A en la entrada | Sí |
| `T_in` | T_in | K | Temperatura de entrada (salida del HX/PID) | Sí (via PID) |
| `T_amb` | T_amb | K | Temperatura ambiente (referencia pérdidas) | No |
| `h_loss` | h_loss | W/m³·K | Coef. global de pérdidas `= U_loss · 4/d_t` | Sí |
| `k0` | k₀ | [variable] | Factor pre-exponencial de Arrhenius | No |
| `Ea` | Ea | J/mol | Energía de activación | No |
| `dHr` | ΔHr | J/mol | Calor de reacción (< 0 exotérmica) | No |
| `rho` | ρ | kg/m³ | Densidad del fluido | No |
| `cp` | cp | J/kg·K | Calor específico del fluido | No |
| `n` | n | — | Orden de reacción | No |

---

## 8. Comportamiento físico esperado

### Tiempo de residencia

```
τ = L / u   [s]
```

Un cambio en `T_in` o `CA_in` tarda exactamente `τ` segundos en manifestarse en la salida `z = L`. Este retardo es un comportamiento físicamente correcto y debe ser visible en la UI.

### Efecto de `h_loss`

- `h_loss = 0` → reactor perfectamente aislado, la temperatura solo evoluciona por reacción y convección.
- `h_loss > 0` → el perfil de temperatura tiende asintóticamente a `T_amb` a lo largo de `z` en ausencia de reacción. Para reacción exotérmica, `h_loss` atenúa el hot spot.

### Régimen isotérmico aproximado

Si se quiere operar en régimen cuasi-isotérmico, la condición es:

```
|(-ΔHr) · (-rA)| << h_loss · (T - T_amb)    para todo z
```

La temperatura de entrada `T_in` controlada por el PID puede compensar las pérdidas para mantener un perfil aproximadamente plano.

---

## 9. Notas para la integración con la aplicación existente

1. **La función `pfr_rhs` reemplaza completamente al RHS actual.** Verificar que el vector de estado `y` mantiene la convención `[CA_0..N, T_0..N]`.

2. **El parámetro `T_in`** debe ser actualizado en cada tick de simulación con el valor entregado por el controlador PID externo, llamando a `sim.update_params({'T_in': valor_pid})` antes de `sim.step(dt)`.

3. **`h_loss = 0` reproduce el caso perfectamente aislado** sin ningún cambio de código adicional.

4. **Estabilidad numérica:** Si se observan oscilaciones en los perfiles, reducir `rtol`/`atol` de `solve_ivp` o aumentar `N`. No usar diferencias centrales en la dirección `z` — solo upwind.

5. **El perfil de temperatura interno `T_profile`** es válido aunque la operación sea nominalmente isotérmica: mostrará cómo se propaga el frente térmico cuando `T_in` cambia, lo que es útil para validar el modelo visualmente.
