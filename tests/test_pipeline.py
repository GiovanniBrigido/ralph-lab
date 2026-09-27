"""Testes do pipeline Vendas x Lojas.

Rodam sobre os CSVs reais da raiz (vendas.csv e lojas.csv) e usam os valores
de conferencia do PRD como oraculo. Execute com: python -m pytest -q
"""
import csv
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import pipeline  # noqa: E402

MESES = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]


@pytest.fixture(scope="module")
def dados():
    vendas, lojas = pipeline.carregar_dados(RAIZ)
    join, orfas, sem_vendas = pipeline.fazer_join(vendas, lojas)
    return join, orfas, sem_vendas


@pytest.fixture(scope="module")
def pivot(dados):
    join, _, _ = dados
    return pipeline.montar_pivot(join)


def test_join_tem_420_linhas(dados):
    join, _, _ = dados
    assert len(join) == 420


def test_orfas_e_lojas_sem_vendas(dados):
    _, orfas, sem_vendas = dados
    assert set(orfas["id_venda"]) == {"V00421", "V00422", "V00423"}
    assert sem_vendas["id_loja"].tolist() == [108]


def test_receita_total(dados):
    join, _, _ = dados
    assert join["receita_brl"].sum() == pytest.approx(931274.06, abs=0.01)


def test_regiao_lider(pivot):
    por_regiao = pivot.set_index("regiao")[MESES].sum(axis=1)
    assert por_regiao.idxmax() == "Sudeste"
    assert por_regiao["Sudeste"] == pytest.approx(265077.49, abs=0.01)


def test_pivot_formato(pivot):
    assert len(pivot) == 4
    assert pivot.columns.tolist() == ["regiao"] + MESES
    assert pivot["regiao"].tolist() == ["Centro-Oeste", "Nordeste", "Sudeste", "Sul"]
    sul_marco = pivot.loc[pivot["regiao"] == "Sul", "2026-03"].iloc[0]
    assert sul_marco == pytest.approx(19584.52, abs=0.01)


def test_conclusao_minimo_300(pivot):
    texto = pipeline.gerar_conclusao(pivot)
    assert len(texto) >= 300
    assert "Sudeste" in texto and "Sul" in texto and "2026-02" in texto


def test_pivot_csv_formato_numerico(tmp_path):
    pipeline_csv = RAIZ / "pivot_receita.csv"
    if not pipeline_csv.exists():
        pytest.skip("pivot_receita.csv ainda nao foi gerado; rode python pipeline.py")
    with open(pipeline_csv, encoding="utf-8", newline="") as f:
        linhas = list(csv.reader(f))
    assert linhas[0] == ["regiao"] + MESES
    assert len(linhas) == 5
    padrao = re.compile(r"^\d+\.\d{2}$")
    for linha in linhas[1:]:
        assert len(linha) == 7
        for celula in linha[1:]:
            assert padrao.match(celula), f"celula fora do formato: {celula!r}"
