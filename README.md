# PUCPR - Extrator de Dados Abertos do STJ

### Propósito
Este projeto tem como objetivo automatizar a extração e o processamento de dados abertos do Superior Tribunal de Justiça (STJ), visando a criação de um dataset estruturado para fins de pesquisa científica na PUCPR.

### Funcionalidades Principais
- **Download Automatizado:** Captura arquivos ZIP e metadados JSON diretamente do portal de dados abertos do STJ.
- **Processamento de Dados:** Descompacta arquivos, extrai o conteúdo textual de decisões e acórdãos e consolida as informações.
- **Estruturação:** Converte metadados e conteúdos processados para o formato CSV, facilitando a análise de dados.
- **✨ NOVO: Configuração Interativa:** Menu intuitivo para configurar parâmetros sem editar código-fonte.

### Como Utilizar

#### ⚡ Início Rápido
```bash
python main.py
```
O sistema exibirá um menu para você configurar o ano e o tipo de documento. Pressione Enter para usar valores padrão.

**Documentação rápida:** Veja `COMECO_RAPIDO.md` para começar em 30 segundos.

#### 📋 Configuração Detalhada

A partir da **version 2.0**, o sistema oferece um **menu interativo** na inicialização:
- O usuário define o **ano** para extração
- O usuário escolhe o **tipo de documento** (DECISÃO ou ACÓRDÃO)
- As configurações são **salvas automaticamente** em `config.json`

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
