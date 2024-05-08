import numpy as np
from .CantileverBeam import CantileverBeam

class PathModeling:

    '''
        Modelling of paths on a given beam
        cbeam: the beam under simulation (of type CantileverBeam)
        N: memory size of the obtained models
        type: 0 for ideal modeling using the impulse response and
              1 for adaptive modeling using the NLMS algorithm with 0.25 as step size and 1e-3 as normalization factor.
        simtime: simulation time for type = 1 (adaptive modeling)
        mode: 0 for accelearation (accelerometer)
              1 for rotation velocity (gyroscope)
    '''
    def __init__(self,cbeam: CantileverBeam,N=1000,type=1,simtime=120,mode=0):
        self.beam = cbeam
        self.N = N
        self.type = type
        self.simtime = simtime
        if mode == 0:
            self.movefunc = self.beam.getaccelms2
        elif mode == 1:
            self.movefunc = self.beam.getrotationvel

    '''
        pinput: position for force application
        poutput: position for accelaration (m/s^2) reading         
    '''
    def runModelling(self,pinput,poutput):
        self.beam.reset()
        N = self.N
        ww = np.zeros(N)

        if self.type == 0:
            x = np.zeros(N)
            x[0] = 10            
            for n in range(0,N):
                self.beam.setforce(pinput,x[n])
                self.beam.update()
                #wfcb[n] = cbeam.a[pref]
                # wfcb[n] = cbeam.getaccel(pref)/10
                ww[n] = self.movefunc(poutput)
        else:
            NN = self.simtime * int(np.round(1/self.beam.Ts))
            x = np.random.rand(NN)*4-2
            xx = np.zeros(N)
            for n in range(0,NN):
                xx[1:] = xx[:-1]
                xx[0] = x[n]
                self.beam.setforce(pinput,x[n])
                self.beam.update()
                e = self.movefunc(poutput) - ww @ xx
                ww = ww + 0.25 * e * xx / (xx.T @ xx + 1e-3) 

        return ww 