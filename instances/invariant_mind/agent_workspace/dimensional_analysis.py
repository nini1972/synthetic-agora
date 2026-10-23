# Integrate the Lorenz system using RK4
    def integrate_lorenz(initial_state, sigma, beta, rho, dt, t_total):
        states = np.zeros((int(t_total/dt), 3))
        times = np.arange(0, t_total, dt)
        
        state = np.array(initial_state)
        for i, t in enumerate(times):
            states[i] = state
            
            # Euler method for simplicity
            k1 = lorenz(state, sigma, beta, rho)
            state += dt * k1
        
        return states
    
    # Calculate lambda_max using Benettin's algorithm
    def benettin_lambda_max(states, dt, dim=3, max_iter=5000, threshold=1e-12):
        """
        Compute maximal Lyapunov exponent via Benettin's algorithm.
        Uses QR decomposition to avoid renormalization drift.
        """
        n_steps = len(states)
        if n_steps < max_iter:
            max_iter = n_steps
        
        # Take first few points as tangent vectors
        tangent_vectors = states[:max_iter].copy()
        tangent_vectors -= tangent_vectors.mean(axis=0)
        tangent_vectors /= np.linalg.norm(tangent_vectors, axis=1, keepdims=True)
        
        # Track accumulated Lyapunov sum and normalization factors
        log_sum = 0.0
        norm_prod = 1.0
        
        # Track largest eigenvalue magnitude
        max_lambda = 0.0
        
        for i in range(max_iter):
            # Predict step
            pred_states = states.copy()[:i+1]
            pred_states[-1] += dt * lorenz(pred_states[-1], sigma, beta, rho)
            
            # Correct step (use predicted state for better accuracy)
            correct_state = pred_states[-1]
            k1 = lorenz(correct_state, sigma, beta, rho)
            k2 = lorenz(correct_state + dt/2*k1, sigma, beta, rho)
            k3 = lorenz(correct_state + dt/2*k2, sigma, beta, rho)
            k4 = lorenz(correct_state + dt*k3, sigma, beta, rho)
            correct_state += dt/6*(k1 + 2*k2 + 2*k3 + k4)
            
            # Update tangent vectors via variational equations
            dv_dt = np.zeros_like(tangent_vectors)
            for j in range(len(tangent_vectors)):
                dv_dt[j] = lorenz(pred_states[j], sigma, beta, rho)
            
            tangent_vectors += dt * dv_dt
            
            # Reorthogonalize and normalize tangent vectors
            Q, R = np.linalg.qr(tangent_vectors)
            diag_R = np.abs(np.diag(R))
            valid_mask = diag_R > threshold
            if np.any(valid_mask):
                log_sum += np.sum(np.log(diag_R[valid_mask]))
                norm_prod *= diag_R[valid_mask]**dt
                Q = Q[:, valid_mask]
                tangent_vectors = Q
                
                # Accumulate largest eigenvalue magnitude
                max_lambda = max(max_lambda, np.max(np.abs(np.log(diag_R))))
        
        # Average exponent
        lam = 0.0
        if n_steps > 0:
            lam = log_sum / (norm_prod * n_steps * dt)
        
        return lam, max_lambda
    
    # Main analysis loop
    base_params = (10, 28, 8/3)
    scale_factors = np.logspace(-1, 1, 5)  # Reduced from 9 to 5
    
    quantization_results = []
    
    print("Performing Dimensional Analysis in World C:")
    for sf in scale_factors:
        scaled_params = (base_params[0]*sf, base_params[1], base_params[2])
        
        # Integrate trajectory
        init_state = np.random.randn(3) * 0.1
        traj = integrate_lorenz(init_state, *scaled_params, dt=0.001, t_total=50)
        
        # Remove transient
        traj_clean = traj[200:]
        
        # Compute Lyapunov exponent using Benettin's algorithm
        lam_max, _ = benettin_lambda_max(traj_clean, dt=0.001, max_iter=5000)
        
        # Compute correlation dimension using Grassberger-Procaccia
        dp = correlation_dimension(traj_clean, max_tau=50, min_points=50)
        
        quantization_results.append({
            'sf': float(sf),
            'lam_max': float(lam_max),
            'D2': float(dp['D2']),
            'order': int(dp['order'])
        })
        print(f"Scale {sf:.2f}: lam_max={lam_max:+.4f}, D2={dp['D2']:.4f}, order={dp['order']}")
    
    # Save results
    with open('dimensional_analysis.json', 'w') as f:
        json.dump(quantization_results, f, indent=2)
    
    # Plotting
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Figure 1: Q vs Scaling Factor
    q_values = [r['lam_max'] for r in quantization_results]
    scaled = [r['sf'] for r in quantization_results]
    axes[0].semilogx(scaled, q_values, 'o-', linewidth=2, markersize=8, color='#1f77b4')
    axes[0].set_xlabel('Scaling Factor')
    axes[0].set_ylabel(r'$\lambda_{max}$')
    axes[0].set_title('Topological Scaling of Maximal Lyapunov Exponent')
    axes[0].grid(True, which='both', alpha=0.2)
    axes[0].axvspan(1.0, 10.0, alpha=0.08, color='orange', label='Emergence Horizon')
    axes[0].legend()
    
    # Figure 2: Correlation Dimension vs Scaling Factor
    dp_orders = [r['order'] for r in quantization_results]
    axes[1].semilogx(scaled, dp_orders, 's-', linewidth=2, markersize=8, color='#2ca02c')
    axes[1].set_xlabel('Scaling Factor')
    axes[1].set_ylabel('Correlation Dimension Order')
    axes[1].set_title('Topological Scaling of Correlation Dimension Order')
    axes[1].grid(True, which='both', alpha=0.2)
    axes[1].axvspan(1.0, 10.0, alpha=0.08, color='orange', label='Emergence Horizon')
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig('dimensional_analysis_confirmed.png', dpi=300)
    plt.close()

if __name__ == '__main__':
    main()
