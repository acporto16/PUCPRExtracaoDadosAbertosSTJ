import os
import re
import unicodedata
import json
from datetime import datetime
from functools import lru_cache


_runtime_config_override = {}

_HEADER_KEY_ALIASES = {
    'NM_MINISTRO': 'MINISTRO',
}


def normalize_toggle_flag(value, default='N'):
    """Normaliza flags S/N. Valores inválidos caem no default."""
    if value is None:
        return default

    value_text = str(value).strip().upper()
    if value_text in ('S', 'N'):
        return value_text
    return default


def normalize_month_download(value):
    """Normaliza month_download: vazio/0/inválido/None => None; meses válidos => 'MM'."""
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value or value.lower() == 'none' or value == '0':
            return None

    if isinstance(value, bool):
        return None

    value_text = str(value).strip()
    if value_text.isdigit():
        month_int = int(value_text)
        if month_int == 0:
            return None
        if 1 <= month_int <= 12:
            return str(month_int).zfill(2)

    return None


def set_runtime_config_override(config_data):
    """Define overrides de configuração válidos apenas para a execução atual."""
    global _runtime_config_override
    if isinstance(config_data, dict):
        normalized_config = dict(config_data)
        normalized_config['AUTO-LOADING'] = normalize_toggle_flag(
            normalized_config.get('AUTO-LOADING', normalized_config.get('auto_loading', 'N')),
            default='N'
        )
        if 'month_download' in normalized_config:
            normalized_config['month_download'] = normalize_month_download(normalized_config.get('month_download'))
        _runtime_config_override = normalized_config
    else:
        _runtime_config_override = {}


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


def build_file_index_recursively(root_dir, suffix_filter=None):
    """
    Cria um índice {nome_do_arquivo: caminho_completo} varrendo o diretório recursivamente.
    Mantém o primeiro arquivo encontrado para cada nome, preservando o comportamento de busca sequencial.
    """
    index = {}

    if not os.path.exists(root_dir):
        return index

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if suffix_filter and not filename.endswith(suffix_filter):
                continue

            index.setdefault(filename, os.path.join(dirpath, filename))

    return index


def log_event(log_dir, message):
    """Registra uma mensagem com data e hora em um arquivo de log."""
    log_event_to_file(log_dir, message, 'file_not_found.log')


def log_event_to_file(log_dir, message, file_name):
    """Registra uma mensagem com data e hora em um arquivo de log específico."""
    ensure_dir_exists(log_dir)
    log_file_path = os.path.join(log_dir, file_name)
    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    with open(log_file_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"[{timestamp}] - {message}\n")


def log_relatorio_not_found(log_dir, message):
    """Registra ocorrências em que o campo RELATORIO permaneceu vazio."""
    log_event_to_file(log_dir, message, 'report_not_found.txt')


def removeCRLF(field):
    """Remove quebras de linha, tabs e tags <br> de um objeto de match regex."""
    return CLEANING_PATTERN.sub('', field.group(1)) if field else ''


def removeCRLFString(text):
    """Remove quebras de linha, tabs e tags <br> de uma string."""
    return CLEANING_PATTERN.sub('', text) if text else ''


def normalize_output_value(value):
    """Normaliza valor para saída textual, removendo espaços em branco nas extremidades."""
    if value is None:
        return ''

    if isinstance(value, str):
        return value.strip()

    return str(value).strip()

def _format_datetime_to_br_date(value):
    """Formata datetime no padrão brasileiro sem hora."""
    return value.strftime('%d/%m/%Y')


def _parse_numeric_date_value(value_text):
    """Interpreta datas numéricas em formatos comuns do STJ (timestamp e YYYYMMDD)."""
    if not value_text or not value_text.isdigit():
        return None

    try:
        if len(value_text) == 8 and value_text[:4].isdigit():
            return datetime.strptime(value_text, '%Y%m%d')

        numeric_value = int(value_text)

        if len(value_text) >= 13 or numeric_value > 10000000000:
            return datetime.utcfromtimestamp(numeric_value / 1000)

        if len(value_text) >= 10:
            return datetime.utcfromtimestamp(numeric_value)
    except (ValueError, OSError, OverflowError):
        return None

    return None


def _parse_textual_date_value(value_text):
    """Interpreta datas textuais nos formatos ISO e brasileiro, com ou sem hora."""
    if not value_text:
        return None

    iso_candidate = value_text.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(iso_candidate)
    except ValueError:
        pass

    known_formats = (
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%d/%m/%Y',
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M',
    )

    for fmt in known_formats:
        try:
            return datetime.strptime(value_text, fmt)
        except ValueError:
            continue

    return None


