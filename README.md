ac# PUCPR - Extrator de Dados Abertos do STJ

### Propósito
Este projeto tem como objetivo automatizar a extração e o processamento de dados abertos do Superior Tribunal de Justiça (STJ), visando a criação de um dataset estruturado para fins de pesquisa científica na PUCPR.

### Principais Regras de Negócio
- **RN01 - Data de Início da Publicação no DJE:** A data de publicação no Diário da Justiça Eletrônico (DJE) iniciou em 2021, como precisamos da primeira resposta -- liminar --, o sistema não pode extrair dados cuja data de recebimento seja anterior a 01/01/2021.

### Funcionalidades Principais
- **Download Automatizado:** Captura arquivos ZIP e metadados JSON diretamente do portal de dados abertos do STJ.
- **Processamento de Dados:** Descompacta arquivos, extrai o conteúdo textual de decisões e acórdãos e consolida as informações.
- **Estruturação:** Converte metadados e conteúdos processados para o formato CSV, facilitando a análise de dados.
- **Filtro por Classe Processual:** Valida o campo `PROCESSO` durante a extração dos metadados, usando a classe informada pelo usuário.
- **Modo Híbrido para TXT:** Processa diretamente dos ZIPs e salva em disco apenas os TXT correspondentes aos metadados filtrados.
- **Extração de RELATÓRIO/DECISÃO:** No processamento textual, aceita documentos iniciados por `DECISÃO` ou `DESPACHO` para separação de campos.
- **Restrição do Período de Extração:** Em atendimento a RN01, o sistema não pode extrair dados cuja data de recebimento seja anterior a 01/01/2021.
- **✨ NOVO: Configuração Interativa:** Menu intuitivo para configurar parâmetros sem editar código-fonte.

### Formatos de Data Suportados
O sistema já valida e normaliza múltiplos formatos de data para o padrão `DD/MM/YYYY`.

- **Numéricos:** `YYYYMMDD`, timestamp em segundos e timestamp em milissegundos.
- **ISO 8601:** `YYYY-MM-DD`, `YYYY-MM-DD HH:MM:SS`, `YYYY-MM-DDTHH:MM:SS`, variantes com fração de segundos e timezone (ex.: `Z`, `+00:00`).
- **Brasileiros:** `DD/MM/YYYY`, `DD/MM/YYYY HH:MM:SS` e `DD/MM/YYYY HH:MM`.

Essa validação é aplicada durante a extração dos metadados (incluindo `DATARECEBIMENTO`) e no parâmetro de corte da RN01 (`ANO-PUBLICACAO-DJE`).

### Como Utilizar

#### ⚡ Início Rápido
```bash
python main.py
```
O sistema exibirá um menu para você configurar o ano e o tipo de documento. Pressione Enter para usar valores padrão.
Também é possível informar a **classe processual** que será usada apenas como filtro na extração dos metadados.

**Documentação rápida:** Veja `COMECO_RAPIDO.md` para começar em 30 segundos.

#### 📋 Configuração Detalhada

A partir da **version 2.0**, o sistema oferece um **menu interativo** na inicialização:
- O usuário define o **ano** para extração
- O usuário escolhe o **tipo de documento** (DECISÃO, ACÓRDÃO ou GERAL para ambos)
- O usuário informa a **classe processual** de forma livre, por exemplo `HC`, `REsp`, `AREsp` ou outra sigla/texto disponível no metadado
- As configurações são **aplicadas apenas na execução atual**

> Observação: a classe processual é usada somente para filtragem durante a leitura do JSON de metadados. No modo híbrido, apenas os TXT correspondentes aos `SEQDOCUMENTO` filtrados são salvos em disco.
> Observação: `FORCE-DOWNLOAD` (`S`/`N`) é lido de `config.json` e não é perguntado no menu interativo.

**Documentação completa:** Consulte `CONFIGURACAO.md` para instruções detalhadas.

#### Instalação de Dependências
```powershell
py -3 -m pip install requests
```

#### (Opcional) Exportar todas as bibliotecas instaladas com versão
```powershell
py -3 -m pip freeze
```

### 📚 Documentação

| Documento | Descrição | Para Quem |
|-----------|-----------|-----------|
| `COMECO_RAPIDO.md` | Guia em 30 segundos | Quem quer começar já |
| `CONFIGURACAO.md` | Guia completo de uso | Usuários finais |
| `EXEMPLOS_EXECUCAO.md` | Exemplos práticos | Quem quer ver exemplos |
| `RESUMO_ALTERACOES.md` | Detalhes técnicos | Desenvolvedores |
| `TESTES.md` | Guia de testes | QA / Testadores |
| `INDICE.md` | Índice completo | Quem precisa navegar |

---

**Versão:** 2.0 (Com Sistema de Configuração Interativa)
*Autor: Alessandro C Porto*
*Última atualização: 21/05/2026*
