import os
import re
import unicodedata
from datetime import datetime


# Regex compilada para remover quebras de linha, tabs e tags <br> ou <br/>
CLEANING_PATTERN = re.compile(r'<br/?>|[\r\n\t]')

def ensure_dir_exists(dir_path):
    """Garante que um diretório exista, criando-o se necessário."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"   -> Diretório criado: {dir_path}")


def find_file_recursively(root_dir, filename):
    """Encontra um arquivo em um diretório e seus subdiretórios."""
    for dirpath, _, filenames in os.walk(root_dir):
        if filename in filenames:
            return os.path.join(dirpath, filename)
    return None


def log_event(log_dir, message):
    """Registra uma mensagem com data e hora em um arquivo de log."""
    ensure_dir_exists(log_dir)
    log_file_path = os.path.join(log_dir, 'file_not_found.log')
    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    with open(log_file_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"[{timestamp}] - {message}\n")


def removeCRLF(field):
    """Remove quebras de linha, tabs e tags <br> de um objeto de match regex."""
    return CLEANING_PATTERN.sub('', field.group(1)) if field else ''


def removeCRLFString(text):
    """Remove quebras de linha, tabs e tags <br> de uma string."""
    return CLEANING_PATTERN.sub('', text) if text else ''

def convert_timestamp_to_date(timestamp):
    '''
    Converte timestamp em formato legível de data
    :param timestamp: Timestamp em milissegundos ou segundos
    :return: String formatada de data ou valor original se não for timestamp
    '''
    if not timestamp:
        return ''

    try:
        # Tentar converter assumindo milissegundos
        if isinstance(timestamp, (int, float)):
            # Se o timestamp for muito grande, provavelmente está em milissegundos
            if timestamp > 10000000000:
                timestamp = timestamp / 1000

            data = datetime.fromtimestamp(timestamp)
            return data.strftime('%d/%m/%Y %H:%M:%S')
        else:
            return str(timestamp)
    except (ValueError, TypeError, OSError):
        # Se falhar, retornar como string
        return str(timestamp)

def normalize_header_key(key: str) -> str:
    """
    Normaliza uma string para ser usada como chave de cabeçalho de CSV.
    - Converte para maiúsculas.
    - Remove acentos.
    - Substitui espaços e hífens por underscore.
    - Remove todos os outros caracteres não alfanuméricos (exceto underscore).
    """
    if not isinstance(key, str):
        return ''

    # Remove acentos (ex: 'ACÓRDÃO' -> 'ACORDAO')
    sem_acentos = unicodedata.normalize('NFD', key).encode('ascii', 'ignore').decode('utf-8')

    # Converte para maiúsculas
    em_maiusculo = sem_acentos.upper()

    # Substitui espaços e hífens por underscore
    com_underscore = re.sub(r'[\s-]', '_', em_maiusculo)

    # Remove qualquer caractere que não seja letra, número ou underscore
    chave_final = re.sub(r'[^A-Z0-9_]', '', com_underscore)

    return chave_final


def normalize_tipo_documento(value: str) -> str:
    """Normaliza texto para comparação (sem acento, minúsculo, sem espaços extras)."""
    if not isinstance(value, str):
        return ''
    return unicodedata.normalize('NFD', value).encode('ascii', 'ignore').decode('utf-8').strip().lower()


def tipo_documento_slug(lista_tipo_documento):
    """
    Retorna slug elegante para nome de arquivo:
    - DECISÃO/DECISAO -> decisoes
    - ACÓRDÃO/ACORDAO -> acordaos
    Fallback: normalizado + 's'
    """
    if not lista_tipo_documento:
        return 'documentos'

    base = normalize_tipo_documento(lista_tipo_documento[0])

    mapa = {
        'decisao': 'decisoes',
        'acordao': 'acordaos',
    }
    return mapa.get(base, f'{base}s' if base else 'documentos')


def periodo_arquivo(year_download, month_download):
    """Monta sufixo temporal para o arquivo: YYYY ou MMYYYY."""
    if month_download is None:
        return str(year_download)
    return f"{str(month_download).zfill(2)}{year_download}"


