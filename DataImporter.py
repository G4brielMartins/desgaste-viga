import os
from functools import wraps
from typing import Callable, Iterable, Any

import numpy as np

from scipy.signal import find_peaks
from Tools.DataChecker import DataHandler


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
    atuador = int(file_name.split("_")[1][1])
    
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
    dir = dir_path[dir_path.rfind('Viga'):]
    desgaste_lvl = 0 if dir.find('Intacta') > 0 else int(dir[-1])
    
    return desgaste_lvl


def enable_arguments_list(func: Callable) -> Any:
    """
    Decorador para habilitar que a função receba uma lista de argumentos.
    Utilizado para dar suporte ao uso da biblioteca multiprocessing.
    """
    @wraps(func)
    def wrappper(*args, **kwargs):
        if isinstance(args[0], Iterable) and len(args) == 1:
            args = args[0]
        return func(*args, **kwargs)
        
    return wrappper


@enable_arguments_list
def achar_ressonancias(feather: str|os.PathLike, imu: str, *, distancia: int = 10) -> list[int]:
    """
    Encontra as frequências de ressonância identificadas na amostra.

    Parameters
    ----------
    feather : str | os.PathLike
        Caminho do arquivo feader com os dados da amostra.
    imu : str
        Sensor IMU de interesse (imu1accz, imu2gyroy ...)
    distancia : int, optional
        Ajuste de sensibilidade pela distância mínima entre dois picos.
        Por padrão, assume o valor 10.
    Returns
    -------
    list[int]
        Lista com o valor de cada frequência de ressonância, da menor para a maior.
    """
    dac_n = atuador(feather)
    
    data = DataHandler(feather, dac=f'dac{dac_n}', imu=imu)
    data.generate_fir_freq()
    fir_freq = np.array(data.fir_freq)

    altura = np.mean(fir_freq[0]) + abs(np.mean(fir_freq[0]) * .33)
    indices_picos = find_peaks(fir_freq[0], height=altura, width=distancia)[0]
    frequencias = [fir_freq[1, i] for i in indices_picos]
    
    return frequencias


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


def agrupar_por_desgaste(feather_paths: list[str|os.PathLike]) -> list[list[str]]:
    """
    Separa os arquivos fornecidos pelo seu nível de desgaste.

    Parameters
    ----------
    feather_paths : list[str | os.PathLike]
        Lista com os arquivos a serem organizados.

    Returns
    -------
    list[list[str]]
        Lista de amostras separadas por desgaste.
        Os índices da lista correspondem ao desgaste (lista[3] retorna uma lista com todas as amostras de desgaste nível 3)
    """
    sorted_paths = [[None] for _ in range(8)]
    for path in feather_paths:
        d = desgaste(path)
        if sorted_paths[d][0] is None:
            sorted_paths[d][0] = path
        else:
            sorted_paths[d].append(path)
            
    return sorted_paths