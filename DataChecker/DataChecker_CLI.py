"""
CLI para plot e verificação de integridade de dados gerados com o firmware ActVib.
"""

from DataChecker import main
    
if "__main__" == __name__:
    import argparse
    
    # Configuração do CLI
    parser = argparse.ArgumentParser(
        prog= "DataChecker",
        description= "Plot e análise de dados de vibração obtidos com o firmware Actvib",
        usage= "DataChecker [-h] [-A] [-s -i -f -a] FEATHER_PATH DAC",
        add_help= False        
    )
    parser.add_argument('-h', '--help', action= 'help', default=argparse.SUPPRESS,
                        help= "escreve esta mensagem de ajuda e sai do programa")
    parser.add_argument('path', type= str, metavar= 'FEATHER_PATH',
                        help= "caminho do arquivo feather com os dados a serem análisados")
    parser.add_argument('dac', type= int, metavar= 'DAC',
                        help= "dac a ser utilizado (1, 2...)")
    parser.add_argument('-A', '--all_files', action= 'store_true',
                        help= "plota todos os arquivos sequencialmente (desabilita seletor de arquivos)")

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
    
    # Input handler
    graph_input_arr = [args.scatter, args.impulse, args.freq, args.all]
    graph_types = ['scatter', 'impulse', 'freq', 'all']
    
    selected_graphs = [graph_types[i] for i in range(len(graph_types)) if graph_input_arr[i]]
    
    main(args.path, selected_graphs, args.dac, args.all_files)
