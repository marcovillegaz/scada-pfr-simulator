"""
Reactor state module

Defines state variables for reactors (concentration, temperature, pressure, etc.)
Separates the physical state from dynamics and control
"""

import numpy as np


class ReactorState:
    """
    Represents the physical state of a reactor at a given time
    
    State variables include:
    - Concentration profile C(z,t) or discretized Ci(t)
    - Temperature T(t)
    - Pressure P(t)
    - Flow rate F(t)
    """
    
    def __init__(self, n_species=1, n_spatial_points=1):
        """
        Initialize reactor state
        
        Parameters:
            n_species: Number of chemical species
            n_spatial_points: Number of spatial discretization points (1 for CSTR, >1 for PFR)
        """
        self.n_species = n_species
        self.n_spatial_points = n_spatial_points
        
        # State variables
        self.concentration = np.zeros((n_species, n_spatial_points))
        self.temperature = 298.15  # K (default ambient)
        self.pressure = 101325.0  # Pa (default atmospheric)
        self.flow_rate = 0.0  # m³/s
        
        # Time
        self.time = 0.0
    
    def get_concentration(self, species_idx=0, position_idx=0):
        """Get concentration of a species at a position"""
        return self.concentration[species_idx, position_idx]
    
    def set_concentration(self, value, species_idx=0, position_idx=0):
        """Set concentration of a species at a position"""
        self.concentration[species_idx, position_idx] = value
    
    def get_outlet_concentration(self, species_idx=0):
        """Get outlet concentration (last spatial point)"""
        return self.concentration[species_idx, -1]
    
    def get_average_concentration(self, species_idx=0):
        """Get spatially averaged concentration"""
        return np.mean(self.concentration[species_idx, :])
    
    def copy(self):
        """Create a deep copy of the state"""
        new_state = ReactorState(self.n_species, self.n_spatial_points)
        new_state.concentration = self.concentration.copy()
        new_state.temperature = self.temperature
        new_state.pressure = self.pressure
        new_state.flow_rate = self.flow_rate
        new_state.time = self.time
        return new_state
    
    def __repr__(self):
        return (f"ReactorState(T={self.temperature:.2f} K, "
                f"P={self.pressure:.2f} Pa, "
                f"F={self.flow_rate:.4f} m³/s, "
                f"t={self.time:.2f} s)")
