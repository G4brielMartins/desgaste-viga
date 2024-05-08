import numpy as np
from scipy.signal import butter, lfilter
from scipy.fftpack import fft

#class SignalGen:

def sine(Npoints,freqHz,samplingT,Amplitude=1):
    x = np.zeros(Npoints)
    for k in range(0,Npoints):
        x[k] = np.sin(2*np.pi*freqHz*k*samplingT)   
    return x

def filteredNoise(Npoints,var,lowcut,highcut,samplingFreq,order=10):
    xa = np.sqrt(var) * np.random.randn(Npoints)
    nyq = 0.5 * samplingFreq
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    x = lfilter(b, a, xa)
    return x

def chirp(seconds,samplingfreq,freq,ampl=1,deltai=10,deltaf=10,tinicio=10,tfim=None):
    """
    Generates a signal that resembles the start, steady state and end of the functioning of a rotating machine.
    Such a signal is useful for testing active vibration control systems.
    The generated signal is based on the chirp signal.

    Args:
        seconds (int): Total time of the signal
        samplingfreq (int): Sampling frequency (Hz)
        freq (int): Signal frequency (Hz)
        ampl (int, optional): Signal amplitude at steady state. Defaults to 1.
        deltai (int, optional): Rising time of the signal. Defaults to 10.
        deltaf (int, optional): Fall time of the signal. Defaults to 10.
        tinicio (int, optional): Time of the beginning of signal rise. Defaults to 10.
        tfim (int, optional): Time of the beginning of signal fall. Defaults to None.

    Returns:
        numpy.ndarray: Generated signal
    """    
    dt = 1/samplingfreq
    tt = np.arange(0,seconds,dt) # Vetor de tempo de 0 a Nseconds com passos de dt
    out = np.zeros(tt.shape[0]) # Retorno
    f = 0 # Freq. inicial = 0
    integ = 0 # Integral, valor inicial
    cA = ampl/(freq**2) # Constante para amplitude ficar igual a "ampl" em regime
    A = 0 # Amplitude inicial
    if tfim is None:
        tfim = seconds
    for n,t in enumerate(tt): # Varia n de 0 ao número de elementos no vetor tt, e t = tt[n]
        if (t < tinicio) or (t > (tfim+deltaf)):
            f = 0             
        elif t <= (tinicio+deltai):
            f = freq * (t-tinicio) / deltai              
        elif (t >= tfim) and (t <= (tfim+deltaf)):
            f = freq - freq * (t-tfim) / deltaf               
        A = (f**2) * cA
        integ = integ + 2*np.pi*f*dt
        out[n] = A * np.sin(integ)
    return out
