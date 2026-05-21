# 🔄 Fluxo do Sistema - Diagrama Visual

## 📊 Fluxo de Execução Completo

```
┌─────────────────────────────────────────────────────────────┐
│                    INÍCIO DO PROGRAMA                       │
│                    (python main.py)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         EXIBIR SAUDAÇÃO E PERGUNTA DE CONFIRMAÇÃO           │
│  ============================================================│
│  📥 Bem-vindo ao Extrator de Dados de Acórdãos e Decisões   │
│  ============================================================│
│                                                             │
│  Deseja iniciar a execução do processo de extração?         │
│  (s/n) [auto em 3s]:                                        │
│                                                             │
│  ├─► Resposta SIM (S) → Continua para configuração         │
│  ├─► Resposta NÃO (N) → Encerra                            │
│  └─► Timeout 3s → Auto-continua                            │
└────────────────────────┬────────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼ (SIM ou Timeout)    ▼ (NÃO)
   ┌──────────────────────┐   ┌──────────────────┐
   │CONFIGURAÇÃO DO      │   │ENCERRAR NORMAL  │
   │SISTEMA              │   │                  │
   │                      │   │                  │
   │1. Menu de Ano       │   │                  │
   │   2023, 2022, ...   │   │                  │
   │                      │   │                  │
   │2. Menu de Tipo      │   │                  │
   │   1=DECISÃO         │   │                  │
   │   2=ACÓRDÃO         │   │                  │
   │                      │   │                  │
   │3. Salvar config.json│   │                  │
   │                      │   └──────────────────┘
   └──────────┬───────────┘           │
              │                       │
              ▼                       │
   ┌──────────────────────┐         │
   │RECARREGAR CONSTANTES │         │
   │                      │         │
   │const.py carrega      │         │
   │config.json (novamente)         │
   │                      │         │
   │- YEAR_DOWNLOAD  ✓   │         │
   │- LISTA_TIPO DOC ✓   │         │
   └──────────┬───────────┘         │
              │                     │
              ▼                     │
   ┌──────────────────────┐         │
   │INICIAR EXTRAÇÃO     │         │
   │                      │         │
   │01 download_zip_files│         │
   │02 download_json    │         │
   │03 extract_zip      │         │
   │04 json_to_csv      │         │
   │05 read_txt_files   │         │
   │                      │         │
   │ ...processo...      │         │
   │ ...continua...      │         │
   └──────────┬───────────┘         │
              │                     │
              └────────────┬────────┘
                           ▼
            ┌─────────────────────────────────┐
            │  FIM DO PROGRAMA                │
            │  🏁 Tempo total de execução     │
            └─────────────────────────────────┘
```

---

## 🔗 Relacionamento entre Arquivos

```
main.py (entrada)
    │
    ├─► load_config() ──────────► config.json (arquivo de config)
    ├─► get_user_config() ──────► [Menu interativo]
    ├─► save_config() ──────────► config.json (atualizado)
    │
    └─► from lib import *
            │
            ├─► lib.py
            │   └─► from const import *
            │       └─► const.py
            │           ├─► load_config() (carrega novamente)
            │           ├─► YEAR_DOWNLOAD = config['year_download']
            │           ├─► LISTA_TIPO_DOCUMENTO = [mapear tipo]
            │           └─► ... outras constantes ...
            │
            └─► from utils import *
                └─► utils.py
                    ├─► load_config()
                    ├─► save_config()
                    └─► ... outras funções ...
```

---

## 🎯 Estados Possíveis

### Estado 1: Primeiro Uso
```
❌ config.json não existe
         │
         ▼
✅ Sistema cria config.json com valores padrão
         │
         ▼
👤 Usuário interage com menu interativo
         │
         ▼
💾 config.json é salvo com escolhas do usuário
```

### Estado 2: Uso Subsequente
```
✅ config.json existe
         │
         ▼
📖 Valores padrão carregados de config.json
         │
         ▼
👤 Usuário pode:
   ├─ Pressionar Enter → Mantém valores
   ├─ Digitar novos valores → Atualiza config.json
   └─ [Timeout 3s] → Auto-mantém valores
         │
         ▼
💾 Configuração final salva em config.json
```

---

## 🔄 Ciclo de Vida das Configurações

```
CICLO 1:
First Execution → Configure → Save → CICLO 2

CICLO 2:
Load from config.json → Display Menu → User Input → Update → Save

CICLO 3:
Load from config.json → Display Menu → User Input → Update → Save

... repete indefinidamente ...
```

---

## 🎛️ Mapeamento de Decisões

### Entrada do Usuário → Ação

```
Year Input:
├─ [vazio] ──────► Mantém valor atual
├─ [válido] ─────► year_download = entrada
└─ [inválido] ──► Mantém valor atual (sem validação de ano)

Type Input:
├─ "1" ──────────► tipo_documento = "DECISAO"
├─ "2" ──────────► tipo_documento = "ACORDAO"
├─ [vazio] ──────► Mantém valor atual
└─ [outro] ─────► Mantém valor atual (entrada ignorada)

Confirmation:
├─ "S" ou "s" ──► Inicia extração
├─ "N" ou "n" ──► Encerra programa
├─ [vazio] ─────► Aguarda 3s, depois auto-inicia
└─ [outro] ─────► Trata como NÃO (encerra)
```

---

