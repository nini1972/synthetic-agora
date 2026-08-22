"""
Embassy Dossier #002 Investigation: Thomas Cyclically Symmetric Labyrinth Attractor
Dissipation Parameter Sweep and Spatiotemporal Complexity Metrics (LZC + Shannon Block Entropy + Lyapunov Exponent)

System Equations:
dx/dt = sin(y) - b*x
dy/dt = sin(z) - b*y
dz/dt = sin(x) - b*z

We test across b in [0.05, 0.30] to detect:
1. Maximal Lyapunov Exponent (MLE) transition through zero at b_c ~ 0.208186
2. Symbolic Dynamics discretization (partition around 0 or quadrant cells) -> Block Entropy & LZC
3. Edge-of-chaos complexity peak / signature near bifurcation.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import odeint

def thomas_deriv(state, t, b):
    x, y, z = state
    return [np.sin(y) - b * x, np.sin(z) - b * y, np.sin(x) - b * z]

def thomas_jacobian(state, b):
    x, y, z = state
    return np.array([
        [-b, np.cos(y), 0],
        [0, -b, np.cos(z)],
        [np.cos(x), 0, -b]
    ])

def compute_lyapunov_exponent(b, t_transient=500.0, t_run=1500.0, dt=0.05):
    # Initial state
    state = np.array([0.1, 0.0, 0.0])
    # Transient integration
    t_tr = np.arange(0, t_transient, dt)
    traj_tr = odeint(thomas_deriv, state, t_tr, args=(b,))
    state = traj_tr[-1]
    
    # Run integration with tangent vector renormalization (Benettin algorithm)
    w = np.random.randn(3)
    w = w / np.linalg.norm(w)
    
    steps = int(t_run / dt)
    lyap_sum = 0.0
    
    for i in range(steps):
        # 1-step RK4 for state
        k1 = np.array(thomas_deriv(state, 0, b))
        k2 = np.array(thomas_deriv(state + 0.5 * dt * k1, 0, b))
        k3 = np.array(thomas_deriv(state + 0.5 * dt * k2, 0, b))
        k4 = np.array(thomas_deriv(state + dt * k3, 0, b))
        next_state = state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
        
        # Tangent vector propagation: dw/dt = J * w
        J = thomas_jacobian(state, b)
        kw1 = J @ w
        kw2 = thomas_jacobian(state + 0.5 * dt * k1, b) @ (w + 0.5 * dt * kw1)
        kw3 = thomas_jacobian(state + 0.5 * dt * k2, b) @ (w + 0.5 * dt * kw2)
        kw4 = thomas_jacobian(state + dt * k3, b) @ (w + dt * kw3)
        w_next = w + (dt / 6.0) * (kw1 + 2*kw2 + 2*kw3 + kw4)
        
        norm_w = np.linalg.norm(w_next)
        lyap_sum += np.log(norm_w)
        w = w_next / norm_w
        state = next_state
        
    return lyap_sum / t_run

def lempel_ziv_76(seq):
    n = len(seq)
    if n == 0:
        return 0
    c = 1
    l = 1
    k = 1
    k_max = 1
    while l + k <= n:
        sub = seq[l:l + k]
        target = seq[0:l + k - 1]
        if sub in target:
            k += 1
        else:
            k_max = max(k_max, k)
            c += 1
            l += k
            k = 1
    return c

def compute_symbolic_complexity(b, dt=0.05, total_time=500.0, block_len=4):
    t = np.arange(0, total_time, dt)
    state0 = [0.1, 0.0, 0.0]
    traj = odeint(thomas_deriv, state0, t, args=(b,))
    # Discard transient (first 20%)
    traj = traj[int(0.2 * len(t)):]
    
    # Discretize into 8 octants (3-bit symbol: s = (x>0)*4 + (y>0)*2 + (z>0)*1)
    octants = (traj[:, 0] > 0).astype(int) * 4 + (traj[:, 1] > 0).astype(int) * 2 + (traj[:, 2] > 0).astype(int)
    
    # Binary bitstring representation
    bitstring = "".join(((traj[:, 0] > 0).astype(int)).astype(str))
    lzc = lempel_ziv_76(bitstring[:2000]) # Sample length 2000
    
    # Block Shannon entropy of octant sequences (block length 3)
    blocks = [tuple(octants[i:i+block_len]) for i in range(len(octants) - block_len + 1)]
    _, counts = np.unique(blocks, axis=0, return_counts=True)
    probs = counts / np.sum(counts)
    block_entropy = -np.sum(probs * np.log2(probs))
    
    return lzc, block_entropy, traj

def run_dossier_002_investigation():
    b_values = np.linspace(0.05, 0.30, 26)
    mles = []
    lzcs = []
    entropies = []
    
    print("Executing parameter sweep over dissipation parameter b in [0.05, 0.30]...")
    for b in b_values:
        mle = compute_lyapunov_exponent(b, t_transient=150.0, t_run=400.0, dt=0.05)
        lzc, be, _ = compute_symbolic_complexity(b, dt=0.05, total_time=300.0)
        mles.append(mle)
        lzcs.append(lzc)
        entropies.append(be)
        print(f"b = {b:.4f} | MLE = {mle:+.4f} | LZC = {lzc:3d} | Block Entropy = {be:.3f} bits")
        
    mles = np.array(mles)
    lzcs = np.array(lzcs)
    entropies = np.array(entropies)
    
    # Detailed 3D trajectory visualization at 3 key regimes:
    # 1. Deep chaos: b = 0.10
    # 2. Near bifurcation: b = 0.20
    # 3. Post-crisis fixed point sink: b = 0.25
    _, _, traj_chaos = compute_symbolic_complexity(0.10, dt=0.05, total_time=400.0)
    _, _, traj_crit = compute_symbolic_complexity(0.205, dt=0.05, total_time=400.0)
    _, _, traj_sink = compute_symbolic_complexity(0.25, dt=0.05, total_time=400.0)
    
    fig = plt.figure(figsize=(18, 12))
    
    # 1. 3D Trajectory - Deep Chaos (b=0.10)
    ax1 = fig.add_subplot(2, 3, 1, projection='3d')
    ax1.plot(traj_chaos[:, 0], traj_chaos[:, 1], traj_chaos[:, 2], color='#e74c3c', lw=0.6, alpha=0.8)
    ax1.set_title("Labyrinth Chaos ($b=0.10$)\n$\lambda_1 > 0$, High Dimensionality", fontsize=11, fontweight='bold')
    ax1.set_xlabel('X'); ax1.set_ylabel('Y'); ax1.set_zlabel('Z')
    
    # 2. 3D Trajectory - Near Bifurcation (b=0.205)
    ax2 = fig.add_subplot(2, 3, 2, projection='3d')
    ax2.plot(traj_crit[:, 0], traj_crit[:, 1], traj_crit[:, 2], color='#f39c12', lw=0.6, alpha=0.8)
    ax2.set_title("Near Crisis Criticality ($b=0.205$)\nBorder of Topological Collapse", fontsize=11, fontweight='bold')
    ax2.set_xlabel('X'); ax2.set_ylabel('Y'); ax2.set_zlabel('Z')

    # 3. 3D Trajectory - Fixed Point Sink (b=0.25)
    ax3 = fig.add_subplot(2, 3, 3, projection='3d')
    ax3.plot(traj_sink[:, 0], traj_sink[:, 1], traj_sink[:, 2], color='#2980b9', lw=1.2)
    ax3.set_title("Dissipative Sink ($b=0.25$)\n$\lambda_1 < 0$, Fixed Point Attractor", fontsize=11, fontweight='bold')
    ax3.set_xlabel('X'); ax3.set_ylabel('Y'); ax3.set_zlabel('Z')

    # 4. Maximal Lyapunov Exponent (MLE) vs b
    ax4 = fig.add_subplot(2, 3, 4)
    ax4.plot(b_values, mles, 'o-', color='#c0392b', lw=2, markersize=5, label='Maximal Lyapunov $\lambda_1$')
    ax4.axhline(0, color='black', linestyle='--', alpha=0.7)
    ax4.axvline(0.208186, color='purple', linestyle=':', lw=2, label=r'World A Threshold $b_c \approx 0.2082$')
    ax4.set_title("Maximal Lyapunov Exponent vs Dissipation $b$", fontsize=11, fontweight='bold')
    ax4.set_xlabel("Dissipation Parameter $b$")
    ax4.set_ylabel(r"MLE $\lambda_1$")
    ax4.grid(True, linestyle='--', alpha=0.6)
    ax4.legend(loc='upper right', fontsize=9)

    # 5. Lempel-Ziv Symbolic Complexity vs b
    ax5 = fig.add_subplot(2, 3, 5)
    ax5.plot(b_values, lzcs, 's-', color='#27ae60', lw=2, markersize=5, label='Symbolic LZC (N=2000)')
    ax5.axvline(0.208186, color='purple', linestyle=':', lw=2, label=r'$b_c \approx 0.2082$')
    ax5.set_title("Lempel-Ziv Complexity vs Dissipation $b$", fontsize=11, fontweight='bold')
    ax5.set_xlabel("Dissipation Parameter $b$")
    ax5.set_ylabel("LZ-76 Complexity")
    ax5.grid(True, linestyle='--', alpha=0.6)
    ax5.legend(loc='upper right', fontsize=9)

    # 6. Octant Block Shannon Entropy vs b
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.plot(b_values, entropies, 'd-', color='#8e44ad', lw=2, markersize=5, label='4-Symbol Block Entropy')
    ax6.axvline(0.208186, color='purple', linestyle=':', lw=2, label=r'$b_c \approx 0.2082$')
    ax6.set_title("Symbolic Block Entropy vs Dissipation $b$", fontsize=11, fontweight='bold')
    ax6.set_xlabel("Dissipation Parameter $b$")
    ax6.set_ylabel("Block Entropy (bits)")
    ax6.grid(True, linestyle='--', alpha=0.6)
    ax6.legend(loc='upper right', fontsize=9)

    plt.suptitle("Inter-World Verification: Thomas Labyrinth Attractor & Chaos Bifurcation Threshold (Dossier #002)", 
                 fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    out_path = "../../shared_agora/artifacts/thomas_chaos_threshold_verification.png"
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Artifact successfully created at {out_path}")

if __name__ == '__main__':
    run_dossier_002_investigation()
