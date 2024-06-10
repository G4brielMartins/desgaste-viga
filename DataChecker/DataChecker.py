"""
Programa para plot e verificação de integridade de dados gerados com o firmware ActVib.
"""

import os
from typing import Optional

import plotly.express as px

from ActVibModules.ActVibSystem import ActVibData
from ActVibModules.Adaptive import FIRNLMS
from ActVibModules.DSPFuncs import easyFourier

PLT_WIDTH, PLT_HEIGHT = 800, 300

class ConfigError(Exception):
    # Erro utilizado pela classe DataHolder
    def __init__(self):
        mensagem = "O objeto não está configurado. Defina o dac e imu de interesse utilizando (self.set_config)."
        super().__init__(mensagem)


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
          Algumas funções ficam desabilitadas até a devida configuração do dac e imu.
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
        fig = px.line(width=PLT_WIDTH, height=PLT_HEIGHT, title=self.name)
        for imu in imus:
            fig.add_scatter(x=self.data['time'], y=self.data[imu], name=imu)
        fig.show()
    
    def plt_fir(self) -> None:
        """
        Plota o gráfico da resposta ao impulso armazenada em (self.fir).
        Calcula (self.fir) caso este não exista.
        """        
        try:
            fig = px.line(self.fir.ww, width=PLT_WIDTH, height=PLT_HEIGHT, title=self.name)
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
            fig = px.line(x=x, y=y, width=PLT_WIDTH, height=PLT_HEIGHT, title=self.name)
            fig.show()
        except AttributeError:
            self.generate_fir_freq()
            self.plt_fir_freq()


def drive_importer(url: str) -> str:
    import gdown

    raiz = os.getcwd()
    os.chdir(output_dir)
    download(link, fuzzy=True)
    os.chdir(raiz)


def main(path: str|os.PathLike, graphs: list[str], dac: str, plot_all: bool = False):
    def plot_data(feather_path):
        data = DataHolder(feather_path, dac=dac, imu='imu2accz')
        
        graph_plotters = {'scatter':    data.plt_scatter,
                          'impulse':    data.plt_fir,
                          'freq':       data.plt_fir_freq}
        
        if 'all' in graphs:
            for plot in graph_plotters.values():
                plot()
            return None
        
        for graph in graphs:
            graph_plotters[graph]()
    
    if os.path.isfile(path):
        plot_data(path)
        return None
    
    # Se o caminho aponta uma pasta
    files = os.listdir(path) 
    file_paths = [os.path.join(path, file) for file in files]
    num_files = len(file_paths)
    
    i = 1
    def processar_input(user_input: str):
        nonlocal i, plot_all

        try:
            user_input = int(user_input)
        except ValueError:
            pass
            
        match user_input:
            case '':
                return False
            case 'q':
                return True
            case 'all':
                plot_all = True
                return False
            case str() if user_input in files:
                i = files.index(user_input)
                return False
            case int() if user_input <= num_files + 1:
                i = int(user_input)
                return False
            case _:
                new_in = input("Opção não suportada. Entre um valor válido: ")
                return processar_input(new_in)
    if not plot_all:
        print("Arquivos encontrados. Pressione enter para prosseguir ou digite 'q' para sair.")
        user_in = input("Para acessar um plot específico, digite o nome ou índice do arquivo. 'all' plota todos os arquivos. ")
        if processar_input(user_in): return None
    
    while True:
        if i > num_files:
            break

        print(f"Plotando arquivo {files[i-1]} ({i}/{num_files})...")
        plot_data(file_paths[i-1])

        i+= 1

        if plot_all: continue

        user_in = input("Plot concluído. Pressione enter para seguir ou digite sua opção: ")
        if processar_input(user_in): break

if "__main__" == __name__:
    print("Data Checker iniciado. Entre o caminho do arquivo ou pasta com arquivos a serem plotados. ")
    path = input("--> ")
    
    print("Defina o dac utilizado:")
    dac = input("--> ")

    print("\nOs gráficos disponíveis são:")
    print(" - scatter (dispersão)")
    print(" - impulse (resposta ao impulso)")
    print(" - freq (resposta ao impulso no domínio da frequência)")
    print(" - all (plota todos os gráficos)")
    
    graph_options = {'scatter', 'impulse', 'freq', 'all'}
    while True:
        print("Digite as opções desejadas, separadas por espaço, ou pressione enter para plotar todos.")
        input_graphs = input("--> ")
        
        if input_graphs == '':
            selected_graphs = ['all']
            break
        
        selected_graphs = input_graphs.split()
        if not (set(selected_graphs) - graph_options):
            break
    
    main(path, selected_graphs, dac)