## 📁 Arquivos de Dados

### config.json (Estrutura)
```json
{
  "year_download": "string (YYYY)",
  "month_download": "number ou null",
  "tipo_documento": "DECISAO ou ACORDAO",
  "auto_start_seconds": "number (segundos)"
}
```

### Fluxo de Dados
```
User Input → get_user_config()
             │
             ▼
         config dict
             │
             ├─► save_config() → config.json (arquivo)
             │
             └─► const.py lê novamente
                 │
                 ▼
             YEAR_DOWNLOAD = config['year_download']
             LISTA_TIPO_DOCUMENTO = [é mapeado]
                 │
                 ▼
             lib.py usa constantes
                 │
                 ▼
             main() executa com valores corretos
```

---

## ⏱️ Cronograma de Execução

```
Tempo │ Evento
  0s  │ Início do programa
------│─────────────────────────────────
  0s  │ Exibir menu de configuração
  -   │ Aguardando entrada do usuário
  -   │ Processando entrada
  -   │ Salvando config.json
  2s  │ Importando lib (carrega const com novos valores)
------│─────────────────────────────────
  2s  │ Exibir menu de confirmação
      │ ├─ Se responder: ~imediato
      │ └─ Se timeout: aguarda até 3s
------│─────────────────────────────────
  5s  │ Iniciando extração (se SIM ou timeout)
  N   │ Processando downloads, conversões, etc.
      │ (tempo varia de acordo com volume de dados)
------│─────────────────────────────────
  K   │ Extração completa OU encerrada pelo usuário
  K   │ Exibir relatório final
  K   │ Encerrar programa (fim)
```

---

## 🎨 Template do Menu Interativo

```
╔═══════════════════════════════════════════════════════╗
║            CONFIGURAÇÃO DO SISTEMA              ║
╚═══════════════════════════════════════════════════════╝

┌─ PERGUNTA 1 ─────────────────────────────────────────┐
│ 📅 Ano para extração (padrão: 2021):                 │
│    Pressione Enter para manter o valor padrão        │
│    Digite o ano (YYYY): [input]                      │
│    ✅ Ano configurado: 2023                          │
└─────────────────────────────────────────────────────┘

┌─ PERGUNTA 2 ─────────────────────────────────────────┐
│ 📄 Tipo de documento (padrão: ACORDAO):             │
│    1 - DECISÃO                                       │
│    2 - ACÓRDÃO                                       │
│    Pressione Enter para manter o valor padrão        │
│    Digite a opção (1 ou 2): [input]                 │
│    ✅ Tipo configurado: DECISÃO                     │
└─────────────────────────────────────────────────────┘

┌─ CONFIRMAÇÃO ─────────────────────────────────────────┐
│ ✅ Configurações salvas com sucesso!                 │
└─────────────────────────────────────────────────────┘
```

---

## 🔐 Validação de Dados

### Year (Ano)
```
Input:     string (YYYY)
Validação: Nenhuma (aceita qualquer valor)
Resultado: year_download = input
Padrão:    "2021"
```

### Type (Tipo)
```
Input:     "1", "2", vazio, ou outro
Validação: 
  ├─ "1" → DECISAO
  ├─ "2" → ACORDAO
  └─ qualquer outra coisa → mantém anterior
Padrão:    "ACORDAO"
```

### Confirmation (Confirmação)
```
Input:     "S", "N", ou vazio
Validação:
  ├─ S/s → continua
  ├─ N/n → cancela
  └─ vazio → aguarda 3s e continua (timeout)
Padrão:    'S' (após timeout)
```

---

## 📊 Resumo da Arquitetura

```
┌────────────────────────────────────────────────┐
│           CAMADA DE APRESENTAÇÃO               │
│  ┌──────────────────────────────────────────┐  │
│  │  Menu Interativo (get_user_config)       │  │
│  │  - Input Year                            │  │
│  │  - Input Type (1/2)                      │  │
│  │  - Validation & Feedback                 │  │
│  └──────────────────────────────────────────┘  │
└────────────────┬───────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────┐
│         CAMADA DE PERSISTÊNCIA                 │
│  ┌──────────────────────────────────────────┐  │
│  │  config.json (JSON File Storage)         │  │
│  │  - year_download                         │  │
│  │  - tipo_documento                        │  │
│  │  - other config params                   │  │
│  └──────────────────────────────────────────┘  │
└────────────────┬───────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────┐
│         CAMADA DE CONFIGURAÇÃO                 │
│  ┌──────────────────────────────────────────┐  │
│  │  const.py (Constantes do Sistema)        │  │
│  │  - YEAR_DOWNLOAD                         │  │
│  │  - LISTA_TIPO_DOCUMENTO                  │  │
│  │  - DIR_PATH_*                            │  │
│  │  - Outras constantes                     │  │
│  └──────────────────────────────────────────┘  │
└────────────────┬───────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────┐
│         CAMADA DE EXECUÇÃO                     │
│  ┌──────────────────────────────────────────┐  │
│  │  lib.py (Funções Principais)             │  │
│  │  - download_zip_files()                  │  │
│  │  - json_directory_to_csv()               │  │
│  │  - read_txt_files_and_create_csv()       │  │
│  │  - usa constantes de const.py            │  │
│  └──────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

---

**Diagrama completo do sistema de configuração interativa**
*Atualizado em: 21/05/2026*

