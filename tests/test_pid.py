"""Tests for reactor_simulation.control.pid — PIDController."""

import pytest
from reactor_simulation import PIDController


@pytest.fixture
def pid():
    return PIDController(Kp=2.0, Ki=0.5, Kd=0.1, setpoint=100.0,
                         output_min=0.0, output_max=500.0)


class TestPIDController:
    def test_zero_error_gives_zero_output_initially(self, pid):
        out = pid.update(measured_value=100.0, dt=1.0)
        assert out == 0.0

    def test_positive_error_gives_positive_output(self, pid):
        """Setpoint=100, measured=80 → error=20 → positive output."""
        out = pid.update(measured_value=80.0, dt=1.0)
        assert out > 0

    def test_negative_error_gives_zero_output_when_clamped(self, pid):
        """Setpoint=100, measured=150 → error=-50 → output clipped to output_min=0."""
        out = pid.update(measured_value=150.0, dt=1.0)
        assert out == 0.0

    def test_output_respects_max_limit(self):
        pid = PIDController(Kp=1000.0, Ki=0.0, Kd=0.0,
                            setpoint=100.0, output_max=200.0)
        out = pid.update(measured_value=0.0, dt=1.0)
        assert out <= 200.0

    def test_output_respects_min_limit(self):
        pid = PIDController(Kp=1000.0, Ki=0.0, Kd=0.0,
                            setpoint=0.0, output_min=10.0, output_max=500.0)
        out = pid.update(measured_value=100.0, dt=1.0)
        assert out >= 10.0

    def test_integral_accumulates(self):
        """Persistent error should make integral term grow over time."""
        pid = PIDController(Kp=0.0, Ki=1.0, Kd=0.0,
                            setpoint=10.0, output_min=-1e6, output_max=1e6)
        out1 = pid.update(measured_value=0.0, dt=1.0)
        out2 = pid.update(measured_value=0.0, dt=1.0)
        assert out2 > out1  # integral grows → output grows

    def test_antiwindup_prevents_integral_explosion(self):
        """When output is saturated, integral should not keep growing unboundedly."""
        pid = PIDController(Kp=0.0, Ki=10.0, Kd=0.0,
                            setpoint=100.0, output_min=0.0, output_max=50.0)
        for _ in range(1000):
            pid.update(measured_value=0.0, dt=1.0)
        assert pid.integral < 1000  # without anti-windup it would be 100*1000=100000

    def test_derivative_opposes_fast_change(self):
        """Derivative term should resist a sudden measurement jump."""
        pid_d = PIDController(Kp=0.0, Ki=0.0, Kd=10.0,
                              setpoint=100.0, output_min=-1e6, output_max=1e6)
        pid_d.update(measured_value=90.0, dt=1.0)     # baseline
        out = pid_d.update(measured_value=70.0, dt=1.0)  # error increases → D positive
        assert out > 0

    def test_set_setpoint(self, pid):
        pid.set_setpoint(200.0)
        assert pid.setpoint == 200.0

    def test_set_gains(self, pid):
        pid.set_gains(Kp=5.0, Ki=None, Kd=0.5)
        assert pid.Kp == 5.0
        assert pid.Ki == 0.5   # unchanged
        assert pid.Kd == 0.5

    def test_reset_clears_state(self, pid):
        for _ in range(10):
            pid.update(measured_value=50.0, dt=1.0)
        pid.reset()
        assert pid.integral == 0.0
        assert pid.previous_error == 0.0
        assert pid.output == 0.0

    def test_get_components_keys(self, pid):
        pid.update(measured_value=80.0, dt=1.0)
        comp = pid.get_components()
        assert set(comp.keys()) == {"P", "I", "D"}

    def test_derivative_filter_smooths_derivative(self):
        """With filtering, the derivative should change less abruptly than without."""
        pid_no_filter   = PIDController(Kp=0, Ki=0, Kd=1,
                                        setpoint=0, output_min=-1e6, output_max=1e6,
                                        derivative_filter_tau=0.0)
        pid_with_filter = PIDController(Kp=0, Ki=0, Kd=1,
                                        setpoint=0, output_min=-1e6, output_max=1e6,
                                        derivative_filter_tau=5.0)
        # Step change in measurement
        out_raw      = abs(pid_no_filter.update(100.0, dt=1.0))
        out_filtered = abs(pid_with_filter.update(100.0, dt=1.0))
        assert out_filtered < out_raw  # filter dampens the derivative kick

    def test_controller_drives_to_setpoint(self):
        """PID acting on a simple first-order plant should converge."""
        pid = PIDController(Kp=2.0, Ki=1.0, Kd=0.0,
                            setpoint=1.0, output_min=-10.0, output_max=10.0)
        y = 0.0
        K, tau = 1.0, 2.0
        dt = 0.05
        for _ in range(500):
            u = pid.update(y, dt)
            y += ((-y + K * u) / tau) * dt
        assert abs(y - 1.0) < 0.05  # within 5% of setpoint
