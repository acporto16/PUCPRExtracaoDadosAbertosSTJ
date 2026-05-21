# 📋 Guia de Configuração do Sistema

## Visão Geral

O sistema foi atualizado para permitir que o usuário configure dinamicamente os parâmetros de extração de dados na inicialização do programa, sem necessidade de editar o código-fonte.

## Como Funciona

### 1. Menu de Confirmação da Execução

Quando você executa o programa (`main.py`), aparecerá **primeiro** um menu de confirmação:

```
============================================================
📥 Olá! Bem-vindo ao Extrator de Dados de Acórdãos e Decisões.
============================================================

Deseja iniciar a execução do processo de extração? (s/n) [auto em 3s]: 
```

- Digite **S** para SIM (continua)
- Digite **N** para NÃO (encerra)
- Pressione Enter para auto-iniciar em 3 segundos

### 2. Menu Interativo de Configuração (Se SIM)

**Apenas se responder SIM**, o sistema perguntará sobre a configuração:

```
------------------------------------------------------------
⚙️  Configurando parâmetros de extração...
------------------------------------------------------------

============================================================
⚙️  CONFIGURAÇÃO DO SISTEMA
============================================================

📅 Ano para extração (padrão: 2021):
   Pressione Enter para manter o valor padrão
   Digite o ano (YYYY): 

📄 Tipo de documento (padrão: ACORDAO):
   1 - DECISÃO
   2 - ACÓRDÃO
   Pressione Enter para manter o valor padrão
   Digite a opção (1 ou 2): 
```

### 2. Opções de Configuração

#### **Ano (YEAR_DOWNLOAD)**
- **O quê:** Define o ano para o qual você deseja extrair dados
- **Formato:** YYYY (ex: 2021, 2022, 2023)
- **Padrão:** 2021
- **Como usar:** Digite o ano desejado ou pressione Enter para manter o padrão

#### **Tipo de Documento (LISTA_TIPO_DOCUMENTO)**
- **Opção 1:** DECISÃO - Extrai apenas documentos do tipo "Decisão"
- **Opção 2:** ACÓRDÃO - Extrai apenas documentos do tipo "Acórdão"
- **Padrão:** ACÓRDÃO
- **Como usar:** Digite `1` ou `2`, ou pressione Enter para manter o padrão

### 3. Arquivo de Configuração (config.json)

As configurações são armazenadas em um arquivo chamado `config.json` na raiz do projeto:

```json
{
  "year_download": "2021",
  "month_download": null,
  "tipo_documento": "ACORDAO",
  "auto_start_seconds": 3
}
```

- **Você pode editar este arquivo manualmente** se preferir configurar valores padrão diferentes
- **As alterações são salvas automaticamente** quando você usa o menu interativo
- **O arquivo é preservado** entre execuções do programa

## Exemplos de Uso

### Exemplo 1: Manter Valores Padrão
```
Digite o ano (YYYY): [pressione Enter]
Digite a opção (1 ou 2): [pressione Enter]
```
Resultado: Usando 2021 e ACÓRDÃO (valores padrão)

### Exemplo 2: Customizar Tudo
```
Digite o ano (YYYY): 2023
Digite a opção (1 ou 2): 1
```
Resultado: Usando 2023 e DECISÃO

### Exemplo 3: Apenas Mudar o Tipo de Documento
```
Digite o ano (YYYY): [pressione Enter]
Digite a opção (1 ou 2): 1
```
Resultado: Usando 2021 (padrão) e DECISÃO

## Estrutura dos Arquivos

| Arquivo | Função | Editável? |
|---------|--------|-----------|
| `config.json` | Armazena as configurações | ✅ Sim |
| `const.py` | Carrega as configurações de `config.json` | ❌ Não (modificado automaticamente) |
| `main.py` | Exibe o menu interativo | ❌ Não recomendado |
| `utils.py` | Funções de gerenciamento de config | ❌ Não modificar |

## Valores Padrão

| Parâmetro | Padrão |
|-----------|--------|
| Ano | 2021 |
| Mês | null (todos os meses) |
| Tipo de Documento | ACORDAO |
| Timeout de Confirmação | 3 segundos |

## Pergunta Frequente (FAQ)

**P: Posso editar `config.json` manualmente?**
R: Sim! Você pode editar o arquivo `config.json` diretamente com um editor de texto. Apenas certifique-se de manter o formato JSON válido.

**P: O que acontece se eu pressionar Enter em ambas as perguntas?**
R: O sistema mantém os valores definidos em `config.json`, que por padrão são: 2021, ACÓRDÃO.

**P: Posso resetar as configurações para o padrão?**
R: Sim! Delete o arquivo `config.json` ou edite-o manualmente com os valores padrão. Na próxima execução, o sistema criará automaticamente um novo `config.json` com os valores padrão.

**P: As configurações são persistentes entre execuções?**
R: Sim! As alterações são salvas no `config.json` e permanecerão para as próximas execuções.

## Valores Especiais

- **month_download:** Deixe como `null` (sem aspas) para extrair dados de todos os meses do ano especificado
- Se quiser extrair dados de um mês específico, edite `config.json` e altere `"month_download": null` para `"month_download": 3` (para março, por exemplo)

## Suporte Técnico

Se encontrar erros ou problemas:
1. Verifique se o arquivo `config.json` está em formato JSON válido
2. Certifique-se de que os valores de ano estão no formato correto (YYYY)
3. Verifique se os permissões de arquivo estão corretas para leitura/escrita

