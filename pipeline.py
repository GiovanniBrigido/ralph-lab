"""Pipeline Vendas x Lojas.

Le vendas.csv e lojas.csv, faz o inner join por id_loja, isola as anomalias
(vendas orfas e lojas sem vendas), monta o pivot de receita mensal por regiao
e gera a pagina estatica index.html com grafico e paragrafo de conclusao.

Uso: python pipeline.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

MESES = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]
COLUNAS_JOIN = [
    "id_venda", "data", "id_loja", "categoria", "unidades", "receita_brl",
    "nome_loja", "regiao", "uf", "gerente",
]
TITULO = "Receita mensal por região (jan a jun 2026)"
MIN_CONCLUSAO = 300
CORES = {
    "Centro-Oeste": "#2563eb",
    "Nordeste": "#d97706",
    "Sudeste": "#059669",
    "Sul": "#dc2626",
}


# ---------------------------------------------------------------------------
# Carga e join
# ---------------------------------------------------------------------------
def carregar_dados(base: Path = BASE_DIR) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Le vendas.csv e lojas.csv, com id_loja como inteiro em ambos."""
    vendas = pd.read_csv(base / "vendas.csv", dtype={"id_loja": "int64"})
    lojas = pd.read_csv(base / "lojas.csv", dtype={"id_loja": "int64"})
    return vendas, lojas


