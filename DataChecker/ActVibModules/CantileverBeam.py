# CantileverBeam Module

import numpy as np
from scipy import linalg


class CantileverBeam:
    '''
        Classe similar à classe Viga, mas com saídas em aceleração ao invés de deslocamento.
    '''
    # Parâmetros gerais:
    m = 1  # massa - sempre 1 para todas as vigas

    def __init__(self,npoints=60,width=0.05,thickness=0.00575,length=0.58,density=7900,
                    elasticmod=2e11,Tsampling=0.004,nmodes=5,
                    damp=[0.002, 0.002, 0.001, 0.001, 0.001],
                    forcescaler=1,noisestd=0):
        self.Ts = Tsampling
        self.npoints = npoints
        self.nmodes = nmodes
        self.width = width
        self.thickness = thickness
        self.length = length        
        self.density = density
        self.elasticmod = elasticmod
        self.forcescaler = forcescaler  # Permite definir um "scaler" para força, simulando por exemplo uma conversão de Volts para Newton caso a força seja gerada a partir de uma tensão elétrica.        
        self.forcescaler1 = forcescaler
        self.deltax = self.length / (self.npoints - 1)  # Checar isso
        self.rotvelmultiplier = (1 / self.deltax) * 180 / np.pi
        self.magnetdist = 1e-3        
        self.evaluateModesAndFreqs()
        self.memiir = 3
        self.Fs = 1 / self.Ts
        self.wn = 2 * np.pi * self.freqsHz
        self.zeta = np.array(damp)
        self.wd = self.wn * np.sqrt(1-self.zeta[:self.nmodes]**2)   
        self.Aiir = np.zeros((self.nmodes,self.memiir-1)) # Coefs dos denominadores dos IIRs de cada modo
        self.Biir = np.zeros((self.nmodes,self.memiir)) # Coefs dos numeradores dos IIRs de cada modo       
        # Cálculo dos coeficientes dos filtros IIR
        for k in range(0,self.nmodes):            
            self.Biir[k,0] = 0
            self.Biir[k,1] = np.exp(-self.zeta[k]*self.wn[k]*self.Ts) * np.sin(self.wd[k]*self.Ts)
            self.Biir[k,2] = 0
            self.Aiir[k,0] = -2 * np.exp(-self.zeta[k]*self.wn[k]*self.Ts) * np.cos(self.wd[k]*self.Ts)
            self.Aiir[k,1] = np.exp(-2*self.zeta[k]*self.wn[k]*self.Ts)        
        self.reset()
        self.noisestd = noisestd        
        self.setaccelg(False)

    
    def getModeShapes(self):
        """
            Get data for plotting the modal curves.

            Returns:
                x: Vector containing the positions along the beam.
                m: mode plots (m[:,0] for the first mode, m[:,1] for the second, etc)
        """
        x = np.linspace(0,self.length,num=self.npoints)
        return x,self.vmod


    def evaluateModesAndFreqs(self):
        I = (self.width * self.thickness**3) / 12 # Inertial moment
        beam_mass = self.density * self.width * self.thickness * self.length
        # Mass matrix:
        M = np.matrix( np.eye(self.npoints) * (beam_mass/self.npoints) )
        M[0,0] = M[0,0]/2        
        A = np.zeros((self.npoints,self.npoints))
        for r in range(self.npoints):
            for c in range(r+1):
                k = self.npoints-r
                l = self.npoints-c
                A[r,c] = ((self.deltax**3)/(6*self.elasticmod*I)) * (3* k**2 * l - k**3)
                A[c,r] = A[r,c]
        K = linalg.inv(A)
        L = linalg.cholesky(M)
        Kt = linalg.inv(L.T) @ K @ linalg.inv(L)
        ww,P = linalg.eig(Kt)
        ww = np.real(ww)
        sidxs = np.argsort(ww)
        U = linalg.inv(L) @ P
        self.vmod = np.zeros((self.npoints,self.nmodes))
        self.freqsHz = np.zeros(self.nmodes)
        for k in range(self.nmodes):
            self.vmod[:,k] = U[::-1,sidxs[k]]
            self.freqsHz[k] = np.sqrt(ww[sidxs[k]])/2/np.pi

    def configforcescaler(self,forcescl,magnetdist=1e-3):
        self.forcescaler1 = forcescl
        self.forcescaler = forcescl / ( (magnetdist * 1000) ** 2 )
        self.magnetdist = magnetdist

    def setforce(self,pos,val):
        self.f[pos] = self.forcescaler * val

    def setforcenl(self,pos,val):
        self.f[pos] = self.forcescaler1 * val / ( (( self.magnetdist + self.x[pos] ) * 1000) ** 2 )

    def setaccelg(self,val):
        if val: 
            self.getaccel = self.getaccelg
        else:
            self.getaccel = self.getaccelms2

    def getaccelms2(self,pos):
        return self.a[pos] + np.random.randn()*self.noisestd

    def getaccelg(self,pos):
        return (self.a[pos] + np.random.randn()*self.noisestd)/9.80665
    
    def getrotationvel(self,pos):
        return self.rotvel[pos] + np.random.randn()*self.noisestd

    def reset(self):
        self.f = np.zeros(self.npoints)
        self.x = np.zeros(self.npoints)
        self.a = np.zeros(self.npoints)
        self.xiir = np.zeros((self.npoints,self.memiir))
        self.yiir = np.zeros((self.npoints,self.memiir))
        self.bufdesloc = np.zeros(self.npoints)
        self.bufvel = np.zeros((self.npoints,2))
        self.rotvel = np.zeros(self.npoints)  # Trying to implement rotation velocity, in degrees per second.

    def update(self):
        self.bufvel[:,1] = self.bufvel[:,0]
        self.bufdesloc[:] = self.x
        self.x = np.zeros(self.npoints)
        for k in range(0,self.nmodes):
            self.xiir[k,1:self.memiir] = self.xiir[k,0:self.memiir-1]
            self.xiir[k,0] = self.vmod[:,k] @ self.f
            self.yiir[k,1:self.memiir] = self.yiir[k,0:self.memiir-1]
            self.yiir[k,0] = (self.Biir[k,:] @ self.xiir[k,:] - self.Aiir[k,:] @ self.yiir[k,1:self.memiir])
            self.x = self.x + self.Ts / (self.m*self.wd[k]) * self.yiir[k,0] * self.vmod[:,k]        
        self.bufvel[:,0] = (self.x - self.bufdesloc) * self.Fs
        self.a = (self.bufvel[:,0] - self.bufvel[:,1]) * self.Fs
        self.rotvel[1:] = (self.bufvel[1:,0] - self.bufvel[:-1,0]) * self.rotvelmultiplier