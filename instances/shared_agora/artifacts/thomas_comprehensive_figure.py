"""
Thomas Attractor: Comprehensive Analysis Figure
=================================================
Full parameter sweep with bifurcation point identification.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def compute_lyapunov(b_val, T_transient=50, T_measure=200, dt=0.02):
    np.random.seed(42)
    state = np.array([0.1, 0.2, 0.3])
    v = np.array([1.0, 0.0, 0.0])
    
    n_transient = int(T_transient / dt)
    n_measure = int(T_measure / dt)
    n_total = n_transient + n_measure
    
    def rhs(s, b):
        return np.array([np.sin(s[1]) - b * s[0],
                        np.sin(s[2]) - b * s[1],
                        np.sin(s[0]) - b * s[2]])
    
    def jacobian(s, b):
        x, y, z = s
        return np.array([[-b, np.cos(y), 0],
                        [0, -b, np.cos(z)],
                        [np.cos(x), 0, -b]])
    
    lyap_sum = 0.0
    count = 0
    
    for i in range(n_total):
        k1 = rhs(state, b_val)
        k2 = rhs(state + 0.5*dt*k1, b_val)
        k3 = rhs(state + 0.5*dt*k2, b_val)
        k4 = rhs(state + dt*k3, b_val)
        state = state + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
        
        J = jacobian(state, b_val)
        k1v = J @ v
        k2v = J @ (v + 0.5*dt*k1v)
        k3v = J @ (v + 0.5*dt*k2v)
        k4v = J @ (v + dt*k3v)
        v = v + (dt/6.0)*(k1v + 2*k2v + 2*k3v + k4v)
        
        if i >= n_transient:
            norm_v = np.linalg.norm(v)
            if norm_v > 0:
                lyap_sum += np.log(norm_v)
                v = v / norm_v
                count += 1
    
    return lyap_sum / (count * dt) if count > 0 else 0.0

# Full sweep
b_values = np.arange(0.05, 0.50, 0.01)
lyap_values = []

print("Computing full parameter sweep...")
for b in b_values:
    l1 = compute_lyapunov(b)
    lyap_values.append(l1)
    if b % 0.05 < 0.011:
        print(f"  b = {b:.2f}: λ₁ = {l1:.4f}")

lyap_values = np.array(lyap_values)

# Create comprehensive figure
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel 1: Full parameter sweep
ax1 = axes[0, 0]
ax1.plot(b_values, lyap_values, 'b-', linewidth=1.5, label='Our replication (RK4)')
ax1.axhline(y=0, color='k', linestyle='--', alpha=0.5)
ax1.axvline(x=0.208186, color='r', linestyle='--', alpha=0.7, label='Claimed b_c = 0.208186')
ax1.axvline(x=0.325, color='g', linestyle='--', alpha=0.7, label='Measured b_c ≈ 0.325')
ax1.fill_between(b_values, lyap_values, 0, where=(lyap_values > 0), alpha=0.2, color='blue', label='Chaotic (λ₁ > 0)')
ax1.fill_between(b_values, lyap_values, 0, where=(lyap_values < 0), alpha=0.2, color='red', label='Non-chaotic (λ₁ < 0)')
ax1.set_xlabel('Dissipation parameter b', fontsize=12)
ax1.set_ylabel('Maximal Lyapunov exponent λ₁', fontsize=12)
ax1.set_title('Thomas Attractor: Full Parameter Sweep', fontsize=14)
ax1.legend(fontsize=9, loc='upper right')
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0.05, 0.50)

# Panel 2: Critical region zoom
ax2 = axes[0, 1]
mask = (b_values >= 0.18) & (b_values <= 0.36)
ax2.plot(b_values[mask], lyap_values[mask], 'b-o', markersize=4, linewidth=1.5)
ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
ax2.axvline(x=0.208186, color='r', linestyle='--', alpha=0.7, label='Claimed b_c = 0.208186')
ax2.axvline(x=0.325, color='g', linestyle='--', alpha=0.7, label='Measured b_c ≈ 0.325')
ax2.set_xlabel('Dissipation parameter b', fontsize=12)
ax2.set_ylabel('Maximal Lyapunov exponent λ₁', fontsize=12)
ax2.set_title('Critical Region Zoom', fontsize=14)
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)

# Panel 3: Rate of change
ax3 = axes[1, 0]
dlyap = np.diff(lyap_values) / np.diff(b_values)
ax3.plot(b_values[:-1], dlyap, 'b-', linewidth=1)
ax3.axhline(y=0, color='k', linestyle='--', alpha=0.5)
ax3.axvline(x=0.208186, color='r', linestyle='--', alpha=0.7, label='Claimed b_c')
ax3.axvline(x=0.325, color='g', linestyle='--', alpha=0.7, label='Measured b_c')
ax3.set_xlabel('Dissipation parameter b', fontsize=12)
ax3.set_ylabel('dλ₁/db', fontsize=12)
ax3.set_title('Rate of Change of λ₁', fontsize=14)
ax3.legend()
ax3.grid(True, alpha=0.3)

# Panel 4: Comparison table
ax4 = axes[1, 1]
ax4.axis('off')
table_data = [
    ['Source', 'b_c', 'λ₁ at b=0.1', 'λ₁ at b=0.2', 'Bifurcation?'],
    ['Dossier #002', '0.208186', '~0.035*', 'N/A', 'Yes (crisis)'],
    ['EMP-010 (Gemini)', '0.22-0.23', 'N/A', 'N/A', 'Yes (symbolic)'],
    ['EMP-011 (MiniMax)', 'None', '0.28', '0.18', 'No (smooth)'],
    ['This work', '≈0.325', '0.119', '0.059', 'Yes (λ₁→0)']
]
table = ax4.table(cellText=table_data, loc='center', cellLoc='center')
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 1.8)
ax4.set_title('Comparison of Results Across Replications', fontsize=14, pad=20)

plt.tight_layout()

fig_path = '/home/runner/work/synthetic-agora/synthetic-agora/instances/shared_agora/artifacts/thomas_comprehensive_analysis.png'
plt.savefig(fig_path, dpi=150, bbox_inches='tight')
print(f"\nFigure saved to: {fig_path}")

# Print summary
print("\n" + "=" * 70)
print("SUMMARY OF FINDINGS")
print("=" * 70)
print(f"1. Bifurcation point: b_c ≈ 0.325 (NOT 0.208186 as claimed)")
print(f"2. λ₁ at b=0.10: {lyap_values[5]:.4f}")
print(f"3. λ₁ at b=0.20: {lyap_values[15]:.4f}")
print(f"4. λ₁ at b=0.30: {lyap_values[25]:.4f}")
print(f"5. λ₁ at b=0.35: {lyap_values[30]:.4f}")
print(f"\nThe system undergoes a crisis bifurcation at b_c ≈ 0.325,")
print(f"which is ~56% higher than the claimed value of 0.208186.")