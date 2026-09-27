# ralph-lab: pipeline Vendas x Lojas

Exercício de engenharia de dados executado com o fluxo Ralph (PRD em `tasks/`, stories em `prd.json`).
A partir de `vendas.csv` e `lojas.csv`, o script `pipeline.py` produz a tabela unificada de vendas,
isola as anomalias, monta o pivot de receita mensal por região e gera uma página estática com gráfico
e parágrafo de conclusão.

## Como rodar

```bash
pip install -r requirements.txt
python pipeline.py
python -m pytest -q
```

O script imprime um resumo com as contagens e regrava todos os artefatos. Ele é idempotente: rodar
duas vezes produz arquivos idênticos. Abra `index.html` com duplo clique para ver o gráfico (precisa
de internet para carregar o Chart.js via CDN).

## Arquivos

| Arquivo | Origem | Conteúdo |
|---|---|---|
| `vendas.csv` | fonte | 423 vendas, jan a jun 2026 |
| `lojas.csv` | fonte | 8 lojas (101 a 108) |
| `pipeline.py` | código | join, pivot, conclusão e HTML em funções importáveis |
| `tests/test_pipeline.py` | código | 7 testes pytest sobre os CSVs reais |
| `vendas_lojas.csv` | gerado | inner join por `id_loja`, 420 linhas |
| `vendas_orfas.csv` | gerado | 3 vendas cuja loja não existe |
| `lojas_sem_vendas.csv` | gerado | 1 loja sem nenhuma venda |
| `pivot_receita.csv` | gerado | receita por região (4 linhas) x mês (6 colunas) |
| `index.html` | gerado | gráfico de barras agrupadas e conclusão |
| `tasks/prd-pipeline-vendas-lojas.md` | planejamento | PRD completo, gerado com a skill `/prd` |
| `scripts/ralph/prd.json` | planejamento | stories no formato Ralph, gerado com a skill `/ralph` |
| `scripts/ralph/ralph.sh` | Ralph | loop autônomo que executa as stories com `claude` ou `amp` |
| `scripts/ralph/CLAUDE.md` | Ralph | prompt de cada iteração para o Claude Code |
| `scripts/ralph/progress.txt` | Ralph | log de progresso escrito pelo agente a cada iteração |
| `.claude/skills/prd/`, `.claude/skills/ralph/` | Ralph | skills `/prd` e `/ralph` disponíveis no ambiente do agente |
| `ralph-run.log` | Ralph | saída da execução `scripts/ralph/ralph.sh --tool claude 1` |

## Fluxo Ralph

1. `/prd` gerou o PRD em `tasks/` a partir da descrição do exercício e de 5 perguntas de esclarecimento.
2. `/ralph` converteu o PRD em `scripts/ralph/prd.json` com 7 stories ordenadas por dependência.
3. As stories foram executadas em ordem de prioridade e marcadas com `passes: true`.
4. `scripts/ralph/ralph.sh --tool claude 1` rodou uma iteração de verificação, registrada em `ralph-run.log`,
   e encerrou com `<promise>COMPLETE</promise>`.

Para rodar o loop de novo:

```bash
bash scripts/ralph/ralph.sh --tool claude 10 2>&1 | tee ralph-run.log
```

## Tratamento das anomalias

O join é estritamente interno. Nada é imputado nem corrigido.

- **Vendas órfãs.** `V00421`, `V00422` e `V00423` apontam para a loja `999`, que não existe em
  `lojas.csv`. Elas ficam fora de `vendas_lojas.csv` e são gravadas em `vendas_orfas.csv` para auditoria.
- **Loja sem vendas.** A loja `108` (Batel, Sul, PR) está cadastrada mas não tem nenhuma venda no
  período. Ela fica fora do join e é gravada em `lojas_sem_vendas.csv`. Por isso a região Sul aparece
  com apenas uma loja ativa no gráfico.

## Formato do pivot

`pivot_receita.csv` tem o cabeçalho exato `regiao,2026-01,2026-02,2026-03,2026-04,2026-05,2026-06`,
4 linhas de dados em ordem alfabética e valores com ponto decimal, 2 casas, sem `R$` e sem separador
de milhar.

## Valores de conferência

Os testes usam estes valores como oráculo. Foram fornecidos com o exercício e recalculados de forma
independente com a biblioteca `csv` do Python.

| Métrica | Valor |
|---|---|
| Linhas do inner join | 420 |
| Vendas órfãs | 3 |
| Lojas sem vendas | 1 |
| Receita total (BRL) | 931274.06 |
| Região líder | Sudeste, 265077.49 |
| Nordeste | 261862.76 |
| Centro-Oeste | 258323.97 |
| Sul | 146009.84 |
| Mês de maior receita | 2026-02, 169800.88 |
| Menor célula do pivot | Sul x 2026-03, 19584.52 |
| Maior célula do pivot | Sudeste x 2026-06, 48584.42 |

## Testes

```
test_join_tem_420_linhas
test_orfas_e_lojas_sem_vendas
test_receita_total
test_regiao_lider
test_pivot_formato
test_conclusao_minimo_300
test_pivot_csv_formato_numerico
```

Comparações monetárias usam `pytest.approx(valor, abs=0.01)`.
