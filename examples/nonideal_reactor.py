"""This code is an example of fitting experimental data to the models employed
to discribe nonideal reactor behavior. The models are highly non linear, so 
numerical methods should be employed. """

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from sklearn.metrics import mean_squared_error, r2_score


# Generar datos simulados (distribución normal con ruido)
def generate_experimental_data(theta_range, true_model, params, noise_std=0.05):
    np.random.seed(42)  # Para reproducibilidad
    theta = np.linspace(*theta_range, 50)  # 50 puntos en el rango definido
    true_values = true_model(theta, *params)  # Valores "reales" del modelo
    noise = np.random.normal(0, noise_std, size=theta.shape)  # Ruido aleatorio
    experimental_values = true_values + noise  # Agregar ruido
    return theta, experimental_values


# Modelo de dispersión
def dispersion_model_1(theta, phi):
    "this is de dispersion model for phi > 0.02"
    return (1 / np.sqrt(4 * np.pi * phi * theta)) * np.exp(
        -((1 - theta) ** 2) / (4 * phi * theta)
    )


def dispersion_model_2(theta, phi):
    "this is de dispersion model for phi < 0.02"
    return (1 / (2 * np.sqrt(phi))) * np.exp(-((1 - theta) ** 2) / (4 * phi))


# Modelo de tanques en serie
def tanks_in_series_model(theta, N):
    from scipy.special import gamma

    return N * (N * theta) ** (N - 1) * np.exp(-N * theta) / gamma(N)


# Parámetros verdaderos para generar los datos
phi_true = 0.1  # Parámetro del modelo de dispersión
N_true = 5  # Número de tanques en el modelo de tanques en serie

# Generar datos experimentales basados en el modelo de dispersión
theta_range = (0.1, 2)  # Rango de tiempo adimensional
noise_std = 0.02  # Desviación estándar del ruido

theta_exp, E_exp = generate_experimental_data(
    theta_range, dispersion_model_1, [phi_true], noise_std=noise_std
)

# AJUSTES DE LOS MODELOS
## Ajuste al modelo de dispersión 1
phi_opt_1, _ = curve_fit(dispersion_model_1, theta_exp, E_exp, p0=[0.1])
## Ajuste al modelo de dispersión 2
phi_opt_2, _ = curve_fit(dispersion_model_2, theta_exp, E_exp, p0=[0.05])
## Ajuste al modelo de tanques en serie
N_opt, _ = curve_fit(tanks_in_series_model, theta_exp, E_exp, p0=[3])

# PREDICCIÓN DE LOS MODELOS
theta_pred = np.linspace(*theta_range, 100)
E_disp1_pred = dispersion_model_1(theta_pred, phi_opt_1[0])
E_disp2_pred = dispersion_model_1(theta_pred, phi_opt_2[0])
E_tanks_pred = tanks_in_series_model(theta_pred, N_opt[0])

# CALCULO DE EVALUADORES ESTADISTICOS
## Cálculo del RMSE y R² para el modelo de dispersión1
E_disp_fitted_1 = dispersion_model_1(theta_exp, phi_opt_1[0])
rmse_disp_1 = np.sqrt(mean_squared_error(E_exp, E_disp_fitted_1))
r2_disp_1 = r2_score(E_exp, E_disp_fitted_1)

## Cálculo del RMSE y R² para el modelo de dispersión2
E_disp_fitted_2 = dispersion_model_2(theta_exp, phi_opt_2[0])
rmse_disp_2 = np.sqrt(mean_squared_error(E_exp, E_disp_fitted_2))
r2_disp_2 = r2_score(E_exp, E_disp_fitted_2)

## Cálculo del RMSE y R² para el modelo de tanques en serie
E_tanks_fitted = tanks_in_series_model(theta_exp, N_opt[0])
rmse_tanks = np.sqrt(mean_squared_error(E_exp, E_tanks_fitted))
r2_tanks = r2_score(E_exp, E_tanks_fitted)


# MOSTRA METRICAS DE LOS AJUSTES
print(
    f"Modelo de dispersión Φ>0.02: Φ={phi_opt_1[0]:.4f}, RMSE={rmse_disp_1:.4f}, R²={r2_disp_1:.4f}"
)
print(
    f"Modelo de dispersión Φ<0.02: Φ={phi_opt_2[0]:.4f}, RMSE={rmse_disp_2:.4f}, R²={r2_disp_2:.4f}"
)
print(
    f"Modelo de tanques en serie: N={N_opt[0]:.4f}, RMSE={rmse_tanks:.4f}, R²={r2_tanks:.4f}"
)

# GRAFICA DE RESULTADOS
plt.scatter(theta_exp, E_exp, label="Datos experimentales (con ruido)", marker=".")
plt.plot(theta_pred, E_disp1_pred, label=f"Dispersión Φ>0.02 (Φ={phi_opt_1[0]:.2f})")
plt.plot(theta_pred, E_disp2_pred, label=f"Dispersión Φ<0.02 (Φ={phi_opt_2[0]:.2f})")
plt.plot(theta_pred, E_tanks_pred, label=f"Tanques en serie (N={N_opt[0]:.2f})")
plt.xlabel("θ (Tiempo adimensional)")
plt.ylabel("E(θ)")
plt.legend()
plt.title("Ajuste de modelos a datos experimentales con ruido")
plt.show()
