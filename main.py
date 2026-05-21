import time
import threading
import os
import importlib
from queue import Empty, Queue
from datetime import datetime, timedelta
from const import DEFAULT_START_CONFIRMATION, TIME_START_SYSTEM
from utils import load_config, save_config

if os.name == 'nt':
    import msvcrt

'''
    Autor: Alessandro C Porto
    Objeto: Extrair dados para montar dataset para pesquisa científica da PUCPR.

    Sugere-se executar os programa por etapas e observando a captura dos dados. No site dos dados abertos, alguns dados
    podem vir em padrões diferentes a depender do período, portanto, ajustes serão necessários durante a extração dos
    dados.
'''


def input_with_timeout(prompt, timeout_seconds, default_value):
    """Lê input com timeout. Em Windows usa msvcrt para não deixar thread bloqueada no stdin."""
    if os.name == 'nt':
        print(prompt, end='', flush=True)
        typed = []
        end_time = time.time() + timeout_seconds

        while time.time() < end_time:
            if msvcrt.kbhit():
                char = msvcrt.getwche()

                if char in ('\r', '\n'):
                    print()
                    return ''.join(typed)

                if char == '\b':
                    if typed:
                        typed.pop()
                    continue

                typed.append(char)

            time.sleep(0.05)

        print(f"\n⏳ Sem confirmação em {timeout_seconds} segundos. Iniciando automaticamente...")
        return default_value

    # Fallback para outros sistemas
    result_queue = Queue(maxsize=1)

    def _read_input():
        try:
            result_queue.put(input(prompt))
        except EOFError:
            result_queue.put('')

    input_thread = threading.Thread(target=_read_input, daemon=True)
    input_thread.start()

    try:
        return result_queue.get(timeout=timeout_seconds)
    except Empty:
        print(f"\n⏳ Sem confirmação em {timeout_seconds} segundos. Iniciando automaticamente...")
        return default_value


def get_user_config():
    """
    Exibe menu interativo para o usuário configurar:
    - Ano para extração (YEAR_DOWNLOAD)
    - Tipo de documento (LISTA_TIPO_DOCUMENTO)
    Salva as configurações em config.json
    """
    config = load_config('config.json')
    
    print("\n" + "=" * 60)
    print("⚙️  CONFIGURAÇÃO DO SISTEMA")
    print("=" * 60)
    
    # Pergunta sobre o ano
    print(f"\n📅 Ano para extração (padrão: {config['year_download']}):")
    print("   Pressione Enter para manter o valor padrão")
    year_input = input("   Digite o ano (YYYY): ").strip()
    
    if year_input:
        config['year_download'] = year_input
        print(f"   ✅ Ano configurado: {year_input}")
    else:
        print(f"   ✅ Ano mantido: {config['year_download']}")
    
    # Pergunta sobre o tipo de documento
    print(f"\n📄 Tipo de documento (padrão: {config['tipo_documento']}):")
    print("   1 - DECISÃO")
    print("   2 - ACÓRDÃO")
    print("   Pressione Enter para manter o valor padrão")
    
    tipo_input = input("   Digite a opção (1 ou 2): ").strip()
    
    if tipo_input == '1':
        config['tipo_documento'] = 'DECISAO'
        print("   ✅ Tipo configurado: DECISÃO")
    elif tipo_input == '2':
        config['tipo_documento'] = 'ACORDAO'
        print("   ✅ Tipo configurado: ACÓRDÃO")
    else:
        print(f"   ✅ Tipo mantido: {config['tipo_documento']}")
    
    # Salva as configurações
    if save_config(config, 'config.json'):
        print("\n✅ Configurações salvas com sucesso!")
    
    print("=" * 60 + "\n")
    
    return config

def main():
    # """Função principal para orquestrar os passos de extração e processamento de dados."""
    
    print("=" * 60)
    print("📥 Olá! Bem-vindo ao Extrator de Dados de Acórdãos e Decisões.")
    print("=" * 60)
    
    resposta = input_with_timeout(
        f"\nDeseja iniciar a execução do processo de extração? (s/n) [auto em {TIME_START_SYSTEM}s]: ",
        timeout_seconds=TIME_START_SYSTEM,
        default_value=DEFAULT_START_CONFIRMATION
    )
    
    if resposta.strip().upper() != 'S':
        print("\nExecução cancelada pelo usuário.")
        return
    
    print("\n" + "-" * 60)
    print("⚙️  Configurando parâmetros de extração...")
    print("-" * 60)
    
    # Agora obtém as configurações do usuário (APÓS confirmação)
    get_user_config()
    
    # Recarrega as constantes e a biblioteca principal com as novas configurações
    import const
    import lib
    importlib.reload(const)
    importlib.reload(lib)
    from const import DIR_PATH_DOWNLOAD_DADOS_METADADOS, DIR_PATH_OUTPUT_DADOS_METADADOS, UNZIP_DIR_PATH, DIR_PATH_OUTPUT_DECISOES_ACORDAOS, DIR_PATH_OUTPUT
        
    print("\n" + "-" * 60)
    print("🚀 Iniciando extração de dados...")
    print("-" * 60)
    
    #01
    if not lib.download_zip_files():
        print("Falha ao baixar os arquivos zip.")
        return
    print("Arquivos zip baixados com sucesso.")

    #02
    if not lib.download_json_metadados():
        print("Falha ao baixar os arquivos JSON.")
        return
    print("Arquivos JSON baixados com sucesso.")

    #03
    if not lib.extract_zip_files():
        print("Falha ao extrair os arquivos zip.")
        return
    print("Arquivos zip extraídos com sucesso.")

    #04
    if not lib.json_directory_to_csv(DIR_PATH_DOWNLOAD_DADOS_METADADOS, DIR_PATH_OUTPUT_DADOS_METADADOS):
        print("Falha ao gerar o CSV de metadados.")
        return
    print("Sucesso! CSV gerado com metadados dos acórdãos e decisões.")

    #05
    if not lib.read_txt_files_and_create_csv(DIR_PATH_OUTPUT_DADOS_METADADOS, UNZIP_DIR_PATH, DIR_PATH_OUTPUT_DECISOES_ACORDAOS, DIR_PATH_OUTPUT):
        print("Falha ao gerar o CSV com os dados dos acórdãos.")
        return
    print("Sucesso! CSV gerado com os dados de acórdãos e decisões.")

if __name__ == "__main__":
    start_time_display = datetime.now()
    start_time_perf = time.perf_counter()
    print(f"⏱️ Início da execução: {start_time_display.strftime('%d/%m/%Y %H:%M:%S')}")
    print("-" * 60)

    # Importar lib e funções de configuração
    import lib
    
    # Executar main()
    main()

    end_time_display = datetime.now()
    end_time_perf = time.perf_counter()
    duration_seconds = end_time_perf - start_time_perf
    total_duration = str(timedelta(seconds=duration_seconds)).split('.')[0] # Formata para HH:MM:SS

    print("-" * 60)
    print(f"🏁 Fim da execução: {end_time_display.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"⏱️ Tempo total de execução: {total_duration}")