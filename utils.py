import os
import re
from datetime import datetime


def ensure_dir_exists(dir_path):
    """Garante que um diretório exista, criando-o se necessário."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"   -> Diretório criado: {dir_path}")


def find_file_recursively(root_dir, filename):
    """
    Encontra um arquivo em um diretório e seus subdiretórios.

    :param root_dir: O diretório raiz para iniciar a busca.
    :param filename: O nome do arquivo a ser encontrado.
    :return: O caminho completo do arquivo se encontrado, caso contrário, None.
    """
    for dirpath, _, filenames in os.walk(root_dir):
        if filename in filenames:
            return os.path.join(dirpath, filename)
    return None


def log_event(log_dir, message):
    """
    Registra uma mensagem com data e hora em um arquivo de log.

    :param log_dir: O diretório onde o arquivo de log será salvo.
    :param message: A mensagem a ser registrada.
    """
    ensure_dir_exists(log_dir)
    log_file_path = os.path.join(log_dir, 'file_not_found.log')
    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    with open(log_file_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"[{timestamp}] - {message}\n")

# Regex compilada para remover quebras de linha, tabs e tags <br> ou <br/>
CLEANING_PATTERN = re.compile(r'<br/?>|[\r\n\t]')

def removeCRLF(field):
    """Remove quebras de linha e tabulações de um objeto de match regex."""
    return re.sub(r'[\r\n\t]', '', field.group(1)) if field else ''


def removeCRLFString(text):
    """Remove quebras de linha e tabulações de uma string."""
    return re.sub(r'[\r\n\t]', '', text) if text else ''

def removeCLRLBR(text):
    return CLEANING_PATTERN.sub('', text) if text else ''