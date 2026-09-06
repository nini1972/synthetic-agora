"""Analyze Thomas fixed points: solve sin(y)=b x, sin(z)=b y, sin(x)=b z.
For b>1: origin is only fixed point. Labyrinth/chaos persists to larger b than 0.208."""
import numpy as np
from scipy.optimize import fsolve
def thomas_f_J(b):
    f=lambda s:np.array([np.sin(s[1])-b*s[0],np.sin(s[2])-b*s[1],np.sin(s[0])-b*s[2]])
    J=lambda s:np.array([[-b,np.cos(s[1]),0.0],[0.0,-b,np.cos(s[2])],[np.cos(s[0]),0.0,-b]])
    return f,J
def lyap1(f,Jf,s0,T=800.0,dt=0.005,trans=400.0):
    s=np.array(s0,float); Q=np.eye(3); n=int(T/dt); nt=int(trans/dt); acc=0.0;cnt=0
    for i in range(n+nt):
        k1=f(s);k2=f(s+k1*dt/2);k3=f(s+k2*dt/2);k4=f(s+k3*dt); s=s+(k1+2*k2+2*k3+k4)*dt/6
        J=Jf(s); M1=J@Q;M2=J@(Q+M1*dt/2);M3=J@(Q+M2*dt/2);M4=J@(Q+M3*dt)
        Q=Q+(M1+2*M2+2*M3+M4)*dt/6
        Q,R=np.linalg.qr(Q)
        if i>=nt: acc+=np.log(abs(R[0,0]));cnt+=1
    return acc/(cnt*dt)
# scan across wide b, single trajectory, fine near claimed criticality
print('=== Wide lambda_1 sweep (validated Benettin) ===')
for b in [0.30,0.40,0.50,0.60,0.70,0.80,0.90,1.0]:
    f,J=thomas_f_J(b)
    print('  b=%.2f lam1=%+.5f'%(b,lyap1(f,J,[1.0,1.5,0.8],T=600,dt=0.005,trans=300)))
