"""
PID Controller module

Classical PID control with anti-windup
"""

import numpy as np


class PIDController:
    """
    PID (Proportional-Integral-Derivative) Controller
    
    Features:
    - Classic PID algorithm
    - Anti-windup (integral clamping)
    - Derivative filtering (optional)
    - Output saturation
    
    IMPORTANT: PID acts on measured values, not true values!
    """
    
    def __init__(
        self,
        Kp=1.0,  # Proportional gain
        Ki=0.1,  # Integral gain
        Kd=0.01,  # Derivative gain
        setpoint=0.0,  # Desired value
        output_min=0.0,  # Minimum output
        output_max=100.0,  # Maximum output
        derivative_filter_tau=0.0,  # Derivative filtering time constant
    ):
        """
        Initialize PID controller
        
        Parameters:
            Kp: Proportional gain
            Ki: Integral gain
            Kd: Derivative gain
            setpoint: Target setpoint
            output_min: Minimum controller output
            output_max: Maximum controller output
            derivative_filter_tau: Time constant for derivative filtering (0 = no filter)
        """
        # Gains
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        
        # Setpoint
        self.setpoint = setpoint
        
        # Output limits
        self.output_min = output_min
        self.output_max = output_max
        
        # Derivative filter
        self.derivative_filter_tau = derivative_filter_tau
        
        # Internal state
        self.integral = 0.0
        self.previous_error = 0.0
        self.filtered_derivative = 0.0
        self.output = 0.0
    
    def set_setpoint(self, setpoint):
        """Update controller setpoint"""
        self.setpoint = setpoint
    
    def set_gains(self, Kp=None, Ki=None, Kd=None):
        """Update controller gains"""
        if Kp is not None:
            self.Kp = Kp
        if Ki is not None:
            self.Ki = Ki
        if Kd is not None:
            self.Kd = Kd
    
    def update(self, measured_value, dt):
        """
        Update PID controller
        
        Parameters:
            measured_value: Current measured process variable (from sensor!)
            dt: Time step (s)
            
        Returns:
            output: Controller output (manipulated variable)
        """
        # Calculate error (setpoint - measured)
        error = self.setpoint - measured_value
        
        # Proportional term
        P = self.Kp * error
        
        # Integral term with anti-windup
        self.integral += error * dt
        I = self.Ki * self.integral
        
        # Derivative term with optional filtering
        if dt > 0:
            raw_derivative = (error - self.previous_error) / dt
            
            if self.derivative_filter_tau > 0:
                # First-order filter on derivative
                alpha = dt / (self.derivative_filter_tau + dt)
                self.filtered_derivative += alpha * (raw_derivative - self.filtered_derivative)
                D = self.Kd * self.filtered_derivative
            else:
                D = self.Kd * raw_derivative
        else:
            D = 0.0
        
        # Calculate output
        output = P + I + D
        
        # Apply saturation
        output_saturated = np.clip(output, self.output_min, self.output_max)
        
        # Anti-windup: back-calculate integral if saturated
        if output != output_saturated and self.Ki != 0:
            self.integral = (output_saturated - P - D) / self.Ki
        
        # Store for next iteration
        self.previous_error = error
        self.output = output_saturated
        
        return self.output
    
    def reset(self):
        """Reset controller state (useful when changing setpoints)"""
        self.integral = 0.0
        self.previous_error = 0.0
        self.filtered_derivative = 0.0
        self.output = 0.0
    
    def get_components(self):
        """Get individual P, I, D components (for debugging/tuning)"""
        P = self.Kp * (self.setpoint - self.previous_error)
        I = self.Ki * self.integral
        D = self.Kd * self.filtered_derivative
        return {"P": P, "I": I, "D": D}
    
    def __repr__(self):
        return (f"PIDController(Kp={self.Kp}, Ki={self.Ki}, Kd={self.Kd}, "
                f"setpoint={self.setpoint:.2f}, output={self.output:.2f})")
