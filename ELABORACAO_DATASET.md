### Elaboração do Dataset

O presente estudo utiliza um dataset construído a partir de dados públicos disponibilizados pelo Superior Tribunal de Justiça (STJ) em seu portal de Dados Abertos. Para a coleta, tratamento e estruturação desses dados, foi desenvolvido um sistema computacional em Python, cujo fluxo de trabalho automatizado garante a criação de um conjunto de dados coeso, filtrado e formatado para análise. O processo metodológico de elaboração do dataset foi dividido em quatro etapas principais: aquisição dos dados brutos, processamento e filtragem dos metadados, extração e estruturação do conteúdo textual, e montagem do dataset final.

**1. Aquisição dos Dados Brutos**

A primeira etapa consistiu na aquisição automatizada dos arquivos de origem. O sistema foi programado para acessar o portal de dados abertos do STJ e realizar o download de dois tipos de arquivos, referentes a um ano e, opcionalmente, a um mês específico, ambos configuráveis:

*   **Arquivos de Metadados:** Arquivos em formato JSON (`metadadosYYYYMMDD.json`) contendo informações de registro sobre cada decisão ou acórdão, como número do processo, data de publicação, ministro relator, tipo de documento, entre outros.
*   **Arquivos de Íntegras:** Arquivos compactados em formato ZIP (`YYYYMMDD.zip`) que agregam os documentos textuais (`.txt`) com a íntegra de cada decisão e acórdão.

Para otimizar o processo, o sistema verifica a existência prévia dos arquivos no diretório local, evitando downloads redundantes e permitindo a retomada do processo em caso de interrupção.

**2. Processamento e Filtragem dos Metadados**

Após o download, os arquivos JSON de metadados foram processados para criar uma base de dados preliminar. Nesta fase, foi aplicada uma série de filtros para selecionar apenas os registros pertinentes aos objetivos da pesquisa:

*   **Filtragem por Tipo de Documento:** Foram selecionados apenas os registros classificados como "ACÓRDÃO" ou "DECISÃO", conforme o escopo definido.
*   **Filtragem por Classe Processual:** O sistema filtrou os documentos com base em uma classe processual específica (e.g., *Habeas Corpus* - HC), garantindo que o dataset final contivesse apenas os tipos de processos de interesse.
*   **Filtragem por Data de Recebimento:** Foi estabelecida uma data de corte (e.g., 01/01/2021) para o campo `DATARECEBIMENTO`, assegurando que apenas os processos mais recentes fossem incluídos na análise.

Os registros que atenderam a todos os critérios foram consolidados em um arquivo CSV intermediário. Durante este processo, os dados passaram por uma etapa de limpeza e normalização, incluindo a conversão de timestamps para formatos de data padronizados (DD/MM/AAAA) e a remoção de quebras de linha e outros caracteres indesejados. O identificador único de cada documento, `SEQDOCUMENTO`, foi preservado como chave primária para a etapa seguinte.

**3. Extração e Estruturação do Conteúdo Textual**

A terceira etapa focou na extração do conteúdo textual dos documentos. Utilizando o arquivo CSV de metadados filtrados como guia, o sistema iterou sobre cada `SEQDOCUMENTO` selecionado. Para cada identificador, o respectivo arquivo `.txt` foi localizado e lido diretamente de dentro dos arquivos ZIP previamente baixados, um método que dispensa a descompressão total dos arquivos em disco, otimizando o uso de armazenamento e o tempo de processamento.

O conteúdo de cada arquivo de texto foi então submetido a um processo de *parsing* (análise sintática) baseado em expressões regulares. Esta análise foi projetada para identificar e extrair seções jurídicas específicas do corpo do texto, segmentando o documento nas seguintes partes estruturadas:

*   **Acórdão:** O corpo principal do acórdão.
*   **Ementa:** O resumo estruturado da decisão.
*   **Relatório:** A seção que descreve o histórico e o contexto do processo.
*   **Voto:** A fundamentação e a argumentação do ministro relator.
*   **Decisão:** O texto da decisão monocrática, quando aplicável.

A lógica de *parsing* foi desenvolvida para lidar com as variações de formatação encontradas nos documentos do STJ, garantindo uma extração robusta e precisa das seções de interesse.

**4. Montagem do Dataset Final**

Finalmente, as seções textuais extraídas foram consolidadas em um novo arquivo CSV, constituindo o dataset final da pesquisa. Cada linha deste arquivo corresponde a um documento judicial e contém o `SEQDOCUMENTO` como identificador, seguido pelas colunas `ACORDAO`, `EMENTA`, `RELATORIO`, `VOTO` e `DECISAO`, cada uma preenchida com o texto extraído na etapa anterior.

Este processo metodológico resultou em um dataset estruturado, limpo e focado, pronto para ser utilizado nas etapas subsequentes de análise de dados e modelagem.
