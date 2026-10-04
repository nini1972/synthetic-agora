import numpy as np
N=200; K0=5.0; dt=0.04; T=45.0
rng=np.random.default_rng(42)
th=rng.uniform(0,2*np.pi,N); om=rng.uniform(-1,1,N)
ns=int(T/dt)
trace=[]
for i in range(ns):
    c=np.cos(th); sn=np.sin(th)
    R=np.sqrt(c.dot(c)+sn.dot(sn))/N
    p=np.arctan2(sn.mean(), c.mean())
    K=K0  # alpha=0
    th += dt*(om + K*np.sin(p-th))
    if i%200==0: trace.append((i,round(float(R),4),round(float(th.std()),3)))
print('alpha=0 trace (i, R, theta-std):', trace)
c=np.cos(th); sn=np.sin(th)
Rf=np.sqrt(c.dot(c)+sn.dot(sn))/N
print('final R =', Rf)
print('mean |om| =', np.abs(om).mean(), ' max om =', om.max())
print('coupling max per step =', K0*dt, ' drift from om per step ~', (om*dt).std())