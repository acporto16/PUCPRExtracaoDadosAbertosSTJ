from lib import *
'''
    Autor: Alessandro C Porto
    Objeto: Extrair dados para montar dataset para pesquisa científica da PUCPR.
    
    Sugere-se executar os programa por etapas e observando a captura dos dados. No site dos dados abertos, alguns dados
    podem vir em padrões diferentes a depender do período, portanto, ajustes serão necessários durante a extração dos
    dados.
'''


#01
# if download_zip_files():
#     print("Zip files downloaded successfully")
# else:
#     print("Failed to download zip files")
#     exit()

#02
if download_json_metadados():
    print("JSON files downloaded successfully")
else:
    print("Failed to download JSON files")
    exit()

#03
if extract_zip_files():
    print("Zip files extracted successfully")
else:
    print("Failed to extract zip files")
    exit()

#04
if json_directory_to_csv(DIR_PATH_DOWNLOAD_DADOS_METADADOS, DIR_PATH_OUTPUT_DADOS_METADADOS):
    print("Success !!! CSV com metadados dos acórdãos e decisões gerado com sucesso.")
else:
    print("Fail...")
    exit()

#05
if read_txt_files_and_create_csv(DIR_PATH_DOWNLOAD_DADOS_METADADOS, DIR_PATH_OUTPUT_DECISOES_ACORDAOS):
    print("Success !!! CSV com os dados de acórdãos e decisões gerado com sucesso.")
else:
    print("Fail...")
    exit()
'''
#06
#clean_csv_empty_lines(DIR_PATH_OUTPUT_DECISOES_ACORDAOS, DIR_PATH_OUTPUT_DECISOES_ACORDAOS_CLEAN)
'''

exit()