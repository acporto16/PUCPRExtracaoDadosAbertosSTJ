from lib import *
import time
from datetime import datetime, timedelta
import pkg_resources

'''
    Autor: Alessandro C Porto
    Objeto: Extrair dados para montar dataset para pesquisa científica da PUCPR.

    Sugere-se executar os programa por etapas e observando a captura dos dados. No site dos dados abertos, alguns dados
    podem vir em padrões diferentes a depender do período, portanto, ajustes serão necessários durante a extração dos
    dados.
'''

def print_installed_libraries():
    print("Bibliotecas instaladas no ambiente:")
    installed_packages = pkg_resources.working_set
    installed_packages_list = sorted(["%s==%s" % (i.key, i.version) for i in installed_packages])
    for package in installed_packages_list:
        print(f"  - {package}")
    print("-" * 60)

def main():
    # """Função principal para orquestrar os passos de extração e processamento de dados."""
    
    print("=" * 60)
    print("👋 Olá! Bem-vindo ao Extrator de Dados de Acórdãos e Decisões.")
    print("=" * 60)
    
    print_installed_libraries()
    
    resposta = input("\nDeseja iniciar a execução do processo de extração? (s/n): ")
    
    if resposta.lower() != 's':
        print("\nExecução cancelada pelo usuário.")
        return
        
    print("\n" + "-" * 60)
    print("🚀 Iniciando extração de dados...")
    print("-" * 60)
    
    #01
    if not download_zip_files():
        print("Falha ao baixar os arquivos zip.")
        return
    print("Arquivos zip baixados com sucesso.")

    #02
    if not download_json_metadados():
        print("Falha ao baixar os arquivos JSON.")
        return
    print("Arquivos JSON baixados com sucesso.")

    #03
    if not extract_zip_files():
        print("Falha ao extrair os arquivos zip.")
        return
    print("Arquivos zip extraídos com sucesso.")

    #04
    if not json_directory_to_csv(DIR_PATH_DOWNLOAD_DADOS_METADADOS, DIR_PATH_OUTPUT_DADOS_METADADOS):
        print("Falha ao gerar o CSV de metadados.")
        return
    print("Sucesso! CSV gerado com metadados dos acórdãos e decisões.")

    #05
    if not read_txt_files_and_create_csv(DIR_PATH_OUTPUT_DADOS_METADADOS, UNZIP_DIR_PATH, DIR_PATH_OUTPUT_DECISOES_ACORDAOS, DIR_PATH_OUTPUT):
        print("Falha ao gerar o CSV com os dados dos acórdãos.")
        return
    print("Sucesso! CSV gerado com os dados de acórdãos e decisões.")

if __name__ == "__main__":
    start_time_display = datetime.now()
    start_time_perf = time.perf_counter()
    print(f"⏱️ Início da execução: {start_time_display.strftime('%d/%m/%Y %H:%M:%S')}")
    print("-" * 60)

    main()

    end_time_display = datetime.now()
    end_time_perf = time.perf_counter()
    duration_seconds = end_time_perf - start_time_perf
    total_duration = str(timedelta(seconds=duration_seconds)).split('.')[0] # Formata para HH:MM:SS

    print("-" * 60)
    print(f"🏁 Fim da execução: {end_time_display.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"⏱️ Tempo total de execução: {total_duration}")