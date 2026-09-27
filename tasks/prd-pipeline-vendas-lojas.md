# PRD: Pipeline Vendas x Lojas (join, pivot e página web)

## Introdução

Este projeto transforma dois arquivos CSV brutos (`vendas.csv` e `lojas.csv`) em três entregáveis analíticos: uma tabela unificada de vendas com dados da loja, um pivot de receita mensal por região e uma página web estática com gráfico e conclusão. Todo o processamento é feito em Python com pandas. Os dados possuem duas anomalias conhecidas que precisam ser tratadas de forma explícita e auditável: 3 vendas que apontam para uma loja inexistente (id 999) e 1 loja cadastrada sem nenhuma venda (id 108, Batel).

O resultado será versionado em um repositório Git próprio, enviado para `https://github.com/GiovanniBrigido/ralph-lab`.

## Fatos conhecidos sobre os dados de entrada

- `vendas.csv`: 423 linhas, colunas `id_venda,data,id_loja,categoria,unidades,receita_brl`. Datas de 2026-01 a 2026-06.
- `lojas.csv`: 8 linhas, colunas `id_loja,nome_loja,regiao,uf,gerente`. Lojas 101 a 108.
- Vendas órfãs (sem loja correspondente): `V00421`, `V00422`, `V00423`, todas com `id_loja` = 999.
- Loja sem vendas: `108` (Batel, Sul, PR, gerente Heitor Braga).
- Regiões existentes: Centro-Oeste, Sudeste, Nordeste, Sul (4 regiões). A região Sul tem vendas apenas pela loja 107 (Moinhos).
- Resultado esperado do inner join: 420 linhas (423 - 3 órfãs).

## Valores de conferência (verificados contra os CSVs em 2026-09-27)

Estes valores foram fornecidos pelo solicitante e recalculados de forma independente com a biblioteca `csv` do Python. Os testes unitários devem usá-los como oráculo.

| Métrica | Valor esperado |
|---|---|
| Linhas do inner join | 420 |
| Vendas órfãs | 3 (`V00421`, `V00422`, `V00423`) |
| Lojas sem vendas | 1 (`108`) |
| Receita total do join (BRL) | 931274.06 |
| Região líder em receita acumulada | Sudeste, 265077.49 |
| Receita acumulada Nordeste | 261862.76 |
| Receita acumulada Centro-Oeste | 258323.97 |
| Receita acumulada Sul | 146009.84 |
| Mês de maior receita total | 2026-02, 169800.88 |
| Célula pivot Sul x 2026-03 (menor célula) | 19584.52 |
| Célula pivot Sudeste x 2026-06 (maior célula) | 48584.42 |

## Objetivos

- Produzir `vendas_lojas.csv` com exatamente 420 linhas via inner join por `id_loja`.
- Isolar as anomalias em `vendas_orfas.csv` (3 linhas) e `lojas_sem_vendas.csv` (1 linha) para auditoria.
- Produzir `pivot_receita.csv` com 4 linhas de dados e 7 colunas, formato numérico estrito.
- Produzir `index.html` estático, que abre direto do disco, com gráfico de barras agrupadas (Chart.js via CDN) e parágrafo de conclusão com 300 caracteres ou mais.
- Ter um único script reprodutível que gera todos os artefatos a partir dos CSVs fonte.
- Cobrir o pipeline com ao menos 4 testes unitários em pytest, usando os valores de conferência como oráculo.
- Publicar tudo no repositório `ralph-lab`.

## User Stories

### US-001: Inicializar repositório próprio e enviar para ralph-lab
**Descrição:** Como desenvolvedor, quero que esta pasta seja um repositório Git independente ligado ao `ralph-lab` para que os entregáveis fiquem versionados separadamente do repositório `Aula2`.

**Critérios de aceite:**
- [ ] `git init` executado dentro de `exercicio-ia-3.1` (a pasta deixa de ser rastreada pelo `Aula2` como conteúdo solto)
- [ ] Remote `origin` aponta para `https://github.com/GiovanniBrigido/ralph-lab.git`
- [ ] Existe `.gitignore` ignorando ao menos `__pycache__/`, `.venv/` e `*.pyc`
- [ ] Existe `requirements.txt` listando `pandas` e `pytest`
- [ ] Commit inicial contendo `vendas.csv`, `lojas.csv`, `prd.json`, `tasks/prd-pipeline-vendas-lojas.md`, `.gitignore` e `requirements.txt`
- [ ] `git push -u origin main` concluído com sucesso e os arquivos visíveis no GitHub

