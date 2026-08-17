import time
import threading
import os
import importlib
import sys
from queue import Empty, Queue
from datetime import datetime, timedelta
from const import DEFAULT_START_CONFIRMATION, TIME_START_SYSTEM
from utils import load_config, set_runtime_config_override, normalize_toggle_flag

if os.name == 'nt':
    import msvcrt

'''
    Autor: Alessandro C Porto
    Objeto: Extrair dados para montar dataset para pesquisa científica da PUCPR.

    Sugere-se executar os programa por etapas e observando a captura dos dados. No site dos dados abertos, alguns dados
    podem vir em padrões diferentes a depender do período, portanto, ajustes serão necessários durante a extração dos
    dados.
'''


def configure_console_encoding():
    """Configura saída UTF-8 para evitar erro de encode em consoles Windows cp1252."""
    if os.name != 'nt':
        return

    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')


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
    - Mês para extração (MONTH_DOWNLOAD)
    - Tipo de documento (LISTA_TIPO_DOCUMENTO)
    Aplica as configurações apenas na execução atual (sem salvar em config.json)
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

    current_month = config.get('month_download')
    current_month_display = str(current_month).zfill(2) if current_month not in (None, '') else 'todos'

    print(f"\n🗓️  Mês para extração (padrão: {current_month_display}):")
    print("   Informe um valor entre 1 e 12")
    print("   Pressione Enter para manter o valor padrão")
    print("   Digite 0 para processar todos os meses do ano")

    month_input = input("   Digite o mês (MM): ").strip()

    if month_input:
        if month_input == '0':
            config['month_download'] = None
            print("   ✅ Mês configurado: todos os meses")
        elif month_input.isdigit() and 1 <= int(month_input) <= 12:
            config['month_download'] = str(int(month_input)).zfill(2)
            print(f"   ✅ Mês configurado: {config['month_download']}")
        else:
            print(f"   ⚠️ Mês inválido. Mantendo valor atual: {current_month_display}")
    else:
        print(f"   ✅ Mês mantido: {current_month_display}")
    
    # Pergunta sobre o tipo de documento
    print(f"\n📄 Tipo de documento (padrão: {config['tipo_documento']}):")
    print("   1 - DECISÃO")
    print("   2 - ACÓRDÃO")
    print("   3 - GERAL (ambos)")
    print("   Pressione Enter para manter o valor padrão")
    
    tipo_input = input("   Digite a opção (1, 2 ou 3): ").strip()
    
    if tipo_input == '1':
        config['tipo_documento'] = 'DECISAO'
        print("   ✅ Tipo configurado: DECISÃO")
    elif tipo_input == '2':
        config['tipo_documento'] = 'ACORDAO'
        print("   ✅ Tipo configurado: ACÓRDÃO")
    elif tipo_input == '3':
        config['tipo_documento'] = 'GERAL'
        print("   ✅ Tipo configurado: GERAL (DECISÃO + ACÓRDÃO)")
    else:
        print(f"   ✅ Tipo mantido: {config['tipo_documento']}")

    # Classe processual com preenchimento livre
    classe_atual = str(config.get('classe_processual', 'HC')).strip()
    print(f"\n⚖️  Classe processual para filtro (padrão: {classe_atual}):")
    print("   Exemplo: HC, REsp, AREsp, AgRg")
    print("   Pressione Enter para manter o valor padrão")

    classe_input = input("   Digite a classe processual: ").strip()
    if classe_input:
        config['classe_processual'] = classe_input
        print(f"   ✅ Classe configurada: {classe_input}")
    else:
        print(f"   ✅ Classe mantida: {classe_atual}")

    # FORCE-DOWNLOAD é controlado apenas por configuração (sem prompt interativo)
    force_download_atual = str(config.get('FORCE-DOWNLOAD', 'N')).strip().upper()
    if force_download_atual not in ('S', 'N'):
        force_download_atual = 'N'
    config['FORCE-DOWNLOAD'] = force_download_atual
    
    # Aplica as configurações somente em memória para esta execução
    set_runtime_config_override(config)
    print("\n✅ Configurações aplicadas para esta execução (sem salvar em config.json).")
    
    print("=" * 60 + "\n")
    
    return config


def run_configured_flow():
    """Executa o fluxo principal usando a configuração já carregada em const/lib."""
    import const
    import lib
    importlib.reload(const)
    importlib.reload(lib)
    from const import DIR_PATH_DOWNLOAD_DADOS_METADADOS, DIR_PATH_OUTPUT_DADOS_METADADOS, ZIP_DIR_PATH, DIR_PATH_OUTPUT_DECISOES_ACORDAOS, DIR_PATH_OUTPUT, UNZIP_DIR_PATH

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
    if not lib.json_directory_to_csv(DIR_PATH_DOWNLOAD_DADOS_METADADOS, DIR_PATH_OUTPUT_DADOS_METADADOS):
        print("Falha ao gerar o CSV de metadados.")
        return
    print("Sucesso! CSV gerado com metadados dos acórdãos e decisões.")

    #04
    if not lib.read_txt_files_and_create_csv(DIR_PATH_OUTPUT_DADOS_METADADOS, ZIP_DIR_PATH, DIR_PATH_OUTPUT_DECISOES_ACORDAOS, DIR_PATH_OUTPUT, UNZIP_DIR_PATH):
        print("Falha ao gerar o CSV com os dados dos acórdãos.")
        return
    print("Sucesso! CSV gerado com os dados de acórdãos e decisões e TXT selecionados salvos localmente.")

def main():
    # """Função principal para orquestrar os passos de extração e processamento de dados."""
    
    print("=" * 60)
    print("📥 Olá! Bem-vindo ao Extrator de Dados de Acórdãos e Decisões.")
    print("=" * 60)
    
    config = load_config('config.json')
    auto_loading = normalize_toggle_flag(config.get('AUTO-LOADING', config.get('auto_loading', 'N')))

    if auto_loading == 'S':
        print("\n⚙️ AUTO-LOADING=S: executando sem prompts, usando apenas config.json.")
        set_runtime_config_override(config)
        run_configured_flow()
        return

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
    run_configured_flow()

if __name__ == "__main__":
    configure_console_encoding()
    start_time_display = datetime.now()
    start_time_perf = time.perf_counter()
    print(f"⏱️ Início da execução: {start_time_display.strftime('%d/%m/%Y %H:%M:%S')}")
    print("-" * 60)
    
    # Executar main()
    main()

    end_time_display = datetime.now()
    end_time_perf = time.perf_counter()
    duration_seconds = end_time_perf - start_time_perf
    total_duration = str(timedelta(seconds=duration_seconds)).split('.')[0] # Formata para HH:MM:SS

    print("-" * 60)
    print(f"🏁 Fim da execução: {end_time_display.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"⏱️ Tempo total de execução: {total_duration}")