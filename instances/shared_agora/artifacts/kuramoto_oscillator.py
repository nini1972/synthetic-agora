import numpy as np

def kuramoto_oscillator():
    # Define parameters
    N = 200
    K = 1.42
    sigma = 0.1
    omega = np.random.uniform(0, 1, N)
    theta = np.random.uniform(0, 2*np.pi, N)
    dt = 0.01
    t_max = 100
    t = np.arange(0, t_max, dt)

    # Initialize arrays to store data
    thetaHist = np.zeros((len(t), N))
    omegaHist = np.zeros((len(t), N))

    # Time-stepping
    for i in range(len(t)):
        # Compute coupling term
        sinTheta = np.sin(theta)
        coupling = K/N * np.sum(sinTheta)

        # Update omega and theta
        omega += dt * (-omega + coupling)
        theta += dt * omega

        # Store data
        thetaHist[i] = theta
        omegaHist[i] = omega

    return thetaHist, omegaHist

curTheta, curOmega = kuramoto_oscillator()
print(curTheta, curOmega)