"""
Dynamic PFR model — Method of Lines (MOL) with upwind finite differences.

Reaction: A + B -> Products   r = k(T) * CA * CB   (bimolecular, 2nd order)

State vector: y = [CA_0..CA_{N-1}, CB_0..CB_{N-1}, T_0..T_{N-1}]

SI units throughout:
    CA, CB  mol/m3
    T       K
    u       m/s
    L       m
    rho     kg/m3
    cp      J/(kg.K)
    dHr     J/mol   (negative = exothermic)
    h_loss  W/(m3.K)
    k0      m3/(mol.s)
    Ea      J/mol
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp

R_GAS = 8.314  # J/(mol.K)


def _upwind(field: np.ndarray, field_in: float, dz: float) -> np.ndarray:
    grad = np.empty_like(field)
    grad[0]  = (field[0]  - field_in)  / dz
    grad[1:] = (field[1:] - field[:-1]) / dz
    return grad


def pfr_rhs(t: float, y: np.ndarray, params: dict) -> np.ndarray:
    N  = params['N']
    CA = y[:N]
    CB = y[N:2*N]
    T  = y[2*N:]

    u      = params['u']
    dz     = params['L'] / N
    CA_in  = params['CA_in']
    CB_in  = params['CB_in']
    T_in   = params['T_in']
    T_amb  = params['T_amb']
    h_loss = params['h_loss']
    k0     = params['k0']
    Ea     = params['Ea']
    dHr    = params['dHr']
    rho    = params['rho']
    cp     = params['cp']

    # Arrhenius + bimolecular rate
    k  = k0 * np.exp(-Ea / (R_GAS * T))
    rA = k * np.maximum(CA, 0.0) * np.maximum(CB, 0.0)

    dCA_dt = -u * _upwind(CA, CA_in, dz) - rA
    dCB_dt = -u * _upwind(CB, CB_in, dz) - rA
    dT_dt  = (-u * _upwind(T, T_in, dz)
               + (-dHr) * rA / (rho * cp)
               - h_loss * (T - T_amb) / (rho * cp))

    return np.concatenate([dCA_dt, dCB_dt, dT_dt])


class PFRSimulator:
    """
    Integrates the PFR PDE system forward in time using solve_ivp (RK45).
    Params (especially T_in, CA_in, CB_in, u) can be updated mid-run.
    """

    def __init__(self, params: dict):
        self.params = params.copy()
        self._reset_state()
        self.t = 0.0

    def step(self, dt_sim: float) -> dict:
        sol = solve_ivp(
            pfr_rhs,
            [self.t, self.t + dt_sim],
            self.state,
            args=(self.params,),
            method='RK45',
            rtol=1e-4,
            atol=1e-6,
        )
        self.state = sol.y[:, -1]
        self.t    += dt_sim
        return self._build_output()

    def update_params(self, updates: dict) -> None:
        self.params.update(updates)

    def reset(self, params: dict | None = None) -> None:
        if params is not None:
            self.params = params.copy()
        self._reset_state()
        self.t = 0.0

    def _reset_state(self) -> None:
        N = self.params['N']
        self.state = np.concatenate([
            np.full(N, self.params['CA_in']),
            np.full(N, self.params['CB_in']),
            np.full(N, self.params['T_in']),
        ])

    def _build_output(self) -> dict:
        N     = self.params['N']
        CA    = self.state[:N]
        CB    = self.state[N:2*N]
        T     = self.state[2*N:]
        CA_in = self.params['CA_in']
        return {
            't':          self.t,
            'CA_profile': CA.tolist(),
            'CB_profile': CB.tolist(),
            'T_profile':  T.tolist(),
            'CA_out':     float(CA[-1]),
            'CB_out':     float(CB[-1]),
            'T_out':      float(T[-1]),
            'X_out':      float(1.0 - CA[-1] / CA_in) if CA_in > 0 else 0.0,
        }
