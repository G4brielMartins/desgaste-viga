import os
from functools import wraps
from multiprocessing import Pool
from typing import Callable, Iterable, Any

import numpy as np
import pandas as pd

from scipy.signal import find_peaks
from Tools.DataChecker import DataHandler


class PathError(Exception):
    # Erro para sinalizar nomenclatura incopatível de pastas e/ou arquivos.
    def __init__(self, path: str|os.PathLike):
        mensagem = f"Formatação inválida do caminho {path}\n"
        super().__init__(mensagem)


def atuador(path: str|os.PathLike) -> int:
    """
    Retorna o atuador utilizado na amostra.

    Parameters
    ----------
    path : str | os.PathLike
        Caminho do arquivo referente à amostra.

    Returns
    -------
    int
        Índice do atuador (1 -> dac1, 2 -> dac2 ...)
    """
    file_name = os.path.basename(path)
    try:
        atuador = int(file_name.split("_")[1][1])
    except (IndexError, ValueError) as exc:
        raise PathError(path) from exc
    
    return atuador


def desgaste(path: str|os.PathLike) -> int:
    """
    Retorna o nível de desgaste da amostra.

    Parameters
    ----------
    path : str | os.PathLike
        Caminho do arquivo referente à amostra.

    Returns
    -------
    int
        Nível de desgaste (0 -> viga intacta)
    """
    dir_path = os.path.dirname(path)
    try:
        dir = dir_path[dir_path.rfind('Viga'):]
        desgaste_lvl = 0 if dir.find('Intacta') > 0 else int(dir[-1])
    except (IndexError, ValueError) as exc:
        raise PathError(path) from exc
    
    return desgaste_lvl


def enable_arguments_list(func: Callable) -> Any:
    """
    Decorador para habilitar que a função receba uma lista de argumentos.
    Utilizado para dar suporte ao uso da biblioteca multiprocessing.
    *Substituído pela implementação com pool.starmap() - facilita rotulagem, mas é menos eficiente.
    """
    @wraps(func)
    def wrappper(*args, **kwargs):
        if isinstance(args[0], Iterable) and len(args) == 1:
            args = args[0]
        return func(*args, **kwargs)
        
    return wrappper


def gerar_resposta_em_frequencia(feather: str|os.PathLike, dac: int, imu: str) -> np.array:
    data = DataHandler(feather, dac=f'dac{dac}', imu=imu)
    data.generate_fir_freq()
    
    return np.array(data.fir_freq)


def achar_ressonancias(feather: str|os.PathLike, imu: str, altura_rel: float = .33, 
                       distancia: int = 8, proeminencia: float = 30) -> tuple[list[float],list[float]]:
    """
    Encontra as frequências de ressonância identificadas na amostra e sua amplitude.
    Os argumentos configuram a função scipy.signal.find_peaks() (documentação disponível em https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html)

    Parameters
    ----------
    feather : str | os.PathLike
        Caminho do arquivo feader com os dados da amostra.
    imu : str
        Sensor IMU de interesse (imu1accz, imu2gyroy ...)
    distancia : int, optional
        Ajuste de sensibilidade pela distância mínima entre dois picos.
        Por padrão, assume o valor 10.
    altura_rel : float, optional
        Ajuste de sensibilidade pela amplitude do pico em relação à média.
        Por padrão, assume o valor .33 (picos devem ser .3 vezes maiores que a média)
    proeminencia : float, optional
        Ajuste de sensibilidade pela proeminencia do pico.
        Por padrão, assume o valor 30.
        
    Returns
    -------
    amplitudes : list[float]
        Lista de amplitudes em cada frequência de ressonância.
    ressonanicas : list[float]
        Lista de frequências de ressonância da amostra.
    """
    dac = atuador(feather)
    fir_freq = gerar_resposta_em_frequencia(feather, dac, imu)

    altura = np.mean(fir_freq[0]) + abs(np.mean(fir_freq[0]) * altura_rel)
    picos = find_peaks(fir_freq[0], height=altura, width=distancia, prominence=proeminencia)[0]
    np_data = np.array([fir_freq[:, i] for i in picos])
    amplitudes, ressonancias = np.split(np_data, 2, 1)
    
    return amplitudes, ressonancias


def achar_feathers(pasta: str|os.PathLike) -> list[str]:
    """
    Encontra todos os arquivos feather na pasta com uma busca recursiva.

    Parameters
    ----------
    pasta : str | os.PathLike
        Caminho do diretório onde será iniciada a busca recursiva.

    Returns
    -------
    list[str]
        Lista de caminhos dos arquivos feather encontrados.
    """
    buffer = []
    def loop(path):
        for i in os.listdir(path):
            p = os.path.join(path, i)
            if os.path.isdir(p):
                loop(p)
            elif i.endswith(".feather"):
                buffer.append(p)
    loop(pasta)
    
    return buffer


def agrupar_por_desgaste(feather_paths: list[str|os.PathLike], *, niveis_desgaste: int = 9) -> list[list[str]]:
    """
    Separa os arquivos fornecidos pelo seu nível de desgaste.

    Parameters
    ----------
    feather_paths : list[str | os.PathLike]
        Lista com os arquivos a serem organizados.
    niveis_desgaste : int
        Quantidade de níveis de desgaste presenetes nos dados. (Deve ser maior ou igual a quantidade real)

    Returns
    -------
    list[list[str]]
        Lista de amostras separadas por desgaste.
        Os índices da lista correspondem ao desgaste (lista[3] retorna uma lista com todas as amostras de desgaste nível 3)
    """
    sorted_paths = [[None] for _ in range(niveis_desgaste)]
    for path in feather_paths:
        d = desgaste(path)
        if sorted_paths[d][0] is None:
            sorted_paths[d][0] = path
        else:
            sorted_paths[d].append(path)
            
    return sorted_paths    
    
    
def importar_respostas_em_frequencia(path: str|os.PathLike, imus = list[str]) -> pd.DataFrame:
    feathers_paths = achar_feathers(path)
    feathers_agrupados = agrupar_por_desgaste(feathers_paths)
    
    dfs = []
    for desgaste_lvl, feathers in enumerate(feathers_agrupados):
        if feathers == [None]:
            continue # ignora níveis de desgaste sem amostras
        
        name_tags = [os.path.basename(feather)[:-8] for feather in feathers]
        for imu in imus:
            inputs = [(feather, atuador(feather), imu) for feather in feathers]
            with Pool() as pool:
                amplitudes = [i[0] for i in pool.starmap(gerar_resposta_em_frequencia, inputs)]
            index = pd.MultiIndex.from_product([[desgaste_lvl], name_tags], names= ["Desgaste", "Amostra"])
            dfs.append(pd.DataFrame(amplitudes, index=index))
    
    return pd.concat(dfs)