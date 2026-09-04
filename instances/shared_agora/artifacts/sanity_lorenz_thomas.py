import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def lyap_benettin(deriv, jac, s0, T=2000.0, dt=0.005, trans=1000.0):
    s=np.array(s0,dtype=float); Q=np.eye(3)
    n=int(T/dt); nt=int(trans/dt)
    acc=0.0; cnt=0
    for i in range(n+nt):
        def f(s): return np.array(deriv(s))
        k1=f(s); k2=f(s+k1*dt/2); k3=f(s+k2*dt/2); k4=f(s+k3*dt)
        s=s+(k1+2*k2+2*k3+k4)*dt/6
        J=np.array(jac(s))
        Q=J@Q
        Q,R=np.linalg.qr(Q)
        if i>=nt:
            acc+=np.log(np.abs(R[0,0])); cnt+=1
    return acc/cnt

# LORENZ validation
def lor_d(s): return [10*(s[1]-s[0]), s[0]*(28-s[2])-s[1], s[0]*s[1]-(8/3)*s[2]]
def lor_j(s): return [[-10,10,0],[28-s[2],-1,-s[0]],[s[1],s[0],-8/3]]
lz=lyap_benettin(lor_d,lor_j,[1,1,1])
print('Lorenz lambda_1 = %.4f  (reference ~0.906)'%lz)

# THOMAS quick trajectory check at b=0.1
def th_d(s,b): return [np.sin(s[1])-b*s[0], np.sin(s[2])-b*s[1], np.sin(s[0])-b*s[2]]
b=0.1; s=np.array([0.5,0.5,0.5]); dt=0.02; T=3000
ts=[]; xs=[]
for i in range(T):
    k1=np.array(th_d(s,b)); k2=np.array(th_d(s+k1*dt/2,b)); k3=np.array(th_d(s+k2*dt/2,b)); k4=np.array(th_d(s+k3*dt,b))
    s=s+(k1+2*k2+2*k3+k4)*dt/6
    if i%10==0: ts.append(i*dt); xs.append(s[0])
plt.figure(figsize=(10,4))
plt.plot(ts,xs,lw=0.5)
plt.title('Thomas b=0.1 trajectory x(t)'); plt.xlabel('t'); plt.ylabel('x')
plt.tight_layout(); plt.savefig('thomas_traj.png',dpi=100)
print('Thomas b=0.1 x range over window: %.3f to %.3f (std=%.3f)'%(min(xs[-500:]),max(xs[-500:]),np.std(xs[-500:])))
