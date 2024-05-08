"""
CLI para plot e verificação de integridade de dados gerados com o firmware ActVib.
"""

import os
from typing import Optional

import plotly.express as px

from ActVibModules.ActVibSystem import ActVibData
from ActVibModules.Adaptive import FIRNLMS
from ActVibModules.DSPFuncs import easyFourier

_PLT_WIDTH, _PLT_HEIGHT = 800, 300

class ConfigError(Exception):
    # Erro utilizado pela classe DataHolder para indicar que dac e/ou imu precisam ser definidos.
    def __init__(self):
        message = "O objeto não está configurado. Defina o dac e imu de interesse utilizando (self.set_config)."
        super().__init__(message)

class DataHolder():
    def __init__(self, path:str|os.PathLike, *, dac:Optional[str]= None, imu:Optional[str]= None):
        """
        Classe para armazenar informações referentes ao grupo de dados e facilitar sua manipulação.

        Parameters
        ----------
        path : str | os.PathLike
            Caminho do arquivo feather que contém os dados.
        dac : Optional[str], optional
            dac de interesse na análise
        imu : Optional[str], optional
            imu e a variável de interesse na análise - Ex.: 'imu2accz'
        
        * dac e imu podem ser fornecidos posteriormentes com set_config.
          Algumas funções ficam desabilitadas até a devida configuração de dac e imu.
        """
        self.name = os.path.basename(path)
        self.data = ActVibData(path)
        self.dac = dac
        self.imu = imu
    
    def is_config(self) -> bool:
        """
        Verifica se dac e imu estão configurados.

        Returns
        -------
        bool
            True se está configurado.
        """        
        return False if None in [self.dac, self.imu] else True
    
    def set_config(self, dac:Optional[str]= None, imu:Optional[str]= None) -> None:
        """
        Atribui valores ao dac e imu.

        Parameters
        ----------
        dac : Optional[str], optional
            Novo dac a ser utilizado.
        imu : Optional[str], optional
            Novos imu e variável a serem utilizados.
        """        
        if dac is not None:
            self.dac = dac
        if imu is not None:
            self.imu = imu
    
    def generate_fir(self) -> None:
        """
        Calcula a resposta ao impulso e armazena em (self.fir).
        * dac e imu precisam estar configurados.
        """                
        if self.is_config():
                self.fir = FIRNLMS(memorysize=2000)
                x = self.data[self.dac].values - self.data[self.dac].mean()
                y = self.data[self.imu].values - self.data[self.imu].mean()
                self.fir.run(x,y)
    
    def generate_fir_freq(self) -> None:
        """
        Calcula a resposta ao impulso no domínio da frequência e armazena em (self.fir_freq).
        * dac e imu precisam estar configurados.
        """        
        try:
            self.fir_freq = easyFourier(self.fir.ww,fs=416)
        except AttributeError:
            self.generate_fir()
            self.generate_fir_freq()
    
    def get_log(self) -> str:
        """
        Gera uma tabela de logs em formato de linha.

        Returns
        -------
        str
            Tabela de logs em formato str.
        """        
        log = f"{'Tempo':^10}|{'Log':>8}\n{'―'*26}"
        for line in self.data.getLogs():
            log += (f"\n {line[0]:<9}| {line[1]}")
        
        return log
    
    def plt_scatter(self, imus:list[str]= ['imu2accz', 'imu1accz']) -> None:
        """
        Plota o gráfico de dispersão dos dados armazenados.

        Parameters
        ----------
        imus : list[str], optional
            Lista de imus e variáveis a serem plotados. Por padrão ['imu2accz', 'imu1accz']
        """        
        fig = px.line(width=_PLT_WIDTH, height=_PLT_HEIGHT, title=self.name)
        for imu in imus:
            fig.add_scatter(x=self.data['time'], y=self.data[imu], name=imu)
        fig.show()
    
    def plt_fir(self) -> None:
        """
        Plota o gráfico da resposta ao impulso armazenada em (self.fir).
        Calcula (self.fir) caso este não exista.
        """        
        try:
            fig = px.line(self.fir.ww, width=_PLT_WIDTH, height=_PLT_HEIGHT, title=self.name)
            fig.show()
        except AttributeError:
            self.generate_fir()
            self.plt_fir()
    
    def plt_fir_freq(self) -> None:
        """
        Plota o gráfico da resposta ao impulso no domínio da frequência armazenada em (self.fir_freq).
        Calcula (self.fir_freq) caso este não exista.
        """        
        try:
            y, x = self.fir_freq
            fig = px.line(x=x, y=y, width=_PLT_WIDTH, height=_PLT_HEIGHT, title=self.name)
            fig.show()
        except AttributeError:
            self.generate_fir_freq()
            self.plt_fir_freq()

def main(args):
    data1 = DataHolder(args.path, dac='dac1', imu='imu2accz')
    
    if args.scatter or args.all:
        data1.plt_scatter()
    if args.impulse or args.all:
        data1.plt_fir()
    if args.freq or args.all:
        data1.plt_fir_freq()
        
if "__main__" == __name__:
    import argparse
    
    # Configuração do CLI
    parser = argparse.ArgumentParser(
        prog= "DataChecker",
        description= "Plot e análise de dados de vibração obtidos com o firmware Actvib",
        usage= "DataChecker [-h] [-s -i -f -a] FEATHER_PATH",
        add_help= False        
    )
    parser.add_argument('-h', '--help', action= 'help', default=argparse.SUPPRESS,
                        help= "escreve esta mensagem de ajuda e sai do programa")
    parser.add_argument('path', metavar= 'FEATHER_PATH',
                        help= "caminho do arquivo feather com os dados a serem análisados")

    # Configuração das flags de plot do CLI
    plots = parser.add_argument_group('plots', "Flags para configurar quais plots serão feitos")
    plots.add_argument('-s', '--scatter', action= 'store_true',
                        help= "plota o gráfico de dispersão da amostra")
    plots.add_argument('-i', '--impulse', action= 'store_true',
                        help= "plota o gráfico da resposta ao impulso")
    plots.add_argument('-f', '--freq', action= 'store_true',
                        help= "plota o gráfico da resposta ao impulso em frequência")
    plots.add_argument('-a', '--all', action= 'store_true',
                        help= "plota todos os gráficos (--scatter, --impulse, --freq)")
    args = parser.parse_args()
    
    if not (args.scatter or args.impulse or args.freq or args.all):
        parser.error("Nenhum plot solicitado. Forneça pelo menos uma flag para plotar")
    
    main(args)