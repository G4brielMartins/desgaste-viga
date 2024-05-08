import numpy as np


class FIRNLMS:    

    def __init__(self,memorysize=100,stepsize=0.1,regularization=1e-6,wwavgwindow=None):
        """
            Parameters:
                memorysize, stepsize and regularization
        """
        self.N = memorysize
        self.mu = stepsize
        self.psi = regularization
        self.finished = False
        self.ww = None
        self.wwavgwindow = wwavgwindow
        self.wwavg = None

    def run(self,insignal,outsignal,maxiter=None):
        if not maxiter:
            rangesim = insignal.shape[0]
        else: 
            rangesim = min(insignal.shape[0],maxiter)
        if insignal.shape[0] != outsignal.shape[0]:
            raise Exception("Input and output must be vectors with same length.")
        self.xx = np.zeros(self.N)
        self.ww = np.zeros(self.N)
        self.sqerror = np.zeros(rangesim)
        if self.wwavgwindow:
            self.wwavg = np.zeros(self.N)
            for n in range(rangesim):
                self.xx[1:] = self.xx[0:-1]
                self.xx[0] = insignal[n]
                y = self.xx @ self.ww
                e = outsignal[n] - y
                self.ww = self.ww + self.mu * e * self.xx / (self.xx @ self.xx + self.psi)
                self.sqerror[n] = e**2
                if n >= (rangesim-self.wwavgwindow):
                  self.wwavg += self.ww
            self.wwavg = self.wwavg / self.wwavgwindow
        else:
            for n in range(rangesim):
                self.xx[1:] = self.xx[0:-1]
                self.xx[0] = insignal[n]
                y = self.xx @ self.ww
                e = outsignal[n] - y
                self.ww = self.ww + self.mu * e * self.xx / (self.xx @ self.xx + self.psi)
                self.sqerror[n] = e**2
        self.finished = True

class FIRFxNLMS:

	def __init__(sf,mem,memsec):
		sf.mem = mem # Memory size
		sf.ww = np.zeros(mem) # Coefficient vector        
		sf.mu = 0.1 # Step-size parameter
		sf.fi = 1e-6 # Regularization parameter        
		if (memsec > 0):
			sf.memsec = memsec
			sf.wwsec = np.zeros(memsec) # Sec. path coefficient vector      
			sf.xxf = np.zeros(mem)
		else:
			sf.memsec = 0
		sf.vecsize = (mem if (mem > memsec) else memsec);
		sf.xx = np.zeros(sf.vecsize) # Input vector
		sf.y = 0 # Filter output
		sf.e = 0 # Error
		sf.norm = 0
		sf.setAlgorithm('NLMS')

	def reset(sf):
		sf.ww = np.zeros(sf.mem)
		sf.xxf = np.zeros(sf.mem)
		sf.xx = np.zeros(sf.vecsize)
		sf.y = 0
		sf.e = 0
		sf.norm = 0

	def setSecondary(sf,wwsec):
		sf.wwsec = wwsec

	def setParams(sf,mu,fi):
		sf.mu = mu
		sf.fi = fi

	def evalout(sf,x):
		sf.xx[1:sf.vecsize] = sf.xx[0:sf.vecsize-1]
		sf.xx[0] = x
		sf.y = sf.xx[0:sf.mem] @ sf.ww
		sf.xxf[1:sf.mem] = sf.xxf[0:sf.mem-1]
		sf.xxf[0] = sf.xx[0:sf.memsec] @ sf.wwsec

	def LMSupdate(sf,e):
		sf.norm = sf.ww @ sf.ww
		sf.ww = sf.ww + 2 * sf.mu * e * sf.xxf

	def NLMSupdate(sf,e):
		sf.norm = sf.ww @ sf.ww
		sf.ww = sf.ww + sf.mu * e * sf.xxf / ((sf.xxf@sf.xxf) + sf.fi)

	def setAlgorithm(sf,alg='NLMS'):
		if alg == 'LMS':
			sf.update = sf.LMSupdate
		else:
			sf.update = sf.NLMSupdate


