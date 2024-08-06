"""
Ferramenta para download de pastas do Google Drive.

* Requer o arquivo DataChecker.py para executar.
"""

from DataChecker import drive_importer

if "__main__" == __name__:
    print("Entre os urls das pastas desejadas, separados por \", \" (vírgula + espaço) :")
    urls = input("--> ")
    urls_list = urls.split(", ")
    
    for url in urls_list:
        drive_importer(url, quiet=False)