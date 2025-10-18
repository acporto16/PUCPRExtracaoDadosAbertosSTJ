import os
import re
import unicodedata
from datetime import datetime


# Regex compilada para remover quebras de linha, tabs e tags <br> ou <br/>
CLEANING_PATTERN = re.compile(r'<br/?>|[\r\n\t]')


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

def _process_txt_content(content):
    """Função auxiliar para extrair seções de um conteúdo de texto."""
    if YEAR_DOWNLOAD == '2024':
        acordao = re.search('ACÓRDÃO\s*(?:</?br>\s*)*([\s\S]*?)\s*(?:</?br>\s*)*RELATÓRIO', content, re.DOTALL)
    else:
        acordao = re.search('ACÓRDÃO\s*(?:</?br>\s*)*([\s\S]*?)\s*(?:</?br>\s*)*EMENTA', content, re.DOTALL)
        #acordao = re.search(r'ACÓRDÃO<br>(.*?)<br>EMENTA<br>', content, re.DOTALL)

    if not acordao:
        return None

    if YEAR_DOWNLOAD == '2024':
        ementa = re.search(r'EMENTA\s*(?:</?br>\s*)*([\s\S]*?)\s*(?:</?br>\s*)*VOTO', content, re.DOTALL)
        relatorio = re.search(r'RELATÓRIO\s*(?:</?br>\s*)*([\s\S]*?)\s*(?:</?br>\s*)*EMENTA', content, re.DOTALL)
        voto = re.search(r'VOTO\s*(?:</?br>\s*)*([\s\S]*?)\s*(?:</?br>\s*)*', content, re.DOTALL)
        decisao = re.search(r'DECISÃO\s*(?:</?br>\s*)*([\s\S]*?)\s*(?:</?br>\s*)*', content, re.DOTALL)
    else:
        #ementa = re.search(r'<br>EMENTA<br>(.*?)RELATÓRIO<br>', content, re.DOTALL)

        if YEAR_DOWNLOAD == 2023:
            ementa = re.search(r'EMENTA\s*(?:</?br>\s*)*([\s\S]*?)\s*(?:</?br>\s*)*VOTO', content, re.DOTALL)
        else:
            ementa = re.search(r'EMENTA\s*(?:</?br>\s*)*([\s\S]*?)\s*(?:</?br>\s*)*RELATÓRIO', content, re.DOTALL)

        #relatorio = re.search(r'RELATÓRIO<br>(.*?)<br>VOTO<br>', content, re.DOTALL)
        relatorio = re.search(r'RELATÓRIO\s*(?:</?br>\s*)*([\s\S]*?)\s*(?:</?br>\s*)*VOTO', content, re.DOTALL)

        #voto = re.search(r'<br>VOTO<br>(.*)', content, re.DOTALL)
        voto = re.search(r'VOTO\s*(?:</?br>\s*)*([\s\S]*?)\s*(?:</?br>\s*)*', content, re.DOTALL)

        #decisao = re.search(r'DECISÃO<br>(.*)', content, re.DOTALL)
        decisao = re.search(r'DECISÃO\s*(?:</?br>\s*)*([\s\S]*?)\s*(?:</?br>\s*)*', content, re.DOTALL)

    # A função removeCRLF já está em utils.py, então podemos usá-la
    return (removeCRLF(acordao), removeCRLF(ementa), removeCRLF(relatorio),
            removeCRLF(voto), removeCRLF(decisao))


def _process_txt_content2(content):
    """
    Extrai seções de um conteúdo de texto, independentemente da ordem das tags.
    Busca por ACÓRDÃO, RELATÓRIO, EMENTA, VOTO, DECISÃO.
    """
    TAGS = ['ACÓRDÃO', 'RELATÓRIO', 'EMENTA', 'VOTO', 'DECISÃO']

    # Regex para encontrar qualquer uma das tags, ignorando <br> e espaços ao redor.
    # Captura a tag encontrada no grupo 1.
    tag_pattern = re.compile(r'(?:<br/?>|\s)*(' + '|'.join(TAGS) + r')\s*(?:<br/?>|\s)*')

    # Encontra todas as tags e suas posições
    found_tags = []
    for match in tag_pattern.finditer(content):
        # match.group(1) é a tag limpa (ex: 'EMENTA')
        # match.start() é a posição de início da tag no texto original
        found_tags.append({'tag': match.group(1), 'start': match.start(), 'end': match.end()})

    if not found_tags:
        return None

    # Ordena as tags pela posição em que aparecem no texto
    found_tags.sort(key=lambda x: x['start'])

    # Extrai o conteúdo entre as tags
    extracted_data = {}
    for i, current_tag_info in enumerate(found_tags):
        start_of_content = current_tag_info['end']

        # O fim do conteúdo é o início da próxima tag, ou o fim do texto se for a última tag
        end_of_content = found_tags[i + 1]['start'] if i + 1 < len(found_tags) else len(content)

        # Pega o texto e limpa com a função de utils
        text_slice = content[start_of_content:end_of_content]
        extracted_data[current_tag_info['tag']] = removeCRLFString(text_slice)

    # Retorna os dados na ordem padrão, usando .get() para o caso de uma tag não ser encontrada
    return (extracted_data.get('ACÓRDÃO', ''), extracted_data.get('EMENTA', ''),
            extracted_data.get('RELATÓRIO', ''), extracted_data.get('VOTO', ''),
            extracted_data.get('DECISÃO', ''))