class LeakyFxNLMS (FIRFxNLMS):

	def __init__(sf,mem,memsec,leakfactor):
		super().__init__(mem,memsec)
		sf.leakfactor = leakfactor

	def LMSupdate(sf,e):
		sf.norm = sf.ww @ sf.ww
		sf.ww = sf.leakfactor * sf.ww + 2 * sf.mu * e * sf.xxf

	def NLMSupdate(sf,e):
		sf.norm = sf.ww @ sf.ww
		sf.ww = sf.leakfactor * sf.ww + sf.mu * e * sf.xxf / ((sf.xxf@sf.xxf) + sf.fi)
		

class CVAFxNLMS:

	def __init__(sf,mem,memsec=0,mem2=0,memsec2=0):
		sf.mem = mem # Memory size
		sf.mem2 = mem2 # Memory size of second filter
		sf.ww = np.zeros(mem) # Coefficient vector        
		sf.ww2 = np.zeros(mem2)
		sf.mu = 0.1 # Step-size parameter
		sf.fi = 1e-6 # Regularization parameter        
		sf.mu2 = 0.1
		if (memsec > 0):
			sf.memsec = memsec
			sf.wwsec = np.zeros(memsec) # Sec. path coefficient vector      
			sf.xxf = np.zeros(mem)			
		else:
			sf.memsec = 0
		if (memsec2 > 0):
			sf.memsec2 = memsec2
			sf.wwsec2 = np.zeros(memsec2) # Sec. path coefficient vector      
			sf.xxf2 = np.zeros(mem2)			
		else:
			sf.memsec2 = 0
		sf.vecsize = (mem if (mem > memsec) else memsec)
		sf.xx = np.zeros(sf.vecsize) # Input vector
		sf.y = 0 # Filter output
		sf.vecsize2 = (mem2 if (mem2 > memsec2) else memsec2)
		sf.xx2 = np.zeros(sf.vecsize2) # Input vector
		sf.y2 = 0 # Filter output
		sf.e = 0 # Error
		sf.norm = 0
		sf.setAlgorithm('NLMS')

	def reset(sf):
		sf.ww = np.zeros(sf.mem)
		sf.xxf = np.zeros(sf.mem)
		sf.xx = np.zeros(sf.vecsize)
		sf.y = 0
		sf.ww2 = np.zeros(sf.mem2)
		sf.xxf2 = np.zeros(sf.mem2)
		sf.xx2 = np.zeros(sf.vecsize2)
		sf.y2 = 0
		sf.e = 0
		sf.norm = 0

	def setSecondary(sf,wwsec):
		sf.wwsec = wwsec
		sf.wwsec2 = wwsec

	def setParams(sf,mu,fi,mu2=0):
		sf.mu = mu
		sf.fi = fi
		sf.mu2 = mu2

	def evalout(sf,x,x2):
		sf.xx[1:sf.vecsize] = sf.xx[0:sf.vecsize-1]
		sf.xx[0] = x
		sf.y1 = sf.xx[0:sf.mem] @ sf.ww
		sf.xxf[1:sf.mem] = sf.xxf[0:sf.mem-1]
		sf.xxf[0] = sf.xx[0:sf.memsec] @ sf.wwsec
		sf.xx2[1:sf.vecsize2] = sf.xx2[0:sf.vecsize2-1]
		sf.xx2[0] = x2
		sf.y2 = sf.xx2[0:sf.mem] @ sf.ww2
		sf.xxf2[1:sf.mem] = sf.xxf2[0:sf.mem-1]
		sf.xxf2[0] = sf.xx2[0:sf.memsec] @ sf.wwsec2
		sf.y = sf.y1 + sf.y2

	def NLMSupdate(sf,e):
		normterm = sf.xxf@sf.xxf + sf.xxf2@sf.xxf2 + sf.fi
		sf.ww = sf.ww + sf.mu * e * sf.xxf / normterm
		sf.ww2 = sf.ww2 + sf.mu2 * e * sf.xxf2 / normterm

	def LMSupdate(sf,e):
		sf.ww = sf.ww + 2 * sf.mu * e * sf.xxf
		sf.ww2 = sf.ww2 + 2 * sf.mu2 * e * sf.xxf2

	def setAlgorithm(sf,alg='NLMS'):
		if alg == 'LMS':
			sf.update = sf.LMSupdate
		else:
			sf.update = sf.NLMSupdate

