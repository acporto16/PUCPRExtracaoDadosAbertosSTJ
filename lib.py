import json
import csv
import requests
import zipfile
from const import *
from utils import *


def read_json_file(file_path):
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
        if data:
            # Preservar ordem das chaves do primeiro registro
            # Normaliza as chaves do primeiro registro
            ordered_keys = [normalize_header_key(key) for key in data[0].keys()]
            original_keys_map = {normalize_header_key(key): key for key in data[0].keys()}

            # Adicionar chaves que aparecem em outros registros
            for item in data[1:]:
                for key in item.keys():
                    normalized_key = normalize_header_key(key)
                    if normalized_key not in ordered_keys:
                        ordered_keys.append(normalized_key.upper())
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
                for key in ordered_keys:
                    value = get_value_case_insensitive(item, key, original_keys_map)

                    #considerar apenas o tipo de documento especificado na constante TIPO_DOCUMENTO
                    if not (key == 'TIPODOCUMENTO' and (value in LISTA_TIPO_DOCUMENTO)) :
                        ignorar_registro = True
                        break

                    if key == 'SEQDOCUMENTO' and not value:
                        source_file = item.get('_source_file', 'desconhecido')
                        log_event(DIR_PATH_OUTPUT, f"Registro com SEQDOCUMENTO vazio encontrado no arquivo '{source_file}'. Registro: {item}")
                        ignorar_registro = True
                        break  # sai do loop e registra controle para não gravar registro
                    try:
                        # Tratamento especial para campos de data
                        if key in ['DATAPUBLICACAO', 'DATADISTRIBUICAO', 'DATAJULGAMENTO', 'DATARECEBIMENTO']:
                            value = convert_timestamp_to_date(value)
                        if key in ['RECURSO', 'TEOR', 'DESCRICAOMONOCRATICA']:
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
            if normalize_header_key(item_key) in LIST_FIELDS:
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

            def check_for_duplicate_keys(ordered_pairs):
                """Hook para o json.load que verifica chaves duplicadas."""
                d = {}
                for key, value in ordered_pairs:
                    if key in d:
                        raise ValueError(f"Chave duplicada encontrada: '{key}'")
                    d[key] = value
                return d

            try:
                with open(file_path, 'r', encoding='utf-8') as json_file:
                    # Usa o hook para verificar chaves duplicadas durante a leitura
                    data = json.load(json_file, object_pairs_hook=check_for_duplicate_keys)

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

    :param directory_path: Caminho do diretório contendo os arquivos JSON
    :param csv_file_path: Caminho do arquivo CSV de saída
    :return: bool - True se sucesso, False se falha
    """
    print("\n" + "=" * 60)
    print("🔄 INICIANDO CONVERSÃO DE ARQUIVOS JSON PARA CSV")
    print("=" * 60)

    # Ler todos os arquivos JSON do diretório
    all_data = read_all_json_files_from_directory(directory_path)

    if all_data is None:
        print("❌ Falha ao ler arquivos JSON")
        return False

    if not all_data:
        print("⚠️ Nenhum dado para converter")
        return False

    # Converter para CSV
    success = json_to_csv(all_data, csv_file_path)

    if success:
        print("\n" + "=" * 60)
        print("✅ CONVERSÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
    else:
        print("\n❌ Falha na conversão para CSV")

    return success

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
        for filename in os.listdir(ZIP_DIR_PATH):
            if filename.endswith('.zip'):
                zip_path = os.path.join(ZIP_DIR_PATH, filename)
                extract_path = os.path.join(UNZIP_DIR_PATH)

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                print(f"Extracted {filename}")
        return True
    except Exception as e:
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

    try:
        response = requests.get(url)
        response.raise_for_status()

        # Find all zip file links
        zip_links = re.findall(r'href="([^"]+\.zip)"', response.text)

        ensure_dir_exists(ZIP_DIR_PATH)

        for link in zip_links:
            filename = os.path.basename(link)
            date_match = date_pattern.search(filename)

            if date_match and date_match.group(1).startswith(year_month_prefix):
                file_path = os.path.join(ZIP_DIR_PATH, filename)
                if not os.path.exists(file_path):
                    print(f"Downloading {filename}...")
                    file_response = requests.get(link)
                    file_response.raise_for_status()

                    with open(file_path, 'wb') as f:
                        f.write(file_response.content)
                    print(f"Downloaded {filename}")
                else:
                    print(f"File {filename} already exists")
        return True

    except Exception as e:
        print(f"Error downloading zip files: {e}")
        return False


def download_json_metadados():
    '''
    Faz o download APENAS dos arquivos JSON de metadados do ano especificado do site web do STJ.

    Regras aplicadas:
    1) Obtém somente arquivos no formato metadadosYYYYMMDD.json
    2) Restringe apenas aos arquivos de YYYY (metadadosYYYYMMDD.json)
    3) Salva os arquivos no diretório: C:\_PUCPR\PrjDadosAbertos\arquivos

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

    json_pattern = re.compile(f'^{JSON_FILE_DOWNLOAD}{month_pattern}(0[1-9]|[12]\d|3[01])\.json$')

    try:
        print("Conectando ao site do STJ para buscar arquivos JSON...")
        # Fazer requisição para obter a página HTML
        response = requests.get(url, timeout=30)
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
                        file_response = requests.get(full_url, timeout=60)
                        file_response.raise_for_status()

                        # Salvar o arquivo JSON
                        with open(file_path, 'wb') as f:
                            f.write(file_response.content)

                        # Verificar se é um arquivo JSON válido

                        with open(file_path, 'r', encoding='utf-8', ) as f:
                            json.load(f)  # Tenta carregar para validar

                        print(f"   ✅ Salvo em: {file_path}")
                        downloaded_count += 1

                    except json.JSONDecodeError:
                        print(f"   ❌ Arquivo baixado não é um JSON válido, removendo...")
                        os.remove(file_path)
                        return False
                    except Exception as e:
                        print(f"   ❌ Erro ao baixar: {e}")
                        return False
                else:
                    print(f"⏭️  {filename} já existe, pulando download")
                    skipped_count += 1

        # Relatório final detalhado
        print("\n" + "=" * 60)
        print(f"📊 RELATÓRIO FINAL - Download de Metadados JSON {YEAR_DOWNLOAD}")
        print("=" * 60)
        print(f"✅ Arquivos baixados com sucesso: {downloaded_count}")
        print(f"⏭️  Arquivos já existentes (pulados): {skipped_count}")
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

        return downloaded_count > 0 or skipped_count > 0

    except requests.RequestException as e:
        print(f"❌ Erro ao fazer requisição HTTP: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado ao baixar arquivos JSON: {e}")
        return False

def read_txt_files_and_create_csv(metadata_csv_path, search_dir, output_csv_path, log_dir):
    """
    Cria um CSV com detalhes de acórdãos/decisões, usando um CSV de metadados como guia.
    """
    print("\n🔄 Iniciando processamento de TXTs guiado por metadados...")

    # Etapa 1: Percorrer o arquivo de metadados CSV e obter os seqDocumento
    print(f"   1. Lendo arquivo de metadados CSV: {metadata_csv_path}")
    if not os.path.exists(metadata_csv_path):
        print(f"❌ Erro: Arquivo de metadados não encontrado.")
        return False

    sequences_to_process = []
    try:
        with open(metadata_csv_path, 'r', encoding='utf-8') as meta_file:
            # Usa DictReader para tratar cada linha como um dicionário
            reader = csv.DictReader(meta_file, delimiter=';')

            for row in reader:
                # Verifica se a linha tem a chave 'TIPODOCUMENTO' (normalizada) e se o valor é ACORDAO
                if 'TIPODOCUMENTO' in row and row['TIPODOCUMENTO'].upper() in LISTA_TIPO_DOCUMENTO:
                    seq = row.get('SEQDOCUMENTO')
                    if seq:
                        sequences_to_process.append(seq)

        print(f"   -> Encontrados {len(sequences_to_process)} documentos do tipo '{LISTA_TIPO_DOCUMENTO[0]}'.")

        # Etapa 2, 3 e 4: Buscar, processar e escrever os dados, e registrar falhas.
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as out_file:
            writer = csv.writer(out_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL, lineterminator='\n')
            writer.writerow(['SEQDOCUMENTO', 'ACORDAO', 'EMENTA', 'RELATORIO', 'VOTO', 'DECISAO'])

            processed_count = 0
            not_found_count = 0
            total_to_process = len(sequences_to_process)

            for idx, seq_documento in enumerate(sequences_to_process, 1):
                filename_to_find = f"{seq_documento}.txt"
                print(f"   Processando {idx}/{total_to_process}: Buscando {filename_to_find}...")

                txt_filepath = find_file_recursively(search_dir, filename_to_find)

                if txt_filepath:
                    with open(txt_filepath, 'r', encoding='utf-8') as txt_file:
                        content = txt_file.read()
                        processed_data = _process_txt_content(content)
                        if processed_data:
                            acordao, ementa, relatorio, voto, decisao = processed_data
                            writer.writerow([seq_documento, acordao, ementa, relatorio, voto, decisao])
                            processed_count += 1
                else:
                    not_found_count += 1
                    log_message = f"Arquivo {filename_to_find} não localizado no diretório {search_dir}"
                    log_event(log_dir, log_message)

        print("\n✅ Processamento guiado por metadados concluído.")
        print(f"   {processed_count} arquivos TXT processados com sucesso.")
        print(f"   {not_found_count} arquivos TXT não encontrados (verifique o log em {log_dir}).")
        return True

    except Exception as e:
        print(f"❌ Erro inesperado ao processar o arquivo de metadados: {e}")
        return False

def _process_txt_content(content):
    """
    Extrai seções de um conteúdo de texto com regras complexas e priorizadas.
    1. Verifica se o texto inicia com 'DECISÃO'. Se sim, captura todo o conteúdo.
    2. Se não, processa como um 'ACÓRDÃO', buscando as demais seções (EMENTA, RELATÓRIO, VOTO).
    """
    # REGRA 2: Verifica se o documento é uma DECISÃO no início.
    decisao_start_pattern = re.compile(r'^\s*(?:</?br>|\s)*DECISÃO', re.IGNORECASE)
    match_decisao = decisao_start_pattern.search(content)
    if match_decisao:
        # Se for uma DECISÃO, o conteúdo é tudo após a tag.
        start_of_content = match_decisao.end()
        decisao_text = content[start_of_content:].strip()
        # Retorna apenas o campo decisão preenchido.
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