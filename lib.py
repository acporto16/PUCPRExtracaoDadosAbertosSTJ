import json
import csv
import requests
import zipfile
from const import *
from utils import *


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
                        ordered_keys.append(normalized_key)
                        original_keys_map[normalized_key] = key

        print(f"Convertendo {len(data)} registros com {len(ordered_keys)} campos para CSV...")

        # Garante que o diretório de saída exista antes de escrever o arquivo
        output_dir = os.path.dirname(csv_file_path)
        ensure_dir_exists(output_dir)

        # Escrever arquivo CSV
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)

            # Escrever cabeçalho
            writer.writerow(ordered_keys)

            # Escrever linhas de dados
            for idx, item in enumerate(data, 1):
                row = []
                for key in ordered_keys:
                    original_key = original_keys_map.get(key, key)
                    value = item.get(original_key, '')

                    if key in ['seqDocumento'] and not value:
                        raise Exception(f"SeqDocumento não foi mapeado corretamente.")

                    # Tratamento especial para campos de data
                    if key in ['dataPublicacao', 'dataDistribuicao', 'dataJulgamento']:
                        value = convert_timestamp_to_date(value)
                    if key in ['recurso', 'teor', 'descricaoMonocratica']:
                        value = removeCRLFString(value)
                    # Tratamento para listas e dicionários
                    elif isinstance(value, (list, dict)):
                        value = json.dumps(value, ensure_ascii=False)
                    # Tratamento para None
                    elif value is None:
                        value = ''
                    else:
                        value = str(value)

                    row.append(value)

                writer.writerow(row)

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
    Faz o download dos arquivos zip do site web do STJ.
    Verifica se o arquivo já existe antes de fazer o download.
    Se o arquivo já existir, o download será ignorado.
    :return: bool
    '''
    url = "https://dadosabertos.web.stj.jus.br/dataset/integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica"

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
            year = int(YEAR_DOWNLOAD)

            if date_match and date_match.group(1).startswith(str(year)):
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

    # Padrão específico para identificar APENAS arquivos metadadosYYYYMMDD.json
    # MMDD = mês (01-12) e dia (01-31)
    # json_pattern = re.compile(f'^{JSON_FILE_DOWNLOAD}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\.json$') #Geral:: todos os meses do ano

    json_pattern = re.compile(
        f'^{JSON_FILE_DOWNLOAD}(01|02)(0[1-9]|[12]\d|3[01])\.json$')  # limitado pelos 2 primeiros meses do ano

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


def _process_txt_content(content):
    """Função auxiliar para extrair seções de um conteúdo de texto."""
    if YEAR_DOWNLOAD != '2025':
        acordao = re.search(r'ACÓRDÃO<br>(.*?)<br>EMENTA<br>', content, re.DOTALL)
    else:
        acordao = acordao = re.search('ACÓRDÃO\s*(?:</?br>\s*)*([\s\S]*?)\s*(?:</?br>\s*)*RELATÓRIO', content, re.DOTALL)

    if not acordao:
        return None

    if YEAR_DOWNLOAD != '2025':
        ementa = re.search(r'<br>EMENTA<br>(.*?)RELATÓRIO<br>', content, re.DOTALL)
        relatorio = re.search(r'RELATÓRIO<br>(.*?)<br>VOTO<br>', content, re.DOTALL)
        voto = re.search(r'<br>VOTO<br>(.*)', content, re.DOTALL)
        decisao = re.search(r'DECISÃO<br>(.*)', content, re.DOTALL)
    else:
        ementa = re.search(r'EMENTA\s*(?:</?br>\s*)*([\s\S]*?)\s*(?:</?br>\s*)*VOTO', content, re.DOTALL)
        relatorio = re.search(r'RELATÓRIO\s*(?:</?br>\s*)*([\s\S]*?)\s*(?:</?br>\s*)*EMENTA', content, re.DOTALL)
        voto = re.search(r'VOTO\s*(?:</?br>\s*)*([\s\S]*?)\s*(?:</?br>\s*)*', content, re.DOTALL)
        decisao = re.search(r'DECISÃO\s*(?:</?br>\s*)*([\s\S]*?)\s*(?:</?br>\s*)*', content, re.DOTALL)

    # A função removeCRLF já está em utils.py, então podemos usá-la
    return (removeCRLF(acordao), removeCRLF(ementa), removeCRLF(relatorio),
            removeCRLF(voto), removeCRLF(decisao))


def read_txt_files_and_create_csv(directory_path, csv_file_path):
    if not os.path.exists(directory_path):
        print(f"❌ Erro: Diretório não encontrado em {directory_path}")
        return False

    txt_files = []
    print(f"\n🔎 Procurando arquivos .txt recursivamente em: {directory_path}")
    for dirpath, _, filenames in os.walk(directory_path):
        for filename in filenames:
            if filename.endswith('.txt'):
                txt_files.append(os.path.join(dirpath, filename))

    total_files = len(txt_files)

    if total_files == 0:
        print(f"⚠️ Nenhum arquivo .txt encontrado em {directory_path}")
        return False

    print(f"\n🔄 Iniciando processamento de {total_files} arquivos .txt encontrados.")
    print(f"   Salvando em: {csv_file_path}")

    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL, lineterminator='\n')
        writer.writerow(['seqDocumento', 'acordao', 'ementa', 'relatorio', 'voto', 'decisao'])

        for idx, file_path in enumerate(sorted(txt_files), 1):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                processed_data = _process_txt_content(content)
                if not processed_data:
                    continue

                relative_path = os.path.relpath(file_path, directory_path)
                print(f"   Processando {idx}/{total_files}: {relative_path}")

                seqDocumento = os.path.basename(file_path).replace('.txt', '')

                acordao, ementa, relatorio, voto, decisao = processed_data
                writer.writerow([seqDocumento, acordao, ementa, relatorio, voto, decisao])

            except Exception as e:
                print(f"      ❌ Erro ao processar o arquivo {relative_path}: {e}")
                return False

    print(f"✅ Processamento concluído. {total_files} arquivos processados.")
    return True


def read_txt_files_and_create_csv2(metadata_csv_path, search_dir, output_csv_path, log_dir):
    """
    Cria um CSV com detalhes de acórdãos, usando um CSV de metadados como guia.
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
                if 'TIPODOCUMENTO' in row and row['TIPODOCUMENTO'].upper() in ('ACÓRDÃO', 'ACORDAO'):
                    seq = row.get('SEQDOCUMENTO')
                    if seq:
                        sequences_to_process.append(seq)

        print(f"   -> Encontrados {len(sequences_to_process)} documentos do tipo 'ACÓRDÃO'.")

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


def clean_csv_empty_lines(input_csv_path, output_csv_path):
    """
    Lê um arquivo CSV, remove linhas onde todos os campos estão vazios e salva em um novo arquivo.

    :param input_csv_path: Caminho para o arquivo CSV de entrada.
    :param output_csv_path: Caminho para o arquivo CSV limpo de saída.
    """
    print(f"\n🧹 Iniciando limpeza do arquivo CSV: {input_csv_path}")

    # Aumenta o limite do tamanho do campo para lidar com textos longos (voto, relatório, etc.)
    # O padrão é 131072 (128KB), o que é muito baixo para este conjunto de dados.
    # Aumentamos para um valor muito maior para evitar o erro "field larger than field limit".
    max_int = 2147483647  # sys.maxsize para sistemas de 32 bits
    try:
        # Tenta definir o limite para o máximo possível no sistema
        csv.field_size_limit(max_int)
    except OverflowError:
        # Se falhar (comum em sistemas de 64 bits), usa um valor grande e seguro
        # Aqui, estamos usando um valor que corresponde ao máximo para um int de 32 bits.
        csv.field_size_limit(max_int)

    try:
        with open(input_csv_path, 'r', newline='', encoding='utf-8') as infile, \
                open(output_csv_path, 'w', newline='', encoding='utf-8') as outfile:

            reader = csv.reader(infile, delimiter=';')
            writer = csv.writer(outfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)

            header = next(reader)
            writer.writerow(header)

            original_row_count = 0
            cleaned_row_count = 0

            for row in reader:
                original_row_count += 1
                row = [re.sub(r'[\r\n\t]', '', field) for field in row]
                # Verifica se existe pelo menos um campo que não seja vazio ou apenas espaços em branco
                if any(field.strip() for field in row):
                    writer.writerow(row)
                    cleaned_row_count += 1

            removed_count = original_row_count - cleaned_row_count
            print(f"✅ Limpeza concluída. {removed_count} linhas em branco removidas.")
            print(f"   Arquivo limpo salvo em: {output_csv_path}")
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo de entrada não encontrado em {input_csv_path}")

    except Exception as e:
        print(f"❌ Erro inesperado durante a limpeza do CSV: {e}")
