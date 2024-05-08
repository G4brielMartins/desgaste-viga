import numpy as np
from scipy import signal

def easyFourier(x: np.ndarray, fs: float = 1.0, N: int = None, phasealso: bool = False, downsamplemode: str = "decimate"):
  """
    Evaluate the magnitude Fourier spectrum in dB using the FFT.
    Parameters:
      x: vector containing the signal in time.
      fs: the sampling frequency. 
      N: Either the number of samples for the transformed signal (when downsamplemode = "truncate") 
         or the approximate number os samples of the transformed signal (when downsamplemode = "decimate")
         (must be smaller than or equal to the length of x)
         (WARNING: obtained via decimation, data may be lost).
      downsamplemode: "decimate" (where the whole signal is considered when carrying out the FFT) or
                      "truncate" (considers only the first N samples of the signal - standard for numpy.fft)
    Returns: (magdb,freqvec)
      magdb: vector containing the magnitude samples of the fft (dB).
      freqs: vector containing the frequency values (Hz).
  """
  nsamples = x.shape[0]
  if downsamplemode == "decimate":
    fftaux = np.fft.fft(x)
    magdb = 20*np.log10( 2*np.abs(fftaux/nsamples)[0:int(np.floor(nsamples/2))] )
    freqs = (np.fft.fftfreq(nsamples) * fs)[0:magdb.shape[0]]
    if N:
      factor = int(np.ceil(float(nsamples)/float(N)))
      if phasealso:
        return magdb[::factor],freqs[::factor],np.angle(fftaux[0:int(np.floor(nsamples/2))][::factor])
      else:
        return magdb[::factor],freqs[::factor]
    else:
      if phasealso:
        return magdb,freqs,np.angle(fftaux[0:int(np.floor(nsamples/2))])
      else:
        return magdb,freqs
  elif downsamplemode == "truncate":
    if not N:
      N = nsamples
    fftaux = np.fft.fft(x,N)
    magdb = 20*np.log10( 2*np.abs(fftaux/N)[0:int(np.floor(N/2))] )
    freqs = (np.fft.fftfreq(N) * fs)[0:magdb.shape[0]]
    if phasealso:
      return magdb,freqs,np.angle(fftaux[0:int(np.floor(nsamples/2))])
    else:
      return magdb,freqs
  else:
    raise BaseException("Invalid value for downsamplemode.")


def ARSmooth(sig,coef=0.95):
  """
    AR signal smoother.
    - sig is the signal;
    - coef is the AR coef.
  """
  last = 0
  out = np.zeros(sig.shape)
  for n in range(0,sig.shape[0]):
    out[n] = coef*last + sig[n]*(1-coef)
    last = out[n]
  return out


class DCRemover():
  
  # http://sam-koblenski.blogspot.com/2015/11/everyday-dsp-for-programmers-dc-and.html
  def __init__(sf,alpha=0.99):
    sf.alpha = alpha
    sf.wn = 0
    sf.wn1 = 0
    
  def filter(sf,x):
    sf.y = np.zeros(x.shape[0])
    sf.wn = 0
    sf.wn1 = 0
    for k in range(x.shape[0]):
      sf.wn1 = sf.wn
      sf.wn = x[k] + sf.alpha * sf.wn1
      sf.y[k] = sf.wn - sf.wn1
    return sf.y


def NLargestPeaks(n,freq,mag,distance=20):
  pks = signal.find_peaks(mag,distance=distance)
  freqpks = freq[pks[0]]
  magpks = mag[pks[0]]
  idxnlargest = np.argsort(magpks)[-n:]
  freqpks = freqpks[idxnlargest]
  magpks = magpks[idxnlargest]
  idxsortbyfreq = np.argsort(freqpks)
  freqpks = freqpks[idxsortbyfreq]
  magpks = magpks[idxsortbyfreq]
  return {'freqs':freqpks, 'mags': magpks}


def freqAnalysis(signal,axis,fs=250,removeDC=True,labelsize=8,npeaks=3,peakdistance=50):
  if removeDC:
    mag,freq = easyFourier(signal - np.mean(signal),fs=fs)
  else:
    mag,freq = easyFourier(signal,fs=fs)

  axis.plot(freq,mag)
  # axis.set_ylim(-100,20)
  axis.tick_params(labelsize=labelsize)
  pks = NLargestPeaks(npeaks,freq,mag,distance=peakdistance)
  axis.plot(pks['freqs'],pks['mags'],"xr")
  for f,m in zip(pks['freqs'],pks['mags']):
    axis.text(f,m,f" {f:.2f} Hz",fontsize=7)