def fazer_join(
    vendas: pd.DataFrame, lojas: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Inner join por id_loja.

    Retorna (join, vendas_orfas, lojas_sem_vendas).
    - join: todas as colunas de vendas seguidas de nome_loja, regiao, uf, gerente,
      na ordem original de vendas (por id_venda).
    - vendas_orfas: vendas cujo id_loja nao existe em lojas.
    - lojas_sem_vendas: lojas sem nenhuma venda.
    """
    join = vendas.merge(lojas, on="id_loja", how="inner")
    join = join[COLUNAS_JOIN].sort_values("id_venda", kind="stable").reset_index(drop=True)

    orfas = vendas[~vendas["id_loja"].isin(lojas["id_loja"])].reset_index(drop=True)
    sem_vendas = lojas[~lojas["id_loja"].isin(vendas["id_loja"])].reset_index(drop=True)
    return join, orfas, sem_vendas


# ---------------------------------------------------------------------------
# Pivot
# ---------------------------------------------------------------------------
def montar_pivot(join: pd.DataFrame) -> pd.DataFrame:
    """Receita por regiao (linhas) x mes YYYY-MM (colunas), ordem alfabetica.

    Retorna um DataFrame com a coluna 'regiao' seguida das 6 colunas de mes.
    """
    df = join[["regiao", "data", "receita_brl"]].copy()
    df["mes"] = df["data"].astype(str).str.slice(0, 7)
    pivot = (
        df.pivot_table(index="regiao", columns="mes", values="receita_brl", aggfunc="sum")
        .reindex(columns=MESES)
        .sort_index()
    )
    if pivot.isna().any().any():
        raise SystemExit("pivot contem celulas vazias; verifique os dados de entrada")
    pivot.columns.name = None
    return pivot.reset_index()


def _fmt_brl(valor: float) -> str:
    """Formata um numero no padrao brasileiro para uso em texto: R$ 1.234,56."""
    s = f"{valor:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------------------
# Conclusao
# ---------------------------------------------------------------------------
def gerar_conclusao(pivot: pd.DataFrame) -> str:
    """Monta o paragrafo de conclusao a partir dos numeros do pivot."""
    tabela = pivot.set_index("regiao")[MESES]
    por_regiao = tabela.sum(axis=1)
    por_mes = tabela.sum(axis=0)

    lider = por_regiao.idxmax()
    lanterna = por_regiao.idxmin()
    mes_top = por_mes.idxmax()
    mes_min = por_mes.idxmin()
    total = por_regiao.sum()
    n_regioes = len(por_regiao)

    intermediarias = list(por_regiao.sort_values(ascending=False).index[1:-1])
    seguidas = " e ".join(intermediarias) if len(intermediarias) <= 2 else (
        ", ".join(intermediarias[:-1]) + " e " + intermediarias[-1]
    )

    texto = (
        f"No primeiro semestre de 2026 as {n_regioes} regiões somaram {_fmt_brl(total)} "
        f"em receita. A região {lider} liderou o acumulado com {_fmt_brl(por_regiao[lider])}, "
        f"seguida de perto por {seguidas}, "
        f"o que mostra um grupo de três regiões com desempenho muito próximo. "
        f"A região {lanterna} ficou em último lugar com {_fmt_brl(por_regiao[lanterna])}, "
        f"cerca de {por_regiao[lanterna] / por_regiao[lider]:.0%} do valor da líder. "
        f"Isso se explica em parte pela cobertura: a região Sul tem apenas uma loja ativa "
        f"(Moinhos), pois a loja Batel está cadastrada mas não registrou nenhuma venda no período. "
        f"O mês de maior receita total foi {mes_top}, com {_fmt_brl(por_mes[mes_top])}, "
        f"enquanto {mes_min} foi o mais fraco, com {_fmt_brl(por_mes[mes_min])}."
    )
    return texto


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------
def gerar_html(pivot: pd.DataFrame, conclusao: str) -> str:
    """Pagina estatica com grafico de barras agrupadas (Chart.js via CDN)."""
    regioes = pivot["regiao"].tolist()
    dados = {
        "meses": MESES,
        "series": [
            {
                "regiao": r,
                "cor": CORES.get(r, "#6b7280"),
                "valores": [round(float(v), 2) for v in pivot.loc[pivot["regiao"] == r, MESES].iloc[0]],
            }
            for r in regioes
        ],
    }
    dados_json = json.dumps(dados, ensure_ascii=False, sort_keys=True)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITULO}</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 24px 16px;
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    line-height: 1.5;
    background: Canvas;
    color: CanvasText;
  }}
  main {{ max-width: 960px; margin: 0 auto; }}
  h1 {{ font-size: 1.5rem; margin: 0 0 16px; }}
  .grafico {{ position: relative; width: 100%; height: 420px; }}
  @media (max-width: 600px) {{ .grafico {{ height: 320px; }} }}
  #conclusao {{ margin-top: 24px; font-size: 1rem; }}
  footer {{ margin-top: 24px; font-size: 0.85rem; opacity: 0.7; }}
</style>
</head>
<body>
<main>
  <h1>{TITULO}</h1>
  <div class="grafico"><canvas id="chart" aria-label="{TITULO}" role="img"></canvas></div>
  <p id="conclusao">{conclusao}</p>
  <footer>Fonte: vendas_lojas.csv (inner join de vendas.csv e lojas.csv). Valores em reais (BRL).</footer>
</main>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
  const DADOS = {dados_json};
  const fmt = (v) => v.toLocaleString("pt-BR", {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
  new Chart(document.getElementById("chart"), {{
    type: "bar",
    data: {{
      labels: DADOS.meses,
      datasets: DADOS.series.map((s) => ({{
        label: s.regiao,
        data: s.valores,
        backgroundColor: s.cor,
        borderRadius: 3,
      }})),
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        title: {{ display: true, text: {json.dumps(TITULO, ensure_ascii=False)} }},
        legend: {{ position: "top" }},
        tooltip: {{
          callbacks: {{
            label: (ctx) => `${{ctx.dataset.label}}: R$ ${{fmt(ctx.parsed.y)}}`,
          }},
        }},
      }},
      scales: {{
        x: {{ title: {{ display: true, text: "Mês" }} }},
        y: {{
          beginAtZero: true,
          title: {{ display: true, text: "Receita (BRL)" }},
          ticks: {{ callback: (v) => "R$ " + fmt(v) }},
        }},
      }},
    }},
  }});
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Execucao
# ---------------------------------------------------------------------------
def main(base: Path = BASE_DIR) -> None:
    vendas, lojas = carregar_dados(base)
    join, orfas, sem_vendas = fazer_join(vendas, lojas)

    join.to_csv(base / "vendas_lojas.csv", index=False, encoding="utf-8", lineterminator="\n")
    orfas.to_csv(base / "vendas_orfas.csv", index=False, encoding="utf-8", lineterminator="\n")
    sem_vendas.to_csv(base / "lojas_sem_vendas.csv", index=False, encoding="utf-8", lineterminator="\n")

    # O pivot e derivado do arquivo gravado, garantindo que reflita vendas_lojas.csv.
    join_gravado = pd.read_csv(base / "vendas_lojas.csv", dtype={"id_loja": "int64"})
    pivot = montar_pivot(join_gravado)
    pivot.to_csv(
        base / "pivot_receita.csv", index=False, encoding="utf-8",
        float_format="%.2f", lineterminator="\n",
    )

    conclusao = gerar_conclusao(pivot)
    if len(conclusao) < MIN_CONCLUSAO:
        raise SystemExit(
            f"conclusao com {len(conclusao)} caracteres; minimo exigido e {MIN_CONCLUSAO}"
        )
    (base / "index.html").write_text(gerar_html(pivot, conclusao), encoding="utf-8", newline="\n")

    print("Resumo do pipeline")
    print(f"  vendas lidas      : {len(vendas)}")
    print(f"  vendas unidas     : {len(join)}")
    print(f"  vendas orfas      : {len(orfas)}  {orfas['id_venda'].tolist()}")
    print(f"  lojas sem vendas  : {len(sem_vendas)}  {sem_vendas['id_loja'].tolist()}")
    print(f"  receita total     : {join['receita_brl'].sum():.2f}")
    print(f"  conclusao         : {len(conclusao)} caracteres")
    print("Arquivos gerados: vendas_lojas.csv, vendas_orfas.csv, lojas_sem_vendas.csv, "
          "pivot_receita.csv, index.html")


if __name__ == "__main__":
    sys.exit(main())
