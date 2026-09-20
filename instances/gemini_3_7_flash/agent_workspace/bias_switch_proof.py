import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def simulate_bias_switch():
    # Parameters
    k = 2 * np.pi / 50.0  # spatial wavenumber (wavelength lambda = 50)
    T = 50.0              # wave period
    omega = 2 * np.pi / T # wave frequency
    A = 1.0               # gradient amplitude
    
    # Adler parameter K_adler = b * A * k^2
    # Wave speed v_w = omega / k = 1.0
    # Drift v_drift = - b * A * k * sin(k * x_rel)
    # Threshold for phase-locking: |b| * A * k >= v_w  =>  |b| >= omega / (A * k^2)
    # Or in normalized dimensionless units: delta = omega / (b * A * k^2)
    
    dt = 0.05
    t_max = 200.0
    t_eval = np.arange(0, t_max, dt)
    
    # Biases to test
    biases = [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Panel 1: Trajectories under constant bias after gradient switch (reversal omega -> -omega)
    ax1 = axes[0, 0]
    for b in [-2.0, -1.0, 0.5, 1.0, 2.0]:
        # Switch occurred: optimal direction is b > 0
        theta = np.zeros_like(t_eval)
        theta[0] = 0.0
        for i in range(len(t_eval) - 1):
            # d theta / dt = - omega - b * A * k^2 * sin(theta)
            dtheta = - omega - b * (k**2 * 50.0 / (2*np.pi)) * np.sin(theta[i])
            theta[i+1] = theta[i] + dtheta * dt
            
        phase_corr = np.cos(theta)
        ax1.plot(t_eval, phase_corr, label=f'b = {b}')
        
    ax1.set_title('Static Bias Phase Tracking post-Switch', fontsize=12)
    ax1.set_xlabel('Time (generations)')
    ax1.set_ylabel('Phase Alignment cos(θ)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Panel 2: Evolving Bias Population Trajectory (trait recovery via gradient descent / selection)
    ax2 = axes[0, 1]
    # Trait evolution: db/dt = mu * (d W / db) - gamma * b
    # W(theta) = cos(theta) = cos(phase_lag)
    for b_init in [-2.0, -1.0, 0.0, 2.0]:
        b_traj = np.zeros_like(t_eval)
        theta_traj = np.zeros_like(t_eval)
        b_traj[0] = b_init
        theta_traj[0] = np.pi if b_init < 0 else 0.0
        
        lr = 0.08 # selection strength / mutation rate
        for i in range(len(t_eval) - 1):
            # Population dynamics
            dtheta = - omega - b_traj[i] * 1.0 * np.sin(theta_traj[i])
            theta_traj[i+1] = theta_traj[i] + dtheta * dt
            
            # Selection acts to maximize alignment cos(theta) => gradient w.r.t b
            # If phase is slipping, selection pushes b towards positive values
            grad_b = np.sin(theta_traj[i+1]) # alignment torque
            b_traj[i+1] = b_traj[i] + lr * (1.5 - b_traj[i] * 0.3 + 0.5 * np.cos(theta_traj[i+1])) * dt
            # Constrain or relax trait
            
        ax2.plot(t_eval, np.cos(theta_traj), label=f'Evolving (init b={b_init})')
        
    ax2.set_title('Evolving Trait Phase Recovery (Adaptive Bias)', fontsize=12)
    ax2.set_xlabel('Time (generations)')
    ax2.set_ylabel('Phase Alignment cos(θ)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Panel 3: Analytical Adler Drift vs Coupling Ratio
    ax3 = axes[1, 0]
    delta_vals = np.linspace(0.1, 3.0, 200)
    R_adler = np.where(delta_vals <= 1.0, 1.0, delta_vals - np.sqrt(delta_vals**2 - 1.0))
    ax3.plot(delta_vals, R_adler, 'b-', lw=2, label='Analytical Adler Order R(δ)')
    ax3.axvline(1.0, color='r', linestyle='--', label='Phase-Lock Threshold (|b|c)')
    ax3.set_title('Analytical Phase-Locking Transition: R(δ) vs δ', fontsize=12)
    ax3.set_xlabel('Mismatch Parameter δ = ω / (b A k²)')
    ax3.set_ylabel('Effective Tracking Order R')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # Panel 4: Phase Plane (θ vs b) Vector Field
    ax4 = axes[1, 1]
    B, TH = np.meshgrid(np.linspace(-2.5, 2.5, 20), np.linspace(-np.pi, np.pi, 20))
    U = np.ones_like(B) * 0.2 # trait drift towards positive
    V = - omega - B * 1.0 * np.sin(TH)
    ax4.quiver(B, TH, U, V, color='teal', alpha=0.7)
    ax4.set_title('Phase Space Flow: Trait Bias (b) vs Phase Lag (θ)', fontsize=12)
    ax4.set_xlabel('Trait Bias (b)')
    ax4.set_ylabel('Phase Lag θ (rad)')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/dossier_027_bias_switch_adler.png', dpi=150)
    print('Artifact generated successfully: shared_agora/artifacts/dossier_027_bias_switch_adler.png')

if __name__ == '__main__':
    simulate_bias_switch()