def convert_timestamp_to_date(timestamp):
    '''
    Normaliza datas em formatos heterogêneos para o padrão brasileiro DD/MM/YYYY.

    Aceita:
    - timestamp em milissegundos ou segundos (int, float ou string numérica)
    - YYYYMMDD
    - YYYY-MM-DD
    - DD/MM/YYYY
    - variantes com hora e/ou timezone ISO

    :param timestamp: Valor de data em formato numérico ou textual
    :return: String formatada em DD/MM/YYYY ou valor original se não for possível interpretar
    '''
    if not timestamp:
        return ''

    try:
        if isinstance(timestamp, datetime):
            return _format_datetime_to_br_date(timestamp)

        if isinstance(timestamp, (int, float)) and not isinstance(timestamp, bool):
            numeric_text = str(int(timestamp)) if isinstance(timestamp, float) and timestamp.is_integer() else str(timestamp)
            parsed_date = _parse_numeric_date_value(numeric_text.replace('.', ''))
            if parsed_date:
                return _format_datetime_to_br_date(parsed_date)

        value_text = str(timestamp).strip()
        if not value_text:
            return ''

        parsed_date = _parse_numeric_date_value(value_text)
        if parsed_date:
            return _format_datetime_to_br_date(parsed_date)

        parsed_date = _parse_textual_date_value(value_text)
        if parsed_date:
            return _format_datetime_to_br_date(parsed_date)

        return value_text
    except (ValueError, TypeError, OSError, OverflowError):
        return str(timestamp)

@lru_cache(maxsize=2048)
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

    return _HEADER_KEY_ALIASES.get(chave_final, chave_final)


def normalize_tipo_documento(value: str) -> str:
    """Normaliza texto para comparação (sem acento, minúsculo, sem espaços extras)."""
    if not isinstance(value, str):
        return ''
    return unicodedata.normalize('NFD', value).encode('ascii', 'ignore').decode('utf-8').strip().lower()


def normalize_classe_processual(value: str) -> str:
    """Normaliza classe processual removendo espaços e convertendo para maiúsculo."""
    if not isinstance(value, str):
        return ''
    return re.sub(r'\s+', '', value).strip().upper()


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
    month_download = normalize_month_download(month_download)
    if month_download is None:
        return str(year_download)
    return f"{str(month_download).zfill(2)}{year_download}"


def load_config(config_path='config.json'):
    """
    Carrega configurações de um arquivo JSON.
    Se o arquivo não existir, retorna valores padrão.
    """
    default_config = {
        'year_download': '2021',
        'month_download': None,
        'tipo_documento': 'ACORDAO',
        'classe_processual': 'HC',
        'FORCE-DOWNLOAD': 'N',
        'AUTO-LOADING': 'N',
        'auto_start_seconds': 3
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as config_file:
                loaded_config = json.load(config_file)
                if 'force_download' in loaded_config and 'FORCE-DOWNLOAD' not in loaded_config:
                    loaded_config['FORCE-DOWNLOAD'] = loaded_config.get('force_download')
                if 'auto_loading' in loaded_config and 'AUTO-LOADING' not in loaded_config:
                    loaded_config['AUTO-LOADING'] = loaded_config.get('auto_loading')
                # Mescla com valores padrão para garantir que todas as chaves existem
                merged_config = {**default_config, **loaded_config, **_runtime_config_override}
                merged_config['month_download'] = normalize_month_download(merged_config.get('month_download'))
                merged_config['AUTO-LOADING'] = normalize_toggle_flag(merged_config.get('AUTO-LOADING', 'N'))
                return merged_config
        else:
            merged_config = {**default_config, **_runtime_config_override}
            merged_config['month_download'] = normalize_month_download(merged_config.get('month_download'))
            merged_config['AUTO-LOADING'] = normalize_toggle_flag(merged_config.get('AUTO-LOADING', 'N'))
            return merged_config
    except Exception as e:
        print(f"⚠️ Erro ao carregar configuração: {e}. Usando valores padrão.")
        merged_config = {**default_config, **_runtime_config_override}
        merged_config['month_download'] = normalize_month_download(merged_config.get('month_download'))
        merged_config['AUTO-LOADING'] = normalize_toggle_flag(merged_config.get('AUTO-LOADING', 'N'))
        return merged_config


def save_config(config_data, config_path='config.json'):
    """
    Salva configurações em um arquivo JSON.
    """
    try:
        data_to_save = dict(config_data)
        if 'month_download' in data_to_save:
            data_to_save['month_download'] = normalize_month_download(data_to_save.get('month_download'))
        data_to_save['AUTO-LOADING'] = normalize_toggle_flag(
            data_to_save.get('AUTO-LOADING', data_to_save.get('auto_loading', 'N')),
            default='N'
        )
        with open(config_path, 'w', encoding='utf-8') as config_file:
            json.dump(data_to_save, config_file, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"⚠️ Erro ao salvar configuração: {e}")
        return False
