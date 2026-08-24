import os
from utils import (
    periodo_arquivo,
    tipo_documento_slug,
    load_config,
    normalize_classe_processual,
    normalize_regra_predicao,
    is_regra_predicao_valida,
)

# Carrega configurações do arquivo config.json
_config = load_config('config.json')

YEAR_DOWNLOAD = _config['year_download']
MONTH_DOWNLOAD = _config['month_download']
TIME_START_SYSTEM = _config['auto_start_seconds']
DEFAULT_START_CONFIRMATION = 'S'
CLASSE_PROCESSUAL_ALVO = normalize_classe_processual(_config.get('classe_processual', 'HC'))
FORCE_DOWNLOAD = str(_config.get('FORCE-DOWNLOAD', 'N')).strip().upper()
ANO_PUBLICACAO_DJE = _config.get('ANO-PUBLICACAO-DJE', '01/01/2021')
REGRA_PREDICAO = normalize_regra_predicao(_config.get('REGRA-PREDICAO', 'TEMPO'))
if not is_regra_predicao_valida(REGRA_PREDICAO):
    raise SystemExit("❌ Valor inválido para REGRA-PREDICAO no config.json. Use apenas 'TEMPO' ou 'DECISAO'.")

APLICAR_RESTRICAO_DATARECEBIMENTO = REGRA_PREDICAO == 'TEMPO'

# Mapeia o tipo de documento configurado para a lista esperada
_tipo_doc = _config['tipo_documento'].upper()
if _tipo_doc == 'DECISAO':
    LISTA_TIPO_DOCUMENTO = ['DECISÃO', 'DECISAO']
elif _tipo_doc == 'ACORDAO':
    LISTA_TIPO_DOCUMENTO = ['ACÓRDÃO', 'ACORDAO']
elif _tipo_doc == 'GERAL':
    LISTA_TIPO_DOCUMENTO = ['DECISÃO', 'DECISAO', 'ACÓRDÃO', 'ACORDAO']
else:
    LISTA_TIPO_DOCUMENTO = ['ACÓRDÃO', 'ACORDAO']  # Valor padrão

TIPO_DOCUMENTO_ARQUIVO = tipo_documento_slug(LISTA_TIPO_DOCUMENTO)
PERIODO_ARQUIVO = periodo_arquivo(YEAR_DOWNLOAD, MONTH_DOWNLOAD)

LIST_FIELDS = ['SEQDOCUMENTO', 'DATAPUBLICACAO', 'TIPODOCUMENTO', 'NUMEROREGISTRO', 'PROCESSO', 'DATARECEBIMENTO', 'DATADISTRIBUICAO' , 'MINISTRO','RECURSO', 'TEOR', 'DESCRICAOMONOCRATICA', 'ASSUNTOS']
DIR_PATH = os.path.join('C:\\', '_PUCPR', 'dados-stj')

ZIP_DIR_PATH = os.path.join(DIR_PATH, 'zip', YEAR_DOWNLOAD)
UNZIP_DIR_PATH = os.path.join(DIR_PATH, 'arquivos', YEAR_DOWNLOAD)

DIR_PATH_OUTPUT = os.path.join(DIR_PATH, 'output', YEAR_DOWNLOAD)
DIR_PATH_DOWNLOAD_DADOS_METADADOS = os.path.join(DIR_PATH, 'arquivos', YEAR_DOWNLOAD)
DIR_PATH_OUTPUT_DADOS_METADADOS = os.path.join(DIR_PATH, 'output', YEAR_DOWNLOAD, f'metadados-{TIPO_DOCUMENTO_ARQUIVO}-dj{PERIODO_ARQUIVO}.csv')
DIR_PATH_OUTPUT_DECISOES_ACORDAOS = os.path.join(DIR_PATH, 'output', YEAR_DOWNLOAD, f'dados-{TIPO_DOCUMENTO_ARQUIVO}-dj{PERIODO_ARQUIVO}.csv')

JSON_FILE_DOWNLOAD = f'metadados{YEAR_DOWNLOAD}'