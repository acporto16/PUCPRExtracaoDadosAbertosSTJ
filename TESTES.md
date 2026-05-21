# 🧪 Guia de Testes - Sistema de Configuração Interativa

## Pré-requisitos para Testes

- Python 3.7+
- Arquivo `config.json` presente no diretório raiz
- Todos os arquivos (.py, .json) com encoding UTF-8

## 🔍 Testes de Validação

### Teste 1: Carregamento Básico ✅

**Objetivo:** Verificar se o sistema inicia corretamente e exibe o menu

**Passos:**
1. Execute: `python main.py`
2. Aguarde o menu de configuração aparecer

**Resultado esperado:**
```
============================================================
⚙️  CONFIGURAÇÃO DO SISTEMA
============================================================
```

---

### Teste 2: Valores Padrão 📋

**Objetivo:** Verificar se os valores padrão são carregados corretamente

**Passos:**
1. Abra o arquivo `config.json`
2. Execute `python main.py`
3. Pressione Enter em ambos os prompts
4. Cancelar a execução com 'n'

**Resultado esperado:**
- Sistema exibe os valores que estão em `config.json`
- Os valores permanecem inalterados no arquivo

---

### Teste 3: Alteração de Ano 📅

**Objetivo:** Verificar se a alteração de ano funciona corretamente

**Passos:**
1. Na pergunta "Digite o ano (YYYY):", digite: `2022`
2. Pressione Enter para manter o tipo
3. Cancelar com 'n'

**Resultado esperado:**
- `config.json` contém `"year_download": "2022"`
- Próxima execução pergunta "Ano para extração (padrão: 2022)"

---

### Teste 4: Alteração de Tipo - DECISÃO 📄

**Objetivo:** Verificar se é possível selecionar DECISÃO

**Passos:**
1. Pressione Enter para manter o ano
2. Na pergunta de tipo, digite: `1`
3. Cancelar com 'n'

**Resultado esperado:**
- `config.json` contém `"tipo_documento": "DECISAO"`
- Mensagem exibe: ✅ Tipo configurado: DECISÃO

---

### Teste 5: Alteração de Tipo - ACÓRDÃO 📄

**Objetivo:** Verificar se é possível selecionar ACÓRDÃO

**Passos:**
1. Pressione Enter para manter o ano
2. Na pergunta de tipo, digite: `2`
3. Cancelar com 'n'

**Resultado esperado:**
- `config.json` contém `"tipo_documento": "ACORDAO"`
- Mensagem exibe: ✅ Tipo configurado: ACÓRDÃO

---

### Teste 6: Opção Inválida para Tipo 🚫

**Objetivo:** Verificar comportamento com entrada inválida

**Passos:**
1. Pressione Enter para manter o ano
2. Na pergunta de tipo, digite: `5` (valor inválido)
3. Cancelar com 'n'

**Resultado esperado:**
- Sistema mantém o tipo anterior
- Mensagem exibe: ✅ Tipo mantido: [valor anterior]
- `config.json` não é alterado

---

### Teste 7: Múltiplas Alterações 🔄

**Objetivo:** Verificar se múltiplas alterações são persistidas

**Passos:**
1. Alteração 1: Ano `2020`, Tipo `1` (DECISÃO)
2. Execução 2: Pressione Enter, Enter (mantém 2020, DECISÃO)
3. Modificar `config.json` manualmente para `2021`
4. Execução 3: Verifique se pergunta "Ano para extração (padrão: 2021)"

**Resultado esperado:**
- Cada alteração é salva em `config.json`
- Sistema respeita edições manuais do arquivo

---

### Teste 8: Timeout Automático ⏱️

**Objetivo:** Verificar se o timeout automático funciona

**Passos:**
1. Execute `python main.py`
2. Não digite nada e aguarde 3 segundos

**Resultado esperado:**
```
⏳ Sem confirmação em 3 segundos. Iniciando automaticamente...
```

---

### Teste 9: JSON Inválido 🔴

**Objetivo:** Verificar comportamento com JSON corrompido

**Passos:**
1. Abra `config.json`
2. Remova a última aspas de uma chave: `"year_download` (sem fechar)
3. Salve o arquivo
4. Execute `python main.py`

**Resultado esperado:**
- Sistema exibe warning: `⚠️ Erro ao carregar configuração`
- Sistema usa valores padrão automaticamente

---

### Teste 10: Criação Automática de config.json 📦

**Objetivo:** Verificar se config.json é criado automaticamente se deletado

**Passos:**
1. Delete `config.json`
2. Execute `python main.py`
3. Pressione Enter em ambos os prompts

**Resultado esperado:**
- Um novo `config.json` é criado com valores padrão
- Arquivo está formatado e válido como JSON

---

## 📊 Matriz de Testes

| Teste | Entrada | Resultado Esperado | Status |
|-------|---------|-------------------|--------|
| 1 | Start | Menu aparece | ⬜ |
| 2 | Enter + Enter | Mantém valores | ⬜ |
| 3 | "2022" + Enter | Ano alterado | ⬜ |
| 4 | Enter + "1" | Tipo = DECISÃO | ⬜ |
| 5 | Enter + "2" | Tipo = ACORDAO | ⬜ |
| 6 | Enter + "5" | Mantém tipo | ⬜ |
| 7 | Loop duplo | Config persiste | ⬜ |
| 8 | Wait 3s | Auto-inicia | ⬜ |
| 9 | JSON inválido | Usa padrão | ⬜ |
| 10 | Sem config.json | Cria automático | ⬜ |

## ✅ Checklist de Validação Final

- [ ] Menu de configuração aparece na inicialização
- [ ] Sistema pergunta sobre ano (com padrão exibido)
- [ ] Sistema pergunta sobre tipo de documento (com opções 1 e 2)
- [ ] Entrada vazia mantém valor padrão
- [ ] Entrada válida atualiza `config.json`
- [ ] Entrada inválida é ignorada (para tipo)
- [ ] Mensagens de confirmação aparecem em português
- [ ] Próxima execução reutiliza valores salvos
- [ ] Arquivo `config.json` está sempre em formato JSON válido
- [ ] Programa continua funcionando normalmente após configuração
- [ ] Não há erros de importação ou sintaxe
- [ ] Timeout automático funciona após 3 segundos

## 🐛 Problemas Conhecidos / Observações

1. **Encoding**: Se houver problemas com caracteres acentuados, verificar se o arquivo está em UTF-8
2. **Caminho de config.json**: Deve estar no mesmo diretório de `main.py`
3. **Permissões**: Certifique-se de que há permissão de leitura/escrita no diretório
4. **Python 3.6-**: Pode haver problemas com f-strings (requer Python 3.6+)

## 🔧 Debug / Troubleshooting

### Erro: "FileNotFoundError: utils module not found"
- **Causa**: Path incorreto ou arquivo não localizado
- **Solução**: Execute o script do diretório correto

### Erro: "JSON Decode Error"
- **Causa**: `config.json` com sintaxe JSON inválida
- **Solução**: Valide o JSON em um validador online ou delete e recrie

### Mensagem não aparece
- **Causa**: Encoding diferente ou terminal não suporta Unicode
- **Solução**: Tente executar com: `python -u main.py`

## 📝 Documentação Adicional

Para mais informações, consulte:
- `CONFIGURACAO.md` - Guia de uso do sistema
- `RESUMO_ALTERACOES.md` - Detalhes das mudanças técnicas
- `EXEMPLOS_EXECUCAO.md` - Exemplos de execução

