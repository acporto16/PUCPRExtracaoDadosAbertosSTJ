import json
import csv
import requests
import zipfile
from requests import Session
from const import *
from utils import *

# Conjuntos fixos para lookup O(1) por campo — evitam comparação linear por linha
_DATE_FIELDS = frozenset({'DATAPUBLICACAO', 'DATADISTRIBUICAO', 'DATAJULGAMENTO', 'DATARECEBIMENTO'})
_TEXT_CLEAN_FIELDS = frozenset({'RECURSO', 'TEOR', 'DESCRICAOMONOCRATICA'})
_LISTA_TIPO_DOC_SET = frozenset(v.upper() for v in LISTA_TIPO_DOCUMENTO)


def _directory_contains_matching_files(directory_path, matcher):
    """Verifica se existe ao menos um arquivo compatível no diretório/subdiretórios."""
    if not os.path.exists(directory_path):
        return False

    try:
        for dirpath, _, filenames in os.walk(directory_path):
            for filename in filenames:
                if matcher(filename):
                    return True
    except Exception:
        return False

    return False


def _safe_remove_file(file_path):
    """Remove arquivo, ignorando falha e registrando log se necessário."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        log_event(DIR_PATH_OUTPUT, f"Falha ao remover arquivo temporário/inválido '{file_path}'. Detalhe: {e}")


_LIST_FIELDS_SET = frozenset(normalize_header_key(f) for f in LIST_FIELDS)


def _check_for_duplicate_keys(ordered_pairs):
    """Hook para o json.load que verifica chaves duplicadas."""
    d = {}
    for key, value in ordered_pairs:
        if key in d:
            raise ValueError(f"Chave duplicada encontrada: '{key}'")
        d[key] = value
    return d


    try:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {file_path}")
        return None

def _format_json_data(data, indent=0):
    formatted = ""
    if isinstance(data, dict):
        for key, value in data.items():
            formatted += " " * indent + f"{key}: "
            if isinstance(value, (dict, list)):
                formatted += "\n" + _format_json_data(value, indent + 4)
            else:
                formatted += f"{value}\n"
    elif isinstance(data, list):
        for index, item in enumerate(data):
            formatted += " " * indent + f"[{index}]:\n"
            formatted += _format_json_data(item, indent + 4)
    return formatted


def json_to_csv(data, csv_file_path):
    '''
    Converte dados JSON (lista de dicionários) para arquivo CSV

    :param data: Lista de dicionários com os dados
    :param csv_file_path: Caminho do arquivo CSV de saída
    :return: bool - True se sucesso, False se falha
    '''
    # Validação de entrada
    if not data:
        print("Aviso: Dados vazios fornecidos para conversão")
        return False

    if not isinstance(data, list):
        print("Erro: Dados devem ser uma lista")
        return False

    if not all(isinstance(item, dict) for item in data):
        print("Erro: Todos os itens devem ser dicionários")
        return False

    try:
        # Coletar todas as chaves únicas mantendo a ordem do primeiro registro
        ordered_keys = []
        ordered_keys_set = set()
        if data:
            # Preservar ordem das chaves do primeiro registro
            ordered_keys = [normalize_header_key(key) for key in data[0].keys()]
            ordered_keys_set = set(ordered_keys)
            original_keys_map = {normalize_header_key(key): key for key in data[0].keys()}

            # Adicionar chaves que aparecem em outros registros (schemas diferentes entre arquivos)
            for item in data[1:]:
                for key in item.keys():
                    normalized_key = normalize_header_key(key)
                    if normalized_key not in ordered_keys_set:
                        ordered_keys.append(normalized_key.upper())
                        ordered_keys_set.add(normalized_key.upper())
                        original_keys_map[normalized_key] = key.upper()

        print(f"Convertendo {len(data)} registros com {len(ordered_keys)} campos para CSV...")

        # Garante que o diretório de saída exista antes de escrever o arquivo
        output_dir = os.path.dirname(csv_file_path)
        ensure_dir_exists(output_dir)

        # Escrever arquivo CSV
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)

            # Escrever cabeçalho
            writer.writerow(ordered_keys)

            ignorar_registro = False
            # Escrever linhas de dados
            for idx, item in enumerate(data, 1):
                row = []

                value = get_value_case_insensitive(item, 'tipoDocumento', original_keys_map)
                #considerar apenas o tipo de documento especificado na constante TIPO_DOCUMENTO
                if value.upper() not in _LISTA_TIPO_DOC_SET:
                    continue

                for key in ordered_keys:
                    value = get_value_case_insensitive(item, key, original_keys_map)

                    if key == 'SEQDOCUMENTO' and not value:
                        source_file = item.get('_source_file', 'desconhecido')
                        log_event(DIR_PATH_OUTPUT, f"Registro com SEQDOCUMENTO vazio encontrado no arquivo '{source_file}'. Registro: {item}")
                        ignorar_registro = True
                        break  # sai do loop e registra controle para não gravar registro
                    try:
                        # Tratamento especial para campos de data
                        if key in _DATE_FIELDS:
                            value = convert_timestamp_to_date(value)
                        elif key in _TEXT_CLEAN_FIELDS:
                            value = removeCRLFString(value)
                        # Tratamento para listas e dicionários
                        elif isinstance(value, (list, dict)):
                            value = json.dumps(value, ensure_ascii=False)
                        # Tratamento para None
                        elif value is None:
                            value = ''
                        else:
                            value = str(value)
                    except Exception as e:
                        log_event(DIR_PATH_OUTPUT, f'Erro inesperado ao tratar campo "{key}" com valor "{value}": Detalhe do erro: "{e}".')
                        ignorar_registro = True
                        break

                    row.append(value)

                if not ignorar_registro:
                    writer.writerow(row)
                else:
                    ignorar_registro = False

                # Mostrar progresso a cada 1000 registros
                if idx % 1000 == 0:
                    print(f"  Processados {idx} registros...")

        print(f"✅ CSV criado com sucesso: {csv_file_path}")
        print(f"   Total de registros: {len(data)}")
        print(f"   Total de campos: {len(ordered_keys)}")
        return True

    except PermissionError:
        print(f"❌ Erro: Sem permissão para escrever em {csv_file_path}")
        return False
    except IOError as e:
        print(f"❌ Erro de I/O ao escrever arquivo CSV: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado ao converter para CSV: {e}")
        return False


def get_value_case_insensitive(item, normalized_key, original_keys_map):
    """
    Obtém um valor de um dicionário de forma insensível a maiúsculas/minúsculas,
    especialmente para a chave 'SEQDOCUMENTO'.
    """
    # Se o item foi localizado normalmente, encerramos e já devolvemos o valor
    original_key = original_keys_map.get(normalized_key, normalized_key)
    value =  item.get(original_key, '')
    if value:
        return value

    # Para a chave SEQDOCUMENTO, fazemos uma busca case-insensitive
    if normalized_key == 'SEQDOCUMENTO':
        for item_key, item_value in item.items():
            if normalize_header_key(item_key) in _LIST_FIELDS_SET:
                return item_value
        return ''  # Retorna vazio se nenhuma variação for encontrada

def read_all_json_files_from_directory(directory_path):
    """
    Lê todos os arquivos JSON de um diretório e seus subdiretórios, e retorna uma lista consolidada de dados.

    :param directory_path: Caminho do diretório contendo os arquivos JSON
    :return: Lista consolidada com todos os registros de todos os arquivos JSON
    """
    all_data = []
    json_files = []

    # Verificar se o diretório existe
    if not os.path.exists(directory_path):
        print(f"❌ Erro: Diretório não encontrado: {directory_path}")
        return None

    # Percorre o diretório e todos os seus subdiretórios
    try:
        print(f"\n🔎 Procurando arquivos .json recursivamente em: {directory_path}")
        for dirpath, _, filenames in os.walk(directory_path):
            for filename in filenames:
                if filename.endswith('.json'):
                    # Adiciona o caminho completo do arquivo à lista
                    json_files.append(os.path.join(dirpath, filename))

        if not json_files:
            print(f"⚠️ Nenhum arquivo JSON encontrado em: {directory_path}")
            return []

        print(f"\n📂 Encontrados {len(json_files)} arquivos JSON.")

        # Ler cada arquivo JSON
        for file_path in sorted(json_files):
            # Mostra o caminho relativo para uma saída mais limpa
            relative_path = os.path.relpath(file_path, directory_path)
            print(f"\n📄 Lendo arquivo: {relative_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as json_file:
                    # Usa o hook para verificar chaves duplicadas durante a leitura
                    data = json.load(json_file, object_pairs_hook=_check_for_duplicate_keys)

                    # Verificar se o arquivo contém uma lista ou um único objeto
                    if isinstance(data, list):
                        print(f"   ✅ {len(data)} registros lidos")
                        all_data.extend(data)
                    elif isinstance(data, dict):
                        print(f"   ✅ 1 registro lido")
                        all_data.append(data)
                    else:
                        print(f"   ⚠️ Formato não reconhecido (não é lista nem dicionário)")

            except ValueError as e:
                print(f"   ❌ Erro de validação no arquivo {relative_path}: {e}")
            except json.JSONDecodeError as e:
                print(f"   ❌ Erro ao decodificar JSON: {e}")
            except Exception as e:
                print(f"   ❌ Erro ao ler arquivo: {e}")

        print(f"\n📊 Total de registros consolidados: {len(all_data)}")
        return all_data

    except Exception as e:
        print(f"❌ Erro ao processar diretório: {e}")
        return None

def json_directory_to_csv(directory_path, csv_file_path):
    """
    Lê todos os arquivos JSON de um diretório e converte para um único arquivo CSV.
    Processa arquivo por arquivo (streaming) para evitar pico de memória RAM.

    :param directory_path: Caminho do diretório contendo os arquivos JSON
    :param csv_file_path: Caminho do arquivo CSV de saída
    :return: bool - True se sucesso, False se falha
    """
    print("\n" + "=" * 60)
    print("🔄 INICIANDO CONVERSÃO DE ARQUIVOS JSON PARA CSV")
    print("=" * 60)

    if not os.path.exists(directory_path):
        print(f"❌ Erro: Diretório não encontrado: {directory_path}")
        if os.path.exists(csv_file_path):
            mensagem = f"Diretório JSON '{directory_path}' não encontrado. Utilizando CSV já existente em '{csv_file_path}'."
            log_event(DIR_PATH_OUTPUT, mensagem)
            print(f"⚠️ {mensagem}")
            return True
        return False

    # Coleta e ordena arquivos JSON
    json_files = sorted(
        os.path.join(dirpath, filename)
        for dirpath, _, filenames in os.walk(directory_path)
        for filename in filenames
        if filename.endswith('.json')
    )

    if not json_files:
        print(f"⚠️ Nenhum arquivo JSON encontrado em: {directory_path}")
        if os.path.exists(csv_file_path):
            mensagem = f"Nenhum JSON encontrado em '{directory_path}'. Utilizando CSV já existente em '{csv_file_path}'."
            log_event(DIR_PATH_OUTPUT, mensagem)
            print(f"⚠️ {mensagem}")
            return True
        return False

    print(f"\n📂 Encontrados {len(json_files)} arquivos JSON.")

    ensure_dir_exists(os.path.dirname(csv_file_path))

    ordered_keys = []
    ordered_keys_set = set()
    original_keys_map = {}
    header_written = False
    total_records = 0
    total_written = 0

    try:
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_out:
            writer = csv.writer(csv_out, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)

            for file_path in json_files:
                relative_path = os.path.relpath(file_path, directory_path)
                print(f"\n📄 Lendo arquivo: {relative_path}")

                try:
                    with open(file_path, 'r', encoding='utf-8') as json_file:
                        data = json.load(json_file, object_pairs_hook=_check_for_duplicate_keys)

                    if isinstance(data, dict):
                        data = [data]
                    elif not isinstance(data, list):
                        print(f"   ⚠️ Formato não reconhecido (não é lista nem dicionário)")
                        continue

                    if not data:
                        print(f"   ⚠️ Arquivo vazio")
                        continue

                    print(f"   ✅ {len(data)} registros lidos")
                    total_records += len(data)

                    # Primeiro arquivo: extrai o cabeçalho e escreve
                    if not header_written:
                        ordered_keys = [normalize_header_key(k) for k in data[0].keys()]
                        ordered_keys_set = set(ordered_keys)
                        original_keys_map = {normalize_header_key(k): k for k in data[0].keys()}
                        writer.writerow(ordered_keys)
                        header_written = True

                    # Atualiza chaves para arquivos com schema diferente
                    for item in data:
                        for key in item.keys():
                            nk = normalize_header_key(key)
                            if nk not in ordered_keys_set:
                                ordered_keys.append(nk.upper())
                                ordered_keys_set.add(nk.upper())
                                original_keys_map[nk] = key.upper()

                    # Escreve linha a linha (sem acumular em memória)
                    ignorar_registro = False
                    for idx, item in enumerate(data, 1):
                        value = get_value_case_insensitive(item, 'tipoDocumento', original_keys_map)
                        if value.upper() not in _LISTA_TIPO_DOC_SET:
                            continue

                        row = []
                        for key in ordered_keys:
                            value = get_value_case_insensitive(item, key, original_keys_map)

                            if key == 'SEQDOCUMENTO' and not value:
                                source_file = item.get('_source_file', relative_path)
                                log_event(DIR_PATH_OUTPUT, f"Registro com SEQDOCUMENTO vazio no arquivo '{source_file}'. Registro: {item}")
                                ignorar_registro = True
                                break

                            try:
                                if key in _DATE_FIELDS:
                                    value = convert_timestamp_to_date(value)
                                elif key in _TEXT_CLEAN_FIELDS:
                                    value = removeCRLFString(value)
                                elif isinstance(value, (list, dict)):
                                    value = json.dumps(value, ensure_ascii=False)
                                elif value is None:
                                    value = ''
                                else:
                                    value = str(value)
                            except Exception as e:
                                log_event(DIR_PATH_OUTPUT, f'Erro ao tratar campo "{key}" com valor "{value}": {e}')
                                ignorar_registro = True
                                break

                            row.append(value)

                        if not ignorar_registro:
                            writer.writerow(row)
                            total_written += 1
                        else:
                            ignorar_registro = False

                        if idx % 1000 == 0:
                            print(f"  Processados {idx} registros deste arquivo...")

                except ValueError as e:
                    print(f"   ❌ Erro de validação no arquivo {relative_path}: {e}")
                except json.JSONDecodeError as e:
                    print(f"   ❌ Erro ao decodificar JSON: {e}")
                except Exception as e:
                    print(f"   ❌ Erro ao ler arquivo: {e}")

        if not header_written:
            print("⚠️ Nenhum dado para converter")
            if os.path.exists(csv_file_path):
                mensagem = f"Nenhum dado JSON processado em '{directory_path}'. Utilizando CSV já existente em '{csv_file_path}'."
                log_event(DIR_PATH_OUTPUT, mensagem)
                print(f"⚠️ {mensagem}")
                return True
            return False

        print(f"\n📊 Total de registros lidos: {total_records}")
        print(f"✅ CSV criado com sucesso: {csv_file_path}")
        print(f"   Registros gravados: {total_written}")
        print(f"   Campos: {len(ordered_keys)}")
        print("\n" + "=" * 60)
        print("✅ CONVERSÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        return True

    except PermissionError:
        print(f"❌ Erro: Sem permissão para escrever em {csv_file_path}")
        return False
    except IOError as e:
        print(f"❌ Erro de I/O ao escrever arquivo CSV: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado na conversão para CSV: {e}")
        if os.path.exists(csv_file_path):
            mensagem = f"Erro na conversão JSON→CSV: {e}. Utilizando CSV já existente em '{csv_file_path}'."
            log_event(DIR_PATH_OUTPUT, mensagem)
            print(f"⚠️ {mensagem}")
            return True
        return False

def add_decision_column(csv_file_path):
    try:
        # Read existing CSV
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=';', quotechar='"')
            rows = list(reader)

        # Add new column header
        rows[0].append('decicao_acordao')

        # Add empty values for new column
        for i in range(1, len(rows)):
            rows[i].append('')

        # Write back to CSV
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
            writer.writerows(rows)
        return True
    except Exception as e:
        print(f"Error adding decision column: {e}")
        return False


def extract_zip_files():
    '''
    Extrai todos os arquivos zip do diretório ZIP_DIR_PATH para DIR_PATH
    :return: bool
    '''
    try:
        if not os.path.exists(ZIP_DIR_PATH):
            mensagem = f"Diretório de ZIP não encontrado: {ZIP_DIR_PATH}"
            log_event(DIR_PATH_OUTPUT, mensagem)
            if _directory_contains_matching_files(UNZIP_DIR_PATH, lambda nome: nome.endswith('.txt')):
                aviso = f"{mensagem} Utilizando arquivos TXT já extraídos em '{UNZIP_DIR_PATH}'."
                log_event(DIR_PATH_OUTPUT, aviso)
                print(f"⚠️ {aviso}")
                return True
            print(f"Error extracting zip files: {mensagem}")
            return False

        ensure_dir_exists(UNZIP_DIR_PATH)

        total_zip = 0
        extracted_count = 0
        invalid_count = 0
        failed_count = 0

        for filename in sorted(os.listdir(ZIP_DIR_PATH)):
            if not filename.endswith('.zip'):
                continue

            total_zip += 1
            zip_path = os.path.join(ZIP_DIR_PATH, filename)
            extract_path = os.path.join(UNZIP_DIR_PATH)

            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                extracted_count += 1
                print(f"Extracted {filename}")
            except zipfile.BadZipFile as e:
                invalid_count += 1
                mensagem = f"Arquivo ZIP inválido ignorado: '{zip_path}'. Detalhe: {e}"
                log_event(DIR_PATH_OUTPUT, mensagem)
                print(f"⚠️ {mensagem}")
            except Exception as e:
                failed_count += 1
                mensagem = f"Erro ao extrair arquivo '{zip_path}'. Detalhe: {e}"
                log_event(DIR_PATH_OUTPUT, mensagem)
                print(f"⚠️ {mensagem}")

        if total_zip == 0:
            mensagem = f"Nenhum arquivo ZIP encontrado em: {ZIP_DIR_PATH}"
            log_event(DIR_PATH_OUTPUT, mensagem)
            if _directory_contains_matching_files(UNZIP_DIR_PATH, lambda nome: nome.endswith('.txt')):
                aviso = f"{mensagem} Utilizando arquivos TXT já extraídos em '{UNZIP_DIR_PATH}'."
                log_event(DIR_PATH_OUTPUT, aviso)
                print(f"⚠️ {aviso}")
                return True
            print(f"⚠️ {mensagem}")
            return False

        print("\n📦 Resumo da extração de ZIPs:")
        print(f"   Total encontrados: {total_zip}")
        print(f"   Extraídos com sucesso: {extracted_count}")
        print(f"   Inválidos ignorados: {invalid_count}")
        print(f"   Falhas de extração: {failed_count}")

        if extracted_count > 0:
            return True

        if _directory_contains_matching_files(UNZIP_DIR_PATH, lambda nome: nome.endswith('.txt')):
            aviso = f"Nenhum ZIP novo foi extraído com sucesso. Utilizando arquivos TXT já existentes em '{UNZIP_DIR_PATH}'."
            log_event(DIR_PATH_OUTPUT, aviso)
            print(f"⚠️ {aviso}")
            return True

        return False
    except Exception as e:
        mensagem = f"Erro geral ao extrair arquivos ZIP: {e}"
        log_event(DIR_PATH_OUTPUT, mensagem)
        print(f"Error extracting zip files: {e}")
        return False


def download_zip_files():
    '''
    Faz o download dos arquivos zip de um MÊS e ANO específicos do site web do STJ.
    Verifica se o arquivo já existe antes de fazer o download.
    Se o arquivo já existir, o download será ignorado.
    :return: bool
    '''
    url = "https://dadosabertos.web.stj.jus.br/dataset/integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica"

    if MONTH_DOWNLOAD is not None:
        # Filtra por um mês e ano específicos
        year_month_prefix = f"{YEAR_DOWNLOAD}{str(MONTH_DOWNLOAD).zfill(2)}"
        print(f"\n🔎 Procurando arquivos zip para o período: {str(MONTH_DOWNLOAD).zfill(2)}/{YEAR_DOWNLOAD} (prefixo: {year_month_prefix})")
    else:
        # Filtra por todos os meses de um ano específico
        year_month_prefix = str(YEAR_DOWNLOAD)
        print(f"\n🔎 Procurando arquivos zip para todos os meses de {YEAR_DOWNLOAD} (prefixo: {year_month_prefix})")

    date_pattern = re.compile(r'(\d{8})')
    downloaded_count = 0
    skipped_count = 0
    invalid_count = 0
    failed_count = 0
    found_files = []

    session = Session()

    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()

        # Find all zip file links
        zip_links = re.findall(r'href="([^"]+\.zip)"', response.text)

        ensure_dir_exists(ZIP_DIR_PATH)

        for link in zip_links:
            filename = os.path.basename(link)
            date_match = date_pattern.search(filename)

            if date_match and date_match.group(1).startswith(year_month_prefix):
                found_files.append(filename)
                file_path = os.path.join(ZIP_DIR_PATH, filename)
                if not os.path.exists(file_path):
                    try:
                        print(f"Downloading {filename}...")
                        file_response = session.get(link, timeout=60)
                        file_response.raise_for_status()

                        with open(file_path, 'wb') as f:
                            f.write(file_response.content)

                        if zipfile.is_zipfile(file_path):
                            downloaded_count += 1
                            print(f"Downloaded {filename}")
                        else:
                            invalid_count += 1
                            mensagem = f"Download ignorado por arquivo inválido/não ZIP: '{file_path}'."
                            log_event(DIR_PATH_OUTPUT, mensagem)
                            print(f"⚠️ {mensagem}")
                            _safe_remove_file(file_path)
                    except Exception as e:
                        failed_count += 1
                        mensagem = f"Falha ao baixar ZIP '{filename}'. Detalhe: {e}"
                        log_event(DIR_PATH_OUTPUT, mensagem)
                        print(f"⚠️ {mensagem}")
                        _safe_remove_file(file_path)
                else:
                    skipped_count += 1
                    print(f"File {filename} already exists")

        print("\n📦 Resumo do download de ZIPs:")
        print(f"   Encontrados no portal: {len(found_files)}")
        print(f"   Baixados com sucesso: {downloaded_count}")
        print(f"   Já existentes (pulados): {skipped_count}")
        print(f"   Inválidos descartados: {invalid_count}")
        print(f"   Falhas de download: {failed_count}")

        if downloaded_count == 0 and skipped_count == 0 and _directory_contains_matching_files(
            ZIP_DIR_PATH,
            lambda nome: nome.endswith('.zip') and nome.startswith(year_month_prefix)
        ):
            aviso = f"Nenhum ZIP foi baixado nesta rodada, mas há arquivos locais compatíveis em '{ZIP_DIR_PATH}'."
            log_event(DIR_PATH_OUTPUT, aviso)
            print(f"⚠️ {aviso}")
            return True

        return downloaded_count > 0 or skipped_count > 0

    except Exception as e:
        mensagem = f"Erro geral ao baixar arquivos ZIP: {e}"
        log_event(DIR_PATH_OUTPUT, mensagem)
        if _directory_contains_matching_files(
            ZIP_DIR_PATH,
            lambda nome: nome.endswith('.zip') and nome.startswith(year_month_prefix)
        ):
            aviso = f"{mensagem} Utilizando arquivos ZIP já existentes em '{ZIP_DIR_PATH}'."
            log_event(DIR_PATH_OUTPUT, aviso)
            print(f"⚠️ {aviso}")
            return True
        print(f"Error downloading zip files: {e}")
        return False
    finally:
        session.close()


def download_json_metadados():
    '''
    Faz o download APENAS dos arquivos JSON de metadados do ano especificado do site web do STJ.

    Regras aplicadas:
    1) Obtém somente arquivos no formato metadadosYYYYMMDD.json
    2) Restringe apenas aos arquivos de YYYY (metadadosYYYYMMDD.json)
    3) Salva os arquivos no diretório: C:\\_PUCPR\\PrjDadosAbertos\\arquivos

    :return: bool - True se o download foi bem-sucedido, False caso contrário
    '''
    url = "https://dadosabertos.web.stj.jus.br/dataset/integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica"
    download_dir = DIR_PATH_DOWNLOAD_DADOS_METADADOS
    ensure_dir_exists(download_dir)

    # Constrói o padrão de regex para o mês dinamicamente
    if MONTH_DOWNLOAD is not None:
        # Filtra por um mês específico
        month_str = str(MONTH_DOWNLOAD).zfill(2)
        month_pattern = month_str
        print(f"\n🔎 Filtrando downloads de metadados para o mês: {month_str}/{YEAR_DOWNLOAD}")
    else:
        # Filtra por todos os meses do ano
        month_pattern = "(0[1-9]|1[0-2])"
        print(f"\n🔎 Filtrando downloads de metadados para todos os meses de {YEAR_DOWNLOAD}")

    json_pattern = re.compile(rf'^{JSON_FILE_DOWNLOAD}{month_pattern}(0[1-9]|[12]\d|3[01])\.json$')

    session = Session()

    try:
        print("Conectando ao site do STJ para buscar arquivos JSON...")
        # Fazer requisição para obter a página HTML
        response = session.get(url, timeout=30)
        response.raise_for_status()

        # Buscar TODOS os links na página
        # Procurar por padrões de links que possam conter arquivos JSON
        all_links = re.findall(r'href="([^"]+)"', response.text)

        # Filtrar apenas links que terminam com .json
        json_links = [link for link in all_links if link.endswith('.json')]

        # Garantir que o diretório de destino existe
        ensure_dir_exists(download_dir)

        downloaded_count = 0
        skipped_count = 0
        found_files = []

        print(f"\nBuscando arquivos JSON de metadados {YEAR_DOWNLOAD}...")
        print(f"Total de links JSON encontrados na página: {len(json_links)}")

        for link in json_links:
            # Extrair apenas o nome do arquivo
            filename = os.path.basename(link)

            # Verificar se o arquivo corresponde ao padrão metadadosYYYYMMDD.json
            if json_pattern.match(filename):
                found_files.append(filename)
                file_path = os.path.join(download_dir, filename)

                # Verificar se o arquivo já existe localmente
                if not os.path.exists(file_path):
                    print(f"\n📥 Baixando: {filename}")

                    # Construir URL completa se o link for relativo
                    if not link.startswith('http'):
                        if link.startswith('/'):
                            full_url = f"https://dadosabertos.web.stj.jus.br{link}"
                        else:
                            # Tentar com o caminho do dataset
                            full_url = f"https://dadosabertos.web.stj.jus.br/dataset/integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica/{link}"
                    else:
                        full_url = link

                    try:
                        # Fazer download do arquivo JSON
                        file_response = session.get(full_url, timeout=60)
                        file_response.raise_for_status()

                        # Salvar o arquivo JSON
                        with open(file_path, 'wb') as f:
                            f.write(file_response.content)

                        # Verificar se é um arquivo JSON válido

                        with open(file_path, 'r', encoding='utf-8', ) as f:
                            json.load(f)  # Tenta carregar para validar

                        print(f"   ✅ Salvo em: {file_path}")
                        downloaded_count += 1

                    except json.JSONDecodeError as e:
                        mensagem = f"Arquivo JSON inválido ignorado: '{file_path}'. Detalhe: {e}"
                        log_event(DIR_PATH_OUTPUT, mensagem)
                        print(f"   ⚠️ {mensagem}")
                        _safe_remove_file(file_path)
                        continue
                    except Exception as e:
                        mensagem = f"Erro ao baixar/processar JSON '{filename}'. Detalhe: {e}"
                        log_event(DIR_PATH_OUTPUT, mensagem)
                        print(f"   ⚠️ {mensagem}")
                        _safe_remove_file(file_path)
                        continue
                else:
                    print(f"⏭️  {filename} já existe, pulando download")
                    skipped_count += 1

        # Relatório final detalhado
        print("\n" + "=" * 60)
        print(f"📊 RELATÓRIO FINAL - Download de Metadados JSON {YEAR_DOWNLOAD}")
        print("=" * 60)
        print(f"✅ Arquivos baixados com sucesso: {downloaded_count}")
        print(f"⏭️  Arquivos já existentes (pulados): {skipped_count}")
        print(f"⚠️  Arquivos com falha/ignorados: {len(found_files) - downloaded_count - skipped_count}")
        print(f"📁 Total de arquivos metadados {YEAR_DOWNLOAD} encontrados: {len(found_files)}")
        print(f"📂 Diretório de destino: {download_dir}")

        if found_files:
            print(f"\n📋 Arquivos de metadados {YEAR_DOWNLOAD} encontrados:")
            for f in sorted(found_files):
                status = "✅ Baixado" if os.path.exists(os.path.join(download_dir, f)) else "❌ Não baixado"
                print(f"   • {f} [{status}]")
        else:
            print(f"\n⚠️ ATENÇÃO: Nenhum arquivo metadados{YEAR_DOWNLOAD}MMDD.json foi encontrado na página!")
            print("   Possíveis causas:")
            print(f"   - Os arquivos ainda não foram disponibilizados para {YEAR_DOWNLOAD}")
            print("   - A URL ou estrutura do site pode ter mudado")

        print("=" * 60)

        if downloaded_count == 0 and skipped_count == 0 and _directory_contains_matching_files(
            download_dir,
            lambda nome: json_pattern.match(nome) is not None
        ):
            aviso = f"Nenhum JSON novo foi aproveitado nesta rodada, mas há arquivos locais compatíveis em '{download_dir}'."
            log_event(DIR_PATH_OUTPUT, aviso)
            print(f"⚠️ {aviso}")
            return True

        return downloaded_count > 0 or skipped_count > 0

    except requests.RequestException as e:
        mensagem = f"Erro ao fazer requisição HTTP para JSONs: {e}"
        log_event(DIR_PATH_OUTPUT, mensagem)
        if _directory_contains_matching_files(download_dir, lambda nome: json_pattern.match(nome) is not None):
            aviso = f"{mensagem} Utilizando arquivos JSON já existentes em '{download_dir}'."
            log_event(DIR_PATH_OUTPUT, aviso)
            print(f"⚠️ {aviso}")
            return True
        print(f"❌ Erro ao fazer requisição HTTP: {e}")
        return False
    except Exception as e:
        mensagem = f"Erro inesperado ao baixar arquivos JSON: {e}"
        log_event(DIR_PATH_OUTPUT, mensagem)
        if _directory_contains_matching_files(download_dir, lambda nome: json_pattern.match(nome) is not None):
            aviso = f"{mensagem} Utilizando arquivos JSON já existentes em '{download_dir}'."
            log_event(DIR_PATH_OUTPUT, aviso)
            print(f"⚠️ {aviso}")
            return True
        print(f"❌ Erro inesperado ao baixar arquivos JSON: {e}")
        return False
    finally:
        session.close()

def read_txt_files_and_create_csv(metadata_csv_path, search_dir, output_csv_path, log_dir):
    """
    Cria um CSV com detalhes de acórdãos/decisões, usando um CSV de metadados como guia.
    """
    print("\n🔄 Iniciando processamento de TXTs guiado por metadados...")

    # Etapa 1: Percorrer o arquivo de metadados CSV e obter os seqDocumento
    print(f"   1. Lendo arquivo de metadados CSV: {metadata_csv_path}")
    if not os.path.exists(metadata_csv_path):
        if os.path.exists(output_csv_path):
            mensagem = f"Arquivo de metadados não encontrado em '{metadata_csv_path}'. Utilizando CSV final já existente em '{output_csv_path}'."
            log_event(log_dir, mensagem)
            print(f"⚠️ {mensagem}")
            return True
        print(f"❌ Erro: Arquivo de metadados não encontrado.")
        return False

    sequences_to_process = []
    try:
        with open(metadata_csv_path, 'r', encoding='utf-8') as meta_file:
            # Usa DictReader para tratar cada linha como um dicionário
            reader = csv.DictReader(meta_file, delimiter=';')

            for row in reader:
                # Verifica se a linha tem a chave 'TIPODOCUMENTO' (normalizada) e se o valor é ACORDAO
                if 'TIPODOCUMENTO' in row and row['TIPODOCUMENTO'].upper() in _LISTA_TIPO_DOC_SET:
                    seq = row.get('SEQDOCUMENTO')
                    if seq:
                        sequences_to_process.append(seq)

        print(f"   -> Encontrados {len(sequences_to_process)} documentos do tipo '{LISTA_TIPO_DOCUMENTO[0]}'.")

        txt_index = build_file_index_recursively(search_dir, '.txt')
        print(f"   -> Índice local de TXT construído com {len(txt_index)} arquivos.")

        # Etapa 2, 3 e 4: Buscar, processar e escrever os dados, e registrar falhas.
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as out_file:
            writer = csv.writer(out_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL, lineterminator='\n')
            writer.writerow(['SEQDOCUMENTO', 'ACORDAO', 'EMENTA', 'RELATORIO', 'VOTO', 'DECISAO'])

            processed_count = 0
            not_found_count = 0
            ignored_count = 0
            error_count = 0
            total_to_process = len(sequences_to_process)

            for idx, seq_documento in enumerate(sequences_to_process, 1):
                filename_to_find = f"{seq_documento}.txt"
                print(f"   Processando {idx}/{total_to_process}: Buscando {filename_to_find}...")

                try:
                    txt_filepath = txt_index.get(filename_to_find)

                    if txt_filepath:
                        with open(txt_filepath, 'r', encoding='utf-8') as txt_file:
                            content = txt_file.read()
                            processed_data = _process_txt_content(content)
                            if processed_data:
                                acordao, ementa, relatorio, voto, decisao = processed_data
                                writer.writerow([seq_documento, acordao, ementa, relatorio, voto, decisao])
                                processed_count += 1
                            else:
                                ignored_count += 1
                                log_event(log_dir, f"Arquivo {filename_to_find} localizado, mas sem estrutura reconhecida para extração.")
                    else:
                        not_found_count += 1
                        log_message = f"Arquivo {filename_to_find} não localizado no diretório {search_dir}"
                        log_event(log_dir, log_message)
                except Exception as e:
                    error_count += 1
                    log_event(log_dir, f"Erro ao processar arquivo {filename_to_find}. Detalhe: {e}")
                    print(f"   ⚠️ Erro ao processar {filename_to_find}: {e}")

        print("\n✅ Processamento guiado por metadados concluído.")
        print(f"   {processed_count} arquivos TXT processados com sucesso.")
        print(f"   {not_found_count} arquivos TXT não encontrados (verifique o log em {log_dir}).")
        print(f"   {ignored_count} arquivos TXT ignorados por estrutura não reconhecida.")
        print(f"   {error_count} arquivos TXT com erro durante o processamento.")

        if processed_count == 0 and os.path.exists(output_csv_path):
            mensagem = f"Nenhum TXT foi processado com sucesso nesta execução. Mantendo CSV final existente em '{output_csv_path}'."
            log_event(log_dir, mensagem)
            print(f"⚠️ {mensagem}")

        return True

    except Exception as e:
        if os.path.exists(output_csv_path):
            mensagem = f"Erro inesperado ao processar o arquivo de metadados: {e}. Utilizando CSV final já existente em '{output_csv_path}'."
            log_event(log_dir, mensagem)
            print(f"⚠️ {mensagem}")
            return True
        print(f"❌ Erro inesperado ao processar o arquivo de metadados: {e}")
        return False

def _process_txt_content(content):
    """
    Extrai seções de um conteúdo de texto com regras complexas e priorizadas.
    1. Verifica se o texto inicia com 'DECISÃO'. Se sim, preenche RELATÓRIO com o trecho
       entre 'DECISÃO' e 'o relatório.' e mantém o restante em DECISÃO.
    2. Se não, processa como um 'ACÓRDÃO', buscando as demais seções (EMENTA, RELATÓRIO, VOTO).
    """
    # REGRA 2: Verifica se o documento é uma DECISÃO no início.
    decisao_start_pattern = re.compile(r'^\s*(?:</?br>|\s)*DECIS(?:ÃO|AO)\s*(?:</?br>|\s)*', re.IGNORECASE)
    match_decisao = decisao_start_pattern.search(content)
    if match_decisao:
        start_of_content = match_decisao.end()
        decisao_text = content[start_of_content:].strip()

        relatorio_end_pattern = re.compile(r'(?:É\s+|E\s+)?O\s+RELAT(?:ÓRIO|ORIO)\.', re.IGNORECASE)
        match_relatorio_end = relatorio_end_pattern.search(decisao_text)

        if match_relatorio_end:
            relatorio_text = removeCRLFString(decisao_text[:match_relatorio_end.start()]).strip()
            decisao_text = removeCRLFString(decisao_text[match_relatorio_end.end():]).strip()
            return ('', '', relatorio_text, '', decisao_text)

        # Fallback para preservar o conteúdo quando o marcador final do relatório não é encontrado.
        return ('', '', '', '', removeCRLFString(decisao_text))

    # Se não for DECISÃO, processa como ACÓRDÃO (REGRA 1)
    m_tags = ['RELATÓRIO', 'EMENTA', 'VOTO']
    start_tag = 'ACÓRDÃO'

    pattern_start = r'^\s*(?:</?br>|\s)*(' + start_tag + r')'
    pattern_mandatory_prefix = r'(?:<br/?>|\n)\s*(' + '|'.join(m_tags) + r')'

    tag_pattern = re.compile(
        r'(?:</?br>|\s)*' + f'(?:{pattern_start}|{pattern_mandatory_prefix})' + r'\s*(?:</?br>|\s)*')

    found_tags = []
    for match in tag_pattern.finditer(content):
        tag_name = next((g for g in match.groups() if g is not None), None)
        if tag_name:
            found_tags.append({'tag': tag_name, 'start': match.start(), 'end': match.end()})

    if not found_tags:
        return None

    found_tags.sort(key=lambda x: x['start'])

    extracted_data = {}
    for i, current_tag_info in enumerate(found_tags):
        start_of_content = current_tag_info['end']
        end_of_content = found_tags[i + 1]['start'] if i + 1 < len(found_tags) else len(content)
        text_slice = content[start_of_content:end_of_content]
        extracted_data[current_tag_info['tag']] = removeCRLFString(text_slice)

    # Como já tratamos DECISÃO, aqui só precisamos montar o resultado para ACÓRDÃO.
    acordao_text = extracted_data.get('ACÓRDÃO', '')

    return (acordao_text, extracted_data.get('EMENTA', ''),
            extracted_data.get('RELATÓRIO', ''), extracted_data.get('VOTO', ''),
            '')  # O campo decisão sempre será vazio neste fluxo.