### US-002: Script de join com tratamento de anomalias
**Descrição:** Como analista, quero um script que una vendas e lojas por `id_loja` e separe as anomalias em arquivos próprios para que eu possa auditar o que ficou de fora.

**Critérios de aceite:**
- [ ] Existe `pipeline.py` na raiz, executável com `python pipeline.py`, que lê `vendas.csv` e `lojas.csv` com pandas
- [ ] Gera `vendas_lojas.csv` com inner join por `id_loja`, 420 linhas de dados, colunas na ordem: `id_venda,data,id_loja,categoria,unidades,receita_brl,nome_loja,regiao,uf,gerente`
- [ ] `vendas_lojas.csv` mantém a ordem original de `vendas.csv` (por `id_venda`)
- [ ] Gera `vendas_orfas.csv` com as 3 vendas cujo `id_loja` não existe em `lojas.csv`, mesmas colunas de `vendas.csv`; contém exatamente `V00421`, `V00422` e `V00423`
- [ ] Gera `lojas_sem_vendas.csv` com as lojas sem nenhuma venda, mesmas colunas de `lojas.csv`; contém exatamente a loja `108`
- [ ] Todos os CSVs são gravados com separador vírgula, codificação UTF-8, sem coluna de índice do pandas
- [ ] O script imprime no console um resumo com: total de vendas lidas, vendas unidas, vendas órfãs, lojas sem vendas
- [ ] `python -m py_compile pipeline.py` passa sem erro

### US-003: Pivot de receita mensal por região
**Descrição:** Como analista, quero uma tabela de receita por região e mês para comparar o desempenho regional ao longo do semestre.

**Critérios de aceite:**
- [ ] `pipeline.py` gera `pivot_receita.csv` a partir de `vendas_lojas.csv` (não diretamente de `vendas.csv`)
- [ ] Cabeçalho exato: `regiao,2026-01,2026-02,2026-03,2026-04,2026-05,2026-06`
- [ ] Exatamente 4 linhas de dados (Centro-Oeste, Nordeste, Sudeste, Sul) e 7 colunas
- [ ] Linhas ordenadas alfabeticamente por `regiao`
- [ ] Cada célula numérica é a soma de `receita_brl` da região no mês, formatada com ponto decimal e exatamente 2 casas (ex.: `24513.37`, `1200.00`)
- [ ] Nenhuma célula contém `R$`, espaço ou separador de milhar
- [ ] Nenhuma célula vazia ou `NaN` (todas as 4 regiões têm vendas em todos os 6 meses)
- [ ] Verificação: a soma de todas as 24 células é igual à soma de `receita_brl` em `vendas_lojas.csv` com tolerância de 0.01

### US-004: Página estática com gráfico de barras agrupadas
**Descrição:** Como gestor, quero abrir um arquivo HTML no navegador e ver a receita mensal por região em um gráfico, sem precisar rodar servidor.

**Critérios de aceite:**
- [ ] `pipeline.py` gera `index.html` na raiz, com os dados do pivot embutidos no HTML (sem `fetch` de arquivo externo)
- [ ] Usa Chart.js carregado via CDN (`https://cdn.jsdelivr.net/npm/chart.js`)
- [ ] Gráfico de barras agrupadas: eixo X com os 6 meses (`2026-01` a `2026-06`), uma barra por região em cada mês, uma cor distinta por região, legenda visível
- [ ] Título da página e do gráfico: "Receita mensal por região (jan a jun 2026)"
- [ ] Eixo Y rotulado em BRL; tooltip mostra o valor com 2 casas decimais
- [ ] Página tem `lang="pt-BR"`, `<meta charset="utf-8">` e é legível em largura de celular (sem rolagem horizontal)
- [ ] Abrir `index.html` por duplo clique (protocolo `file://`) renderiza o gráfico sem erros no console
- [ ] Verificar no navegador usando a skill dev-browser (ou captura de tela manual)

### US-005: Parágrafo de conclusão gerado a partir dos dados
**Descrição:** Como gestor, quero um parágrafo de conclusão abaixo do gráfico que resuma os destaques do semestre para não precisar interpretar os números sozinho.

**Critérios de aceite:**
- [ ] `index.html` contém um `<p id="conclusao">` logo abaixo do gráfico
- [ ] Texto em português com 300 caracteres ou mais (contados sem tags HTML)
- [ ] O texto cita ao menos: a região com maior receita acumulada, a região com menor receita acumulada, o mês de maior receita total e uma observação sobre a região Sul ter apenas uma loja ativa (Batel sem vendas)
- [ ] Os valores citados no texto são calculados pelo script a partir de `pivot_receita.csv`, não digitados à mão
- [ ] `pipeline.py` falha com mensagem clara (`SystemExit`) se o texto gerado tiver menos de 300 caracteres

### US-006: Testes unitários com valores de conferência
**Descrição:** Como desenvolvedor, quero testes automatizados que comparem a saída do pipeline com valores conhecidos para que qualquer regressão no join ou no pivot seja detectada imediatamente.

**Critérios de aceite:**
- [ ] `pipeline.py` expõe funções puras importáveis, no mínimo: `carregar_dados()`, `fazer_join(vendas, lojas)` retornando `(join, orfas, lojas_sem_vendas)`, `montar_pivot(join)` e `gerar_conclusao(pivot)`; a execução via `python pipeline.py` fica protegida por `if __name__ == "__main__":`
- [ ] Existe `tests/test_pipeline.py` executável com `python -m pytest -q` a partir da raiz, com no mínimo estes 6 testes:
  - `test_join_tem_420_linhas`: `len(join) == 420`
  - `test_orfas_e_lojas_sem_vendas`: ids das órfãs são exatamente `{"V00421", "V00422", "V00423"}` e `lojas_sem_vendas.id_loja` é exatamente `[108]`
  - `test_receita_total`: soma de `receita_brl` do join igual a `931274.06` com tolerância `abs=0.01`
  - `test_regiao_lider`: a região com maior soma no pivot é `Sudeste` com `265077.49` (tolerância `abs=0.01`)
  - `test_pivot_formato`: pivot tem 4 linhas, colunas exatamente `["regiao", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]`, e a célula `Sul x 2026-03` igual a `19584.52`
  - `test_conclusao_minimo_300`: `len(gerar_conclusao(pivot)) >= 300`
- [ ] Os testes rodam sobre os CSVs reais da raiz (`vendas.csv` e `lojas.csv`), sem fixtures sintéticas
- [ ] Um teste adicional lê `pivot_receita.csv` gravado em disco e confirma que todas as células numéricas casam com a regex `^\d+\.\d{2}$` (sem `R$`, sem vírgula, sem separador de milhar)
- [ ] `python -m pytest -q` termina com todos os testes passando e zero avisos de depreciação do pandas
- [ ] `python -m py_compile pipeline.py tests/test_pipeline.py` passa sem erro

### US-007: README e commit final
**Descrição:** Como avaliador, quero abrir o repositório `ralph-lab` e entender em um minuto o que foi feito e como reproduzir.

**Critérios de aceite:**
- [ ] `README.md` na raiz descreve: objetivo, como instalar (`pip install -r requirements.txt`), como rodar (`python pipeline.py`), como testar (`python -m pytest -q`), lista dos arquivos gerados, os valores de conferência e como as anomalias foram tratadas
- [ ] Todos os artefatos gerados (`vendas_lojas.csv`, `vendas_orfas.csv`, `lojas_sem_vendas.csv`, `pivot_receita.csv`, `index.html`) estão commitados
- [ ] Rodar `python pipeline.py` duas vezes seguidas produz arquivos idênticos (`git status` limpo após a segunda execução)
- [ ] Push final para `origin/main` concluído

## Requisitos Funcionais

- FR-1: O sistema deve ler `vendas.csv` e `lojas.csv` da raiz do repositório usando pandas, tratando `id_loja` como inteiro em ambos.
- FR-2: O sistema deve produzir `vendas_lojas.csv` por inner join em `id_loja`, preservando todas as colunas de `vendas.csv` seguidas de `nome_loja,regiao,uf,gerente`.
- FR-3: O sistema deve produzir `vendas_orfas.csv` contendo toda venda cujo `id_loja` não exista em `lojas.csv`.
- FR-4: O sistema deve produzir `lojas_sem_vendas.csv` contendo toda loja sem nenhuma venda em `vendas.csv`.
- FR-5: O sistema deve derivar a coluna de mês no formato `YYYY-MM` a partir de `data`.
- FR-6: O sistema deve produzir `pivot_receita.csv` com cabeçalho exato `regiao,2026-01,2026-02,2026-03,2026-04,2026-05,2026-06`, uma linha por região em ordem alfabética, valores como soma de `receita_brl`, com 2 casas decimais, ponto decimal, sem símbolo de moeda e sem separador de milhar.
- FR-7: O sistema deve produzir `index.html` estático com Chart.js via CDN, gráfico de barras agrupadas (meses no eixo X, uma série por região) e dados embutidos no próprio HTML.
- FR-8: O sistema deve gerar o parágrafo de conclusão (300 caracteres ou mais) a partir dos valores do pivot e inseri-lo em `index.html`.
- FR-9: O sistema deve imprimir no console um resumo das contagens (vendas lidas, unidas, órfãs, lojas sem vendas).
- FR-10: O sistema deve ser idempotente: execuções repetidas sobrescrevem os mesmos arquivos com conteúdo idêntico.
- FR-11: O repositório deve ser publicado em `https://github.com/GiovanniBrigido/ralph-lab` na branch `main`.
- FR-12: O sistema deve ter uma suíte pytest em `tests/test_pipeline.py` com no mínimo 4 testes (meta: 7) que validem, contra os CSVs reais, os valores de conferência: 420 linhas no join, receita total 931274.06, Sudeste líder com 265077.49, formato do pivot e tamanho mínimo da conclusão.
- FR-13: A lógica do pipeline deve estar em funções importáveis para permitir testes sem executar o script inteiro nem gravar arquivos.

## Não-objetivos (fora de escopo)

- Não fazer left join, outer join ou imputar dados para as vendas órfãs ou para a loja 108.
- Não corrigir ou inferir a loja correta das vendas com `id_loja` 999.
- Não criar banco de dados, API, servidor web ou build com Node.
- Não adicionar filtros interativos, seleção de período ou múltiplos gráficos na página.
- Não gerar pivot por categoria, por UF ou por loja (somente região x mês).
- Não usar LLM em tempo de execução para o parágrafo; o texto é montado por template a partir dos números.
- Não configurar GitHub Pages ou CI.

## Considerações de design

- Uma cor por região, com contraste suficiente entre as 4 séries; manter a mesma ordem de regiões na legenda e no pivot (alfabética).
- Layout em coluna única: título, gráfico em `<canvas>` responsivo, parágrafo de conclusão. Largura máxima de aproximadamente 960px centralizada, com margem lateral de 16px.
- Fonte do sistema (sem Google Fonts) para manter a página leve e funcional offline, exceto pelo CDN do Chart.js.

## Considerações técnicas

- Python 3.10 ou superior (ambiente atual: 3.12.10); dependências externas: `pandas` e `pytest`. Nenhuma das duas está instalada no ambiente hoje, então `pip install -r requirements.txt` é passo obrigatório antes de rodar.
- Comparações de valores monetários nos testes usam `pytest.approx(valor, abs=0.01)`; nunca igualdade exata de float.
- Formatação do pivot: usar `float_format="%.2f"` no `to_csv` ou formatar as colunas como string antes de gravar, garantindo que `1200` vire `1200.00`.
- Somar `receita_brl` como float e arredondar apenas na gravação, para que a verificação de soma total feche.
- Embutir o pivot em `index.html` como um objeto JSON dentro de uma tag `<script>`, gerado com `json.dumps` para evitar problemas de escape.
- O cálculo dos destaques da conclusão (maior/menor região, maior mês) deve usar os mesmos DataFrames do pivot para não divergir do gráfico.
- A pasta atual está dentro do repositório `Aula2` (aparece como `?? ./` no `git status` dele). Após o `git init` local, o `Aula2` passará a ver a pasta como repositório aninhado; isso é aceitável para o exercício.

## Métricas de sucesso

- `vendas_lojas.csv` tem 420 linhas de dados; `vendas_orfas.csv` tem 3; `lojas_sem_vendas.csv` tem 1.
- `pivot_receita.csv` tem exatamente 5 linhas no arquivo (1 cabeçalho + 4 dados) e 7 colunas em todas.
- Soma das 24 células do pivot igual à soma de `receita_brl` de `vendas_lojas.csv` (tolerância 0.01).
- `index.html` abre via `file://` e exibe 24 barras (6 meses x 4 regiões) sem erro no console.
- Parágrafo de conclusão com 300 caracteres ou mais.
- `python -m pytest -q` reporta ao menos 4 testes passando (meta: 7), com os valores de conferência confirmados: 420 linhas, 931274.06 de receita total e Sudeste líder com 265077.49.
- Repositório `ralph-lab` público com todos os artefatos na branch `main`.

## Questões em aberto

- O `.gitignore` deve ignorar os CSVs gerados ou eles devem ser commitados? Este PRD assume que são commitados (US-007), para que o avaliador veja o resultado sem rodar o script.
- Caso o CDN do Chart.js esteja indisponível, a página ficará sem gráfico. Aceitável para este exercício, ou vale embutir o Chart.js localmente em uma iteração futura?
