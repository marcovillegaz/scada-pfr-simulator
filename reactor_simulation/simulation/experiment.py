"""
Experiment orchestration module

Manages the time loop, integration, and data collection
This is the "lab bench" that coordinates all components
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Callable, List, Dict, Any


class Experiment:
    """
    Experiment orchestrator for reactor simulations

    Responsibilities:
    - Advance time with specified integration scheme
    - Apply perturbations at scheduled times
    - Log data from all components
    - Coordinate reactor, actuators, controllers, and sensors
    """

    def __init__(
        self,
        time_step=0.1,  # seconds
        total_time=100.0,  # seconds
        integration_method='euler',  # 'euler', 'rk4', etc.
    ):
        """
        Initialize experiment

        Parameters:
            time_step: Time step for integration (s)
            total_time: Total simulation time (s)
            integration_method: Numerical integration method
        """
        self.time_step = time_step
        self.total_time = total_time
        self.integration_method = integration_method

        # Time state
        self.current_time = 0.0
        self.time_history = []

        # Data logging
        self.data_log = []
        self.log_columns = []

        # Perturbations (scheduled interventions)
        self.perturbations = []

    def add_perturbation(self, perturbation):
        """
        Add a perturbation to the experiment

        Parameters:
            perturbation: Perturbation object (Step, Ramp, Sinusoidal, etc.)
        """
        self.perturbations.append(perturbation)

    def log_data(self, data_dict):
        """
        Log data at current time step

        Parameters:
            data_dict: Dictionary of variable names and values to log
        """
        data_dict['time'] = self.current_time
        self.data_log.append(data_dict)

    def get_data_frame(self):
        """
        Get logged data as pandas DataFrame

        Returns:
            df: DataFrame with all logged data
        """
        if len(self.data_log) == 0:
            return pd.DataFrame()

        return pd.DataFrame(self.data_log)

    def reset(self):
        """Reset experiment to initial state"""
        self.current_time = 0.0
        self.time_history = []
        self.data_log = []

    def run(
        self,
        update_function: Callable,
        log_function: Callable = None,
        verbose=False
    ):
        """
        Run the experiment

        Parameters:
            update_function: Function to call each time step: update_function(t, dt) -> None
            log_function: Optional function to call for data logging: log_function(t) -> dict
            verbose: Print progress messages

        Returns:
            df: DataFrame with logged data
        """
        self.reset()

        num_steps = int(self.total_time / self.time_step)

        if verbose:
            print(f"Starting experiment: {self.total_time} s, dt={self.time_step} s, {num_steps} steps")

        for step in range(num_steps):
            t = self.current_time
            dt = self.time_step

            # Apply perturbations
            for perturbation in self.perturbations:
                perturbation.apply(t)

            # Update system (user-provided dynamics)
            update_function(t, dt)

            # Log data if logging function provided
            if log_function is not None:
                data = log_function(t)
                self.log_data(data)

            # Advance time
            self.current_time += dt
            self.time_history.append(self.current_time)

            # Progress reporting
            if verbose and step % (num_steps // 10) == 0:
                progress = 100 * step / num_steps
                print(f"Progress: {progress:.1f}% (t={t:.2f} s)")

        if verbose:
            print(f"Experiment complete: {len(self.data_log)} data points collected")

        return self.get_data_frame()

    def __repr__(self):
        return (f"Experiment(dt={self.time_step} s, "
                f"T={self.total_time} s, "
                f"{len(self.perturbations)} perturbations)")
