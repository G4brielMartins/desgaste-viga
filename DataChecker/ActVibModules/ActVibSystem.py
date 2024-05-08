import pandas as pd
from numpy import linspace

class ActVibData(pd.DataFrame):

    def __init__(self,filename):    
        if str(filename).endswith(".csv"):
            super().__init__(pd.read_csv(filename,index_col=0,sep="\t"))
        else:    
            super().__init__(pd.read_feather(filename))
        self.filename = filename        
        if "Tempo (s)" in self.columns:
            self.oldcnamestonew()
        if "log" in self.columns:
            self.hasLog = True
        else:
            self.hasLog = False
        
    def oldcnamestonew(self):
        cnames = self.columns
        newcnames = []
        for k in range(len(cnames)):
            if cnames[k].startswith("Tempo"):
                newcnames.append("time")
            elif cnames[k].startswith("IMU") or (cnames[k] == "Log"):
                newcnames.append(cnames[k].lower())
            elif cnames[k].startswith("DAC") or cnames[k].startswith("ADC"):
                newcnames.append(cnames[k].replace(" ","").lower())
            elif cnames[k] == "Perturbacao":
                newcnames.append("perturb")
            elif cnames[k] == "Controle":
                newcnames.append("ctrl")
            elif cnames[k] == "Referencia":
                newcnames.append("ref")
            elif cnames[k] == "Erro": 
                 newcnames.append("err")
        self.columns = newcnames 

    def getTime(self):
        return self.time.values

    def getSignalNames(self):
        return list(self.columns)

    def getSignal(self,signalname):
        """
            Use getSignalNames() to get available signals.

        """
        return self[signalname].values
    
    def getAccX(self,imuidx=1):
        return self[f"imu{imuidx}accx"].values
    
    def getAccY(self,imuidx=1):
        return self[f"imu{imuidx}accy"].values

    def getAccZ(self,imuidx=1):
        return self[f"imu{imuidx}accz"].values

    def getGyroX(self,imuidx=1):
        return self[f"imu{imuidx}gyrox"].values
    
    def getGyroY(self,imuidx=1):
        return self[f"imu{imuidx}gyroy"].values

    def getGyroZ(self,imuidx=1):
        return self[f"imu{imuidx}gyroz"].values

    def getADCData(self,adcid=1):
        if (adcid < 1) or (adcid > 4):
            raise BaseException("ADCid must be between 1 and 4.")
        adccols = list(filter(lambda x: x.startswith("adc"), self.getSignalNames()))
        if len(adccols) == 0:
            raise BaseException("ADC data not found.")
        return self[adccols[adcid-1]].values
    
    def getadc1k(self):
        adccols = list(filter(lambda x: x.startswith("adc"), self.getSignalNames()))
        if len(adccols) == 0:
            raise BaseException("ADC data not found.")
        dt = self[adccols].values.reshape((self.shape[0]*4))
        timevec = linspace(0,self["time"].values[-1]+3e-3,num=dt.shape[0])
        return timevec,dt

    def getADC1kHzData(self):
        adccols = list(filter(lambda x: x.startswith("adc"), self.getSignalNames()))
        if len(adccols) == 0:
            raise BaseException("ADC data not found.")
        return self[adccols].values.reshape((self.shape[0]*4))

    def getNotes(self):
        if not self.hasLog:
            raise BaseException(f"Notes and logs not found in {self.filename}.")
        notes = self["log"].head(1).values.tolist()[0]
        if notes == "Started":
            raise BaseException(f"Notes not found in {self.filename}.")
        return notes

    def getLogs(self):
        if not self.hasLog:
            raise BaseException(f"No logs found in {self.filename}.")
        logs = self[["time","log"]][self["log"].notnull()].values.tolist()
        if logs[0][1] != "Started":
            logs = logs[1:]
        return logs        