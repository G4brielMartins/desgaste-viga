"""
Programa para plot e verificação de integridade de dados gerados com o firmware ActVib.
O programa funciona independentemente, mas é um módulo essencial para o funcionamento das demais ferramentas.
"""

import os
from typing import Optional

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ActVibModules.ActVibSystem import ActVibData
from ActVibModules.Adaptive import FIRNLMS
from ActVibModules.DSPFuncs import easyFourier


class ConfigError(Exception):
    # Erro utilizado pela classe DataHandler
    def __init__(self, path: str|os.PathLike):
        mensagem = "O objeto não está configurado. Defina o dac e imu de interesse utilizando (self.set_config)."
        super().__init__(mensagem)


class DataHandler():
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
        else:
            raise ConfigError
    
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
    
    def get_scatters(self, imus:list[str]= ['imu2accz', 'imu1accz']) -> list[go.Scatter]:
        """
        Cria os traços de dispersão dos dados armazenados.

        Parameters
        ----------
        imus : list[str], optional
            Lista de imus a serem plotados. Por padrão ['imu2accz', 'imu1accz']

        Returns
        -------
        list[go.Scatter]
            Traços de dispersão gerados.
            * Devem ser adcionados em uma figura para realizar a plotagem.
        """
        traces = []
        for imu in imus:
            traces.append(go.Scatter(x=self.data['time'], y=self.data[imu], name=imu))
        return traces
        
    def get_fir(self) -> go.Scatter:
        """
        Cria o traço da resposta ao impulso armazenada em (self.fir).
        Calcula (self.fir) caso este não exista.

        Returns
        -------
        go.Scatter
            Traço da resposta ao impulso.
            * Deve ser adicionado a uma figura para realizar a plotagem.
        """
        try:
            y = self.fir.ww
            x = list(range(len(self.fir.ww)))
            trace = go.Scatter(x=x, y=y, mode='lines', name='Resposta ao Impulso')
        except AttributeError:
            self.generate_fir()
            trace = self.get_fir()
            
        return trace
    
    def get_fir_freq(self) -> go.Scatter:
        """
        Cria o traço da resposta ao impulso no domínio da frequência armazenada em (self.fir_freq).
        Calcula (self.fir_freq) caso este não exista.

        Returns
        -------
        go.Scatter
            Traço da resposta ao impulso no domínio da frequência.
            * Deve ser adicionado a uma figura para realizar a plotagem.
        """        
        try:
            y, x = self.fir_freq
            trace = go.Scatter(x=x, y=y, mode='lines', name='Resposta ao Impulso em Frequência') 
        except AttributeError:
            self.generate_fir_freq()
            trace = self.get_fir_freq()
        return trace


def drive_importer(url: str, *, out_folder: str = "Dados", quiet: bool = True) -> str:
    """
    Importa uma pasta do Google Drive para o diretório local 'Dados/'.

    Parameters
    ----------
    url : str
        Link da pasta do Google Drive.
        * O arquivo deve estar com acesso 'Qualquer pessoa com o link'
    """
    from gdown import download_folder
    
    if not os.path.exists(out_folder):
        os.mkdir(out_folder)
    
    raiz = os.getcwd()
    os.chdir(out_folder)
    paths = download_folder(url, quiet=quiet)
    os.chdir(raiz)

    folder_path = os.path.dirname(os.path.abspath(paths[0]))

    return folder_path


def main(path: str|os.PathLike, graphs: list[str], dac: int, plot_all: bool = False) -> None:
    """
    Corpo principal do programa.

    Parameters
    ----------
    path : str | os.PathLike
        Caminho da pasta, caminho do arquivo ou URL do Google Drive correspondente aos dados a serem plotados.
    graphs : list[str]
        Opções de gráficos selecionadas para plotagem.
    dac : int
        Índice do DAC a ser utilizado (1, 2, 3 ...).
    plot_all : bool, optional
        Flag para plotar todos os arquivos em sequência, ignorando o navegador de arquivos.
    """    
    def plot_data(feather_path: str|os.PathLike) -> None:
        """
        Função para plotagem dos dados a partir dos inputs do usuário.
        * Deve ser chamada somente no contexto da função main.

        Parameters
        ----------
        feather_path : str | os.PathLike
            Caminho do arquivo feather a ser plotado.
        
        Nonlocal Parameters
        ----------
        Estes parâmetros vêm do escopo da função main.
        
        graphs : list[str]
            Opções de gráficos selecionadas para plotagem.
        dac : int
            Índice do DAC a ser utilizado (1, 2, 3 ...).
        """                
        nonlocal graphs, dac
        
        data = DataHandler(feather_path, dac=f'dac{dac}', imu='imu2accz')
        fig = make_subplots(2, 2)
        fig.update_layout(title=data.name)
        get_trace = {'scatter': data.get_scatters,
                     'impulse':  data.get_fir,
                     'freq':    data.get_fir_freq}
        
        if 'all' in graphs:
            graphs = list(get_trace.keys())
        
        traces = []
        for graph in graphs:
            traces.append(get_trace[graph]())
        
        col=1
        if 'scatter' in graphs:
            scatters = traces.pop(0)
            for i, trace in enumerate(scatters):
                fig.add_trace(trace, row=i+1, col=col)
            col += 1
        
        for i, trace in enumerate(traces):
            fig.add_trace(trace, row=i+1, col=col)
        
        fig.show()

    # Se o caminho é um URL
    if path.startswith('http'):
        print("URL reconhecido.")
        path = drive_importer(path) # Atualiza o caminho para o local da pasta baixada
        print("Os dados foram baixados do Google Drive.\n")

    # Se o caminho aponta um arquivo
    if os.path.isfile(path):
        plot_data(path)
        return None
    
    # Se o caminho aponta uma pasta
    files = os.listdir(path) 
    file_paths = [os.path.join(path, file) for file in files]
    num_files = len(file_paths)
    
    # Configuração da interface de navegação entre arquivos
    i = 1
    def processar_input(user_input: str) -> bool:
        """
        Trata o input do usuário durante a nevegação entre arquivos.
        * Deve ser chamada somente no contexto da função main.

        Parameters
        ----------
        user_input : str
            O input do usuário.

        Returns
        -------
        bool
            Flag de solicitação de saída (True - encerra o programa).
        
        Nonlocal Parameters
        ----------
        Estes parâmetros vêm do escopo da função main.
        
        i : int
            Índice do arquivo selecionado pelo navegador de arquivos.
        plot_all : bool
            Flag para plotar todos os arquivos em sequência, ignorando o navegador de arquivos.
        """        
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
    
    # Loop do gerenciador de arquivos a serem plotados
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
    # Interface de terminal para coleta dos parâmetros utilizados na main
    print("Data Checker iniciado. Entre o caminho do arquivo ou pasta com arquivos a serem plotados. ")
    path = input("--> ")
    
    print("Defina o dac utilizado (1, 2...):")
    dac = int(input("--> "))

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
        
        print("Opção inválida. Entre apenas opções disponíveis.\n")
    
    main(path, selected_graphs, dac)