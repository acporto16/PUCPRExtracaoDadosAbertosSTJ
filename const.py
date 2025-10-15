import os

DIR_PATH = os.path.join('C:\\', '_PUCPR', 'dados-stj')
DIR_PATH_DOWNLOAD_DADOS_METADADOS = os.path.join(DIR_PATH, 'arquivos')
DIR_PATH_OUTPUT_DADOS_METADADOS = os.path.join(DIR_PATH, 'output', 'metadados-decisoes-acordaos-dj.csv')
DIR_PATH_OUTPUT_DECISOES_ACORDAOS = os.path.join(DIR_PATH, 'output', 'decisoes-acordaos-dj.csv')
DIR_PATH_OUTPUT_DECISOES_ACORDAOS_CLEAN = os.path.join(DIR_PATH, 'output', 'decisoes-acordaos-dj-clean.csv')

ZIP_DIR_PATH = os.path.join(DIR_PATH, 'zip')
UNZIP_DIR_PATH = os.path.join(DIR_PATH, 'arquivos')
JSON_FILE_PATH = r'metadados20251008.json'
CSV_FILE_PATH = r'metadados20251008.csv'
LIST_YEAR_DOWNLOAD = [2025,]