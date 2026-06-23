"""
Thermocouple sensor module

Temperature measurement with realistic imperfections
"""

import numpy as np
from collections import deque


class Thermocouple:
    """
    Thermocouple temperature sensor with realistic characteristics
    
    Features:
    - Measurement noise (Gaussian)
    - Time delay (first-order lag)
    - Calibration bias
    - Measurement range limits
    """
    
    def __init__(
        self,
        noise_std=0.5,  # K (standard deviation of measurement noise)
        time_constant=2.0,  # seconds (thermal time constant)
        bias=0.0,  # K (calibration offset)
        min_temp=0.0,  # K (minimum measurable temperature)
        max_temp=500.0,  # K (maximum measurable temperature)
        seed=None,  # Random seed for reproducibility
    ):
        """
        Initialize thermocouple sensor
        
        Parameters:
            noise_std: Standard deviation of Gaussian noise (K)
            time_constant: First-order time constant for thermal lag (s)
            bias: Constant calibration offset (K)
            min_temp: Minimum measurable temperature (K)
            max_temp: Maximum measurable temperature (K)
            seed: Random seed for noise generation
        """
        self.noise_std = noise_std
        self.time_constant = time_constant
        self.bias = bias
        self.min_temp = min_temp
        self.max_temp = max_temp
        
        # Random number generator
        self.rng = np.random.RandomState(seed)
        
        # Internal state (sensor reading)
        self.reading = 298.15  # K (ambient initial)
    
    def measure(self, true_temperature, dt):
        """
        Measure temperature with realistic sensor characteristics
        
        Parameters:
            true_temperature: Actual temperature (K)
            dt: Time step since last measurement (s)
            
        Returns:
            measured_temperature: Sensor reading (K)
        """
        # First-order lag (thermal inertia)
        alpha = dt / (self.time_constant + dt)
        self.reading += alpha * (true_temperature - self.reading)
        
        # Add calibration bias
        reading_with_bias = self.reading + self.bias
        
        # Add Gaussian noise
        noise = self.rng.normal(0, self.noise_std)
        reading_noisy = reading_with_bias + noise
        
        # Apply measurement range limits
        reading_saturated = np.clip(reading_noisy, self.min_temp, self.max_temp)
        
        return reading_saturated
    
    def get_reading(self):
        """Get current sensor reading without updating (last measurement)"""
        return self.reading + self.bias
    
    def reset(self, initial_temp=298.15):
        """Reset sensor to initial state"""
        self.reading = initial_temp
    
    def calibrate(self, new_bias=0.0):
        """Recalibrate sensor (change bias)"""
        self.bias = new_bias
    
    def __repr__(self):
        return (f"Thermocouple(reading={self.reading:.2f} K, "
                f"bias={self.bias:.2f} K, "
                f"noise_std={self.noise_std:.2f} K)")
