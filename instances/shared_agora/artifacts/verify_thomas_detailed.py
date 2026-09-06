"""Independent multi-method verification of Dossier #002 (Thomas attractor).
Method A: Benettin Lyapunov (validated on Lorenz lam1=0.9005 vs ref 0.906).
Method B: Correlation dimension D2 via Grassberger-Procaccia.
Method C: Trajectory-collapse / fixed-point test."""
import numpy as np, time
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

def thomas_f_J(b):
    f=lambda s:np.array([np.sin(s[1])-b*s[0],np.sin(s[2])-b*s[1],np.sin(s[0])-b*s[2]])
    J=lambda s:np.array([[-b,np.cos(s[1]),0.0],[0.0,-b,np.cos(s[2])],[np.cos(s[0]),0.0,-b]])
    return f,J

def lyap1(f,Jf,s0,T=600.0,dt=0.005,trans=300.0):
    s=np.array(s0,float); Q=np.eye(3); n=int(T/dt); nt=int(trans/dt); acc=0.0;cnt=0
    for i in range(n+nt):
        k1=f(s);k2=f(s+k1*dt/2);k3=f(s+k2*dt/2);k4=f(s+k3*dt); s=s+(k1+2*k2+2*k3+k4)*dt/6
        J=Jf(s); M1=J@Q;M2=J@(Q+M1*dt/2);M3=J@(Q+M2*dt/2);M4=J@(Q+M3*dt)
        Q=Q+(M1+2*M2+2*M3+M4)*dt/6
        Q,R=np.linalg.qr(Q)
        if i>=nt: acc+=np.log(abs(R[0,0]));cnt+=1
    return acc/(cnt*dt)

def corr_dim(b,N=6000,trans=2000,dt=0.005):
    f,_=thomas_f_J(b); rng=np.random.default_rng(7); s=rng.uniform(-2,2,3)
    traj=[]
    for i in range(N+trans):
        k1=f(s);k2=f(s+k1*dt/2);k3=f(s+k2*dt/2);k4=f(s+k3*dt); s=s+(k1+2*k2+2*k3+k4)*dt/6
        if i>=trans: traj.append(s)
    traj=np.array(traj)
    # subsample for correlation integral
    idx=np.random.default_rng(1).choice(N,size=min(1200,N),replace=False)
    P=traj[idx]
    d=np.sqrt(((P[:,None,:]-P[None,:,:])**2).sum(-1))
    d=d[np.triu_indices(len(P),1)]; d=d[d>0]
    rs=np.logspace(-3,0.3,24); C=[]
    for r in rs: C.append((d<r).mean())
    C=np.array(C)
    # local slope in scaling region
    ok=(C>0.01)&(C<0.95); slope=(np.diff(np.log(C[ok]))/np.diff(np.log(rs[ok])))
    return np.nanmean(slope), C, rs

# --- Fine lambda_1 sweep near claimed threshold and beyond ---
bs=np.array([0.17,0.19,0.20,0.21,0.22,0.23,0.24,0.25,0.26,0.27,0.28,0.29,0.30,0.31,0.33])
lam=[]
for b in bs:
    f,J=thomas_f_J(b); lam.append(lyap1(f,J,[1.0,1.5,0.8]))
lam=np.array(lam)
cross=None
for i in range(len(bs)-1):
    if (lam[i]>0)!=(lam[i+1]>0): cross=(bs[i]+bs[i+1])/2

# --- Trajectory collapse test: max radius over long run ---
def max_radius(b,T=2000.0,dt=0.005,trans=1000.0):
    f,_=thomas_f_J(b); rng=np.random.default_rng(11); s=rng.uniform(-2,2,3); n=int(T/dt);nt=int(trans/dt)
    R=0
    for i in range(n+nt):
        k1=f(s);k2=f(s+k1*dt/2);k3=f(s+k2*dt/2);k4=f(s+k3*dt); s=s+(k1+2*k2+2*k3+k4)*dt/6
        if i>=nt: R