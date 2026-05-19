# PUCPR - Extrator de Dados Abertos do STJ

### Propósito
Este projeto tem como objetivo automatizar a extração e o processamento de dados abertos do Superior Tribunal de Justiça (STJ), visando a criação de um dataset estruturado para fins de pesquisa científica na PUCPR.

### Funcionalidades Principais
- **Download Automatizado:** Captura arquivos ZIP e metadados JSON diretamente do portal de dados abertos do STJ.
- **Processamento de Dados:** Descompacta arquivos, extrai o conteúdo textual de decisões e acórdãos e consolida as informações.
- **Estruturação:** Converte metadados e conteúdos processados para o formato CSV, facilitando a análise de dados.

### Como Utilizar
1.  **Configuração:** Ajuste o ano e o mês de referência no arquivo `const.py`.
2.  **Execução:** Inicie o processo através do script principal `main.py`.
3.  **Ambiente:** Requer Python 3.12 e as bibliotecas listadas no ambiente de execução.


#### Dependências externas usadas pelo projeto
- `requests`

#### Instalação sugerida
```powershell
py -3 -m pip install requests
```

#### (Opcional) Exportar todas as bibliotecas instaladas com versão
```powershell
py -3 -m pip freeze
```

---
*Autor: Alessandro C Porto*

