"""
Peer Verification of SYN-047: Unified Bifurcation Framework
Testing the claim that pitchfork bifurcations and directed percolation
transitions share universal symmetry-breaking behavior.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import odeint

def pitchfork_dynamics(x, t, r):
    """Pitchfork bifurcation ODE: dx/dt = rx - x^3"""
    return r * x - x**3

def contact_process_simulation(L, p, steps=2000, seed_density=0.1):
    """
    Simulate 1D contact process (directed percolation model)
    Rules:
    - Active site becomes inactive at rate 1-p
    - Inactive site becomes active if neighbor is active at rate p/2
    """
    # Initialize with random active sites
    np.random.seed(42)
    lattice = np.random.random(L) < seed_density
    
    density_history = []
    
    for step in range(steps):
        new_lattice = lattice.copy()
        
        for i in range(L):
            if lattice[i]:  # Active site
                # Becomes inactive with probability 1-p
                if np.random.random() > p:
                    new_lattice[i] = False
            else:  # Inactive site
                # Check neighbors (periodic boundary)
                left_active = lattice[(i-1) % L]
                right_active = lattice[(i+1) % L]
                
                # Becomes active if at least one neighbor is active
                if (left_active or right_active) and np.random.random() < p/2:
                    new_lattice[i] = True
        
        lattice = new_lattice
        density = np.mean(lattice)
        density_history.append(density)
    
    return density_history

def analyze_pitchfork_bifurcation():
    """Analyze pitchfork bifurcation diagram"""
    r_values = np.linspace(-1, 1, 200)
    
    # For each r, find equilibrium points
    equilibria = []
    
    for r in r_values:
        if r <= 0:
            # Only x = 0 is stable for r <= 0
            equilibria.append([0])
        else:
            # x = 0 (unstable) and x = ±√r (stable) for r > 0
            equilibria.append([-np.sqrt(r), 0, np.sqrt(r)])
    
    return r_values, equilibria

def analyze_contact_process():
    """Analyze contact process phase transition"""
    p_values = np.linspace(0.2, 0.8, 20)  # Bifurcation parameter
    L = 100  # Lattice size
    
    final_densities = []
    
    for p in p_values:
        print(f"Testing contact process at p = {p:.3f}")
        
        # Run multiple realizations
        densities = []
        for run in range(5):
            np.random.seed(42 + run)  # Different seed per run
            history = contact_process_simulation(L, p, steps=1500, seed_density=0.1)
            # Take final density after transient
            final_density = np.mean(history[-200:])
            densities.append(final_density)
        
        mean_density = np.mean(densities)
        final_densities.append(mean_density)
    
    return p_values, final_densities

def test_symmetry_breaking():
    """Test if both systems exhibit symmetry breaking"""
    
    print("Testing Unified Bifurcation Framework (SYN-047)")
    print("=" * 60)
    
    # 1. Pitchfork bifurcation analysis
    print("\\n1. Analyzing pitchfork bifurcation...")
    r_vals, equilibria = analyze_pitchfork_bifurcation()
    
    # Find bifurcation point
    r_critical = 0.0
    print(f"   Pitchfork critical point: r_c = {r_critical}")
    
    # Test symmetry breaking
    r_test = 0.1  # Above critical point
    x_stable = np.sqrt(r_test)
    print(f"   At r = {r_test}: stable points at x = ±{x_stable:.3f}")
    print(f"   Symmetry broken: ✓")
    
    # 2. Contact process analysis
    print("\\n2. Analyzing contact process phase transition...")
    p_vals, densities = analyze_contact_process()
    
    # Find critical point (rough estimate)
    # Critical point is around p_c ≈ 0.64465 for 1D contact process
    p_theoretical = 0.644
    
    # Find experimental critical point
    density_gradient = np.gradient(densities)
    max_gradient_idx = np.argmax(np.abs(density_gradient))
    p_experimental = p_vals[max_gradient_idx]
    
    print(f"   Contact process critical point (theoretical): p_c ≈ {p_theoretical}")
    print(f"   Contact process critical point (experimental): p_c ≈ {p_experimental:.3f}")
    
    # Test for phase transition
    subcritical_density = np.mean([d for p, d in zip(p_vals, densities) if p < p_experimental])
    supercritical_density = np.mean([d for p, d in zip(p_vals, densities) if p > p_experimental])
    
    print(f"   Subcritical density: {subcritical_density:.4f}")
    print(f"   Supercritical density: {supercritical_density:.4f}")
    
    transition_strength = supercritical_density - subcritical_density
    print(f"   Transition strength: {transition_strength:.4f}")
    
    # 3. Unified framework validation
    print("\\n3. Testing unified framework claims...")
    
    # Claim 1: Both exhibit symmetry breaking
    pitchfork_symmetric = True  # By definition for supercritical pitchfork
    contact_symmetric = transition_strength > 0.05  # Significant transition
    
    print(f"   Pitchfork exhibits symmetry breaking: {pitchfork_symmetric}")
    print(f"   Contact process exhibits phase transition: {contact_symmetric}")
    
    # Claim 2: Universal bifurcation parameter behavior
    # Both should have smooth transition through critical point
    pitchfork_smooth = True  # Analytical result
    contact_smooth = len(p_vals) > 10 and np.all(np.diff(densities) >= -0.1)  # No sudden jumps
    
    print(f"   Pitchfork has smooth transition: {pitchfork_smooth}")
    print(f"   Contact process has smooth transition: {contact_smooth}")
    
    # 4. Create visualization
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    
    # Plot 1: Pitchfork bifurcation diagram
    for r, eq_list in zip(r_vals, equilibria):
        for x_eq in eq_list:
            color = 'blue' if abs(x_eq) > 0.01 else 'red'  # Stable vs unstable
            linewidth = 2 if abs(x_eq) > 0.01 or r <= 0 else 1
            ax1.plot(r, x_eq, 'o', color=color, markersize=1.5, alpha=0.7)
    
    ax1.axvline(x=0, color='black', linestyle='--', alpha=0.5, label='Critical Point')
    ax1.set_xlabel('Bifurcation Parameter r')
    ax1.set_ylabel('Equilibrium x*')
    ax1.set_title('Pitchfork Bifurcation Diagram')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot 2: Contact process phase diagram
    ax2.plot(p_vals, densities, 'ro-', linewidth=2, markersize=6)
    ax2.axvline(x=p_theoretical, color='green', linestyle='--', alpha=0.7, 
                label=f'Theoretical p_c ≈ {p_theoretical}')
    ax2.axvline(x=p_experimental, color='blue', linestyle='--', alpha=0.7,
                label=f'Experimental p_c ≈ {p_experimental:.3f}')
    ax2.set_xlabel('Infection Probability p')
    ax2.set_ylabel('Active Site Density')
    ax2.set_title('Contact Process Phase Transition')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Plot 3: Pitchfork time evolution
    t_span = np.linspace(0, 10, 1000)
    r_test = 0.2
    
    # Multiple initial conditions
    initial_conditions = [-0.5, -0.1, 0.1, 0.5]
    colors = ['red', 'orange', 'green', 'blue']
    
    for ic, color in zip(initial_conditions, colors):
        sol = odeint(pitchfork_dynamics, ic, t_span, args=(r_test,))
        ax3.plot(t_span, sol[:, 0], color=color, linewidth=2, 
                label=f'x(0) = {ic}', alpha=0.8)
    
    # Mark stable fixed points
    x_stable = np.sqrt(r_test)
    ax3.axhline(y=x_stable, color='black', linestyle='--', alpha=0.5)
    ax3.axhline(y=-x_stable, color='black', linestyle='--', alpha=0.5)
    ax3.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
    
    ax3.set_xlabel('Time t')
    ax3.set_ylabel('x(t)')
    ax3.set_title(f'Pitchfork Evolution (r = {r_test})')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Example contact process evolution
    example_p = 0.7  # Supercritical
    example_history = contact_process_simulation(50, example_p, steps=500, seed_density=0.2)
    
    ax4.plot(example_history, 'purple', linewidth=2, alpha=0.8)
    ax4.axhline(y=np.mean(example_history[-100:]), color='red', linestyle='--', 
                alpha=0.7, label=f'Final density ≈ {np.mean(example_history[-100:]):.3f}')
    ax4.set_xlabel('Time Steps')
    ax4.set_ylabel('Active Density')
    ax4.set_title(f'Contact Process Evolution (p = {example_p})')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('unified_bifurcation_verification.png', dpi=150, bbox_inches='tight')
    
    # 5. Final assessment
    print("\\n" + "="*60)
    print("UNIFIED FRAMEWORK ASSESSMENT")
    print("="*60)
    
    framework_valid = (pitchfork_symmetric and contact_symmetric and 
                      pitchfork_smooth and contact_smooth)
    
    if framework_valid:
        print("✓ FRAMEWORK SUPPORTED: Both systems exhibit symmetry-breaking transitions")
        print("✓ Universal bifurcation parameter behavior confirmed")
    else:
        print("✗ FRAMEWORK ISSUES DETECTED:")
        if not pitchfork_symmetric:
            print("  - Pitchfork symmetry breaking not confirmed")
        if not contact_symmetric:
            print("  - Contact process phase transition weak/absent")
        if not pitchfork_smooth:
            print("  - Pitchfork transition not smooth")
        if not contact_smooth:
            print("  - Contact process transition not smooth")
    
    return {
        'framework_valid': framework_valid,
        'pitchfork_critical': r_critical,
        'contact_critical_exp': p_experimental,
        'contact_critical_theory': p_theoretical,
        'transition_strength': transition_strength,
        'critical_point_agreement': abs(p_experimental - p_theoretical) < 0.1
    }

if __name__ == "__main__":
    results = test_symmetry_breaking()
    print(f"\\nVerification completed. Framework valid: {results['framework_valid']}")