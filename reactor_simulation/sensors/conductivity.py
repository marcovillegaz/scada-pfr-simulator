"""
Conductivity sensor module

Measures concentration via electrical conductivity with realistic imperfections
"""

import numpy as np


class ConductivitySensor:
    """
    Conductivity sensor for concentration measurement
    
    Features:
    - Nonlinear calibration curve (concentration -> conductivity)
    - Measurement noise
    - Temperature dependence (optional)
    - Drift over time (optional)
    
    Converts concentration to conductivity, which is what the sensor actually measures
    """
    
    def __init__(
        self,
        calibration_params=None,  # Parameters for C -> conductivity mapping
        noise_std=0.01,  # mS/cm (standard deviation of measurement noise)
        temperature_coefficient=0.02,  # 2% per °C (typical for conductivity)
        reference_temperature=298.15,  # K (calibration temperature)
        drift_rate=0.0,  # mS/cm per hour (sensor drift)
        seed=None,  # Random seed for reproducibility
    ):
        """
        Initialize conductivity sensor
        
        Parameters:
            calibration_params: Dict with 'a', 'b', 'c' for quadratic calibration
                               conductivity = a*C^2 + b*C + c
            noise_std: Standard deviation of measurement noise (mS/cm)
            temperature_coefficient: Temperature dependence (per K)
            reference_temperature: Reference temperature for calibration (K)
            drift_rate: Sensor drift over time (mS/cm per hour)
            seed: Random seed for noise generation
        """
        # Default linear calibration if not provided
        if calibration_params is None:
            self.calibration_params = {'a': 0.0, 'b': 1.0, 'c': 0.0}
        else:
            self.calibration_params = calibration_params
        
        self.noise_std = noise_std
        self.temperature_coefficient = temperature_coefficient
        self.reference_temperature = reference_temperature
        self.drift_rate = drift_rate
        
        # Random number generator
        self.rng = np.random.RandomState(seed)
        
        # Internal state
        self.accumulated_drift = 0.0
        self.total_time = 0.0  # hours
    
    def measure(self, true_concentration, temperature=None, dt=0.0):
        """
        Measure conductivity from concentration
        
        Parameters:
            true_concentration: Actual concentration (mol/L or other units)
            temperature: Current temperature (K), optional
            dt: Time step (s) for drift calculation
            
        Returns:
            measured_conductivity: Sensor reading (mS/cm)
        """
        C = true_concentration
        a = self.calibration_params['a']
        b = self.calibration_params['b']
        c = self.calibration_params['c']
        
        # Nonlinear calibration curve
        conductivity = a * C**2 + b * C + c
        
        # Temperature correction (if temperature provided)
        if temperature is not None:
            temp_correction = 1 + self.temperature_coefficient * (temperature - self.reference_temperature)
            conductivity *= temp_correction
        
        # Add drift (accumulates over time)
        if dt > 0:
            self.total_time += dt / 3600.0  # Convert to hours
            self.accumulated_drift = self.drift_rate * self.total_time
        
        conductivity += self.accumulated_drift
        
        # Add Gaussian noise
        noise = self.rng.normal(0, self.noise_std)
        conductivity_noisy = conductivity + noise
        
        # Conductivity cannot be negative
        conductivity_measured = max(0, conductivity_noisy)
        
        return conductivity_measured
    
    def concentration_from_conductivity(self, conductivity, temperature=None):
        """
        Inverse calibration: estimate concentration from conductivity reading
        
        This is what you'd use to interpret the sensor data
        Uses quadratic formula to invert the calibration curve
        
        Parameters:
            conductivity: Measured conductivity (mS/cm)
            temperature: Current temperature (K), optional
            
        Returns:
            estimated_concentration: Estimated concentration
        """
        # Remove temperature correction if provided
        if temperature is not None:
            temp_correction = 1 + self.temperature_coefficient * (temperature - self.reference_temperature)
            conductivity = conductivity / temp_correction
        
        # Remove drift
        conductivity = conductivity - self.accumulated_drift
        
        # Solve quadratic equation: a*C^2 + b*C + (c - conductivity) = 0
        a = self.calibration_params['a']
        b = self.calibration_params['b']
        c_offset = self.calibration_params['c'] - conductivity
        
        if abs(a) < 1e-10:
            # Linear case: b*C + c_offset = 0
            if abs(b) < 1e-10:
                return 0.0
            return -c_offset / b
        else:
            # Quadratic case
            discriminant = b**2 - 4*a*c_offset
            if discriminant < 0:
                return 0.0  # No real solution
            
            C1 = (-b + np.sqrt(discriminant)) / (2*a)
            C2 = (-b - np.sqrt(discriminant)) / (2*a)
            
            # Return positive solution
            if C1 >= 0:
                return C1
            elif C2 >= 0:
                return C2
            else:
                return 0.0
    
    def reset(self):
        """Reset sensor drift"""
        self.accumulated_drift = 0.0
        self.total_time = 0.0
    
    def recalibrate(self, new_params=None):
        """Recalibrate sensor (update calibration parameters)"""
        if new_params is not None:
            self.calibration_params = new_params
        self.reset()
    
    def __repr__(self):
        return (f"ConductivitySensor(drift={self.accumulated_drift:.4f} mS/cm, "
                f"noise_std={self.noise_std:.3f} mS/cm)")
