"""
Perturbations module

Scheduled interventions for testing and identification:
- Step changes
- Ramp changes
- Sinusoidal variations
- Random noise

Perturbations modify setpoints or disturbances at specific times
"""

import numpy as np


class Perturbation:
    """Base class for perturbations"""
    
    def __init__(self, start_time=0.0):
        """
        Initialize perturbation
        
        Parameters:
            start_time: When to start the perturbation (s)
        """
        self.start_time = start_time
    
    def apply(self, current_time):
        """Apply perturbation at current time - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement apply()")


class StepPerturbation(Perturbation):
    """
    Step change perturbation
    
    Changes a variable from one value to another at a specific time
    """
    
    def __init__(
        self,
        target_object,  # Object whose attribute will be modified
        attribute_name,  # Name of attribute to modify
        initial_value,
        final_value,
        step_time,
    ):
        """
        Initialize step perturbation
        
        Parameters:
            target_object: Object to modify (e.g., pump, heater, controller)
            attribute_name: Name of attribute to change (e.g., 'flow_setpoint')
            initial_value: Value before step
            final_value: Value after step
            step_time: Time of step change (s)
        """
        super().__init__(start_time=step_time)
        self.target_object = target_object
        self.attribute_name = attribute_name
        self.initial_value = initial_value
        self.final_value = final_value
        self.step_time = step_time
        self.applied = False
        
        # Set initial value
        setattr(self.target_object, self.attribute_name, self.initial_value)
    
    def apply(self, current_time):
        """Apply step change at specified time"""
        if current_time >= self.step_time and not self.applied:
            setattr(self.target_object, self.attribute_name, self.final_value)
            self.applied = True


class RampPerturbation(Perturbation):
    """
    Ramp perturbation
    
    Linearly changes a variable over a specified duration
    """
    
    def __init__(
        self,
        target_object,
        attribute_name,
        start_value,
        end_value,
        start_time,
        duration,
    ):
        """
        Initialize ramp perturbation
        
        Parameters:
            target_object: Object to modify
            attribute_name: Name of attribute to change
            start_value: Value at start of ramp
            end_value: Value at end of ramp
            start_time: Time to start ramp (s)
            duration: Duration of ramp (s)
        """
        super().__init__(start_time=start_time)
        self.target_object = target_object
        self.attribute_name = attribute_name
        self.start_value = start_value
        self.end_value = end_value
        self.duration = duration
        self.end_time = start_time + duration
        
        # Set initial value
        setattr(self.target_object, self.attribute_name, self.start_value)
    
    def apply(self, current_time):
        """Apply ramp change"""
        if current_time < self.start_time:
            value = self.start_value
        elif current_time >= self.end_time:
            value = self.end_value
        else:
            # Linear interpolation
            fraction = (current_time - self.start_time) / self.duration
            value = self.start_value + fraction * (self.end_value - self.start_value)
        
        setattr(self.target_object, self.attribute_name, value)


class SinusoidalPerturbation(Perturbation):
    """
    Sinusoidal perturbation
    
    Adds sinusoidal variation around a mean value
    Useful for frequency response testing
    """
    
    def __init__(
        self,
        target_object,
        attribute_name,
        mean_value,
        amplitude,
        frequency,  # Hz
        start_time=0.0,
        phase=0.0,  # radians
    ):
        """
        Initialize sinusoidal perturbation
        
        Parameters:
            target_object: Object to modify
            attribute_name: Name of attribute to change
            mean_value: Mean value of oscillation
            amplitude: Amplitude of oscillation
            frequency: Frequency in Hz
            start_time: When to start oscillation (s)
            phase: Phase offset (radians)
        """
        super().__init__(start_time=start_time)
        self.target_object = target_object
        self.attribute_name = attribute_name
        self.mean_value = mean_value
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase = phase
    
    def apply(self, current_time):
        """Apply sinusoidal variation"""
        if current_time < self.start_time:
            value = self.mean_value
        else:
            omega = 2 * np.pi * self.frequency
            value = self.mean_value + self.amplitude * np.sin(omega * current_time + self.phase)
        
        setattr(self.target_object, self.attribute_name, value)
