import os

DIR_PATH = os.path.join('C:\\', '_PUCPR', 'dados-stj')

ZIP_DIR_PATH = os.path.join(DIR_PATH, 'zip', '2025')
UNZIP_DIR_PATH = os.path.join(DIR_PATH, 'arquivos', '2025')

DIR_PATH_DOWNLOAD_DADOS_METADADOS = os.path.join(DIR_PATH, 'arquivos', '2025')
DIR_PATH_OUTPUT_DADOS_METADADOS = os.path.join(DIR_PATH, 'output', '2025', 'metadados-decisoes-acordaos-dj.csv')
DIR_PATH_OUTPUT_DECISOES_ACORDAOS = os.path.join(DIR_PATH, 'output', '2025', 'decisoes-acordaos-dj.csv')

JSON_FILE_PATH = r'metadados2025.json'
CSV_FILE_PATH = r'metadados2025.csv'

LIST_YEAR_DOWNLOAD = [2025,]