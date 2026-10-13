
"""Previsão experimental de glosas — versão 2.
Dados sintéticos. Não altera o SQL Server.
"""

from pathlib import Path

import pandas as pd
import pyodbc

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

SERVIDOR = "PC03"
BANCO = "Projeto_Faturamento_Medico"

SQL = """
SELECT
    'Unimed' AS operadora,
    numero_guia_prestador AS numero_guia,
    codigo_tuss,
    tipo_guia,
    quantidade_apresentada AS quantidade,
    valor_apresentado,
    data_atendimento,
    data_envio_lote,
    senha_autorizacao,
    valor_glosado
FROM v2.faturamento_unimed

UNION ALL

SELECT
    'Bradesco' AS operadora,
    numero_guia_prestador AS numero_guia,
    codigo_tuss,
    tipo_guia,
    quantidade,
    valor_total_apresentado AS valor_apresentado,
    data_atendimento,
    data_envio_lote,
    senha_autorizacao,
    valor_glosado
FROM v2.faturamento_bradesco
"""


def carregar_dados():
    drivers = [
        d for d in pyodbc.drivers()
        if d.startswith("ODBC Driver") and "SQL Server" in d
    ]
    if not drivers:
        raise RuntimeError("Driver ODBC do SQL Server não encontrado.")

    conexao = pyodbc.connect(
        f"DRIVER={{{drivers[-1]}}};"
        f"SERVER={SERVIDOR};"
        f"DATABASE={BANCO};"
        "Trusted_Connection=yes;"
        "Encrypt=yes;TrustServerCertificate=yes;"
    )

    try:
        cursor = conexao.cursor()
        cursor.execute(SQL)
        colunas = [c[0] for c in cursor.description]
        return pd.DataFrame.from_records(
            cursor.fetchall(), columns=colunas
        )
    finally:
        conexao.close()


def main():
    df = carregar_dados()

    for coluna in ["data_atendimento", "data_envio_lote"]:
        df[coluna] = pd.to_datetime(df[coluna], errors="coerce")

    for coluna in ["valor_apresentado", "valor_glosado", "quantidade"]:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    if df["valor_glosado"].isna().any():
        raise ValueError("Existem valores de glosa ausentes.")

    if df["data_atendimento"].isna().any():
        raise ValueError("Existem datas de atendimento ausentes.")

    df["teve_glosa"] = (df["valor_glosado"] > 0).astype(int)
    df["mes"] = df["data_atendimento"].dt.month
    df["dia_semana"] = df["data_atendimento"].dt.dayofweek
    df["dias_ate_envio"] = (
        df["data_envio_lote"] - df["data_atendimento"]
    ).dt.days

    df["possui_autorizacao"] = (
        df["senha_autorizacao"]
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
        .astype(int)
    )

    categoricas = ["operadora", "codigo_tuss", "tipo_guia"]
    numericas = [
        "quantidade",
        "valor_apresentado",
        "mes",
        "dia_semana",
        "dias_ate_envio",
        "possui_autorizacao",
    ]
    colunas = categoricas + numericas

    for coluna in categoricas:
        df[coluna] = df[coluna].fillna("Desconhecido").astype(str)

    # Guias repetidas ficam juntas; a divisão é cronológica.
    df["chave_guia"] = (
        df["operadora"] + "|" +
        df["numero_guia"].fillna("SEM_GUIA").astype(str)
    )

    df = df.sort_values("data_atendimento").reset_index(drop=True)

    # Divide por data, evitando misturar o mesmo dia nos dois grupos.
    datas = df["data_atendimento"].drop_duplicates().sort_values()
    if len(datas) < 5:
        raise ValueError("Poucas datas distintas para separar treino e teste.")

    data_corte = datas.iloc[int(len(datas) * 0.8)]
    treino = df[df["data_atendimento"] < data_corte].copy()
    teste = df[df["data_atendimento"] >= data_corte].copy()

    # Evita usar no teste guias que já apareceram no treinamento.
    guias_treino = set(treino["chave_guia"])
    teste = teste[~teste["chave_guia"].isin(guias_treino)].copy()

    if treino.empty or teste.empty:
        raise ValueError("Treino ou teste ficou vazio.")

    X_treino, y_treino = treino[colunas], treino["teve_glosa"]
    X_teste, y_teste = teste[colunas], teste["teve_glosa"]

    if y_treino.nunique() != 2 or y_teste.nunique() != 2:
        raise ValueError("Treino e teste precisam conter as duas classes.")

    preparacao = ColumnTransformer([
        (
            "categoricas",
            OneHotEncoder(handle_unknown="ignore"),
            categoricas,
        ),
        (
            "numericas",
            SimpleImputer(strategy="median"),
            numericas,
        ),
    ])

    modelo = Pipeline([
        ("preparacao", preparacao),
        ("classificador", RandomForestClassifier(
            n_estimators=200,
            max_depth=5,
            min_samples_leaf=10,
            class_weight="balanced",
            random_state=42,
        )),
    ])

    referencia = DummyClassifier(strategy="prior")

    referencia.fit(X_treino, y_treino)
    modelo.fit(X_treino, y_treino)

    print(f"Registros totais: {len(df)}")
    print(f"Treinamento: {len(treino)}")
    print(f"Teste: {len(teste)}")
    print(f"Glosas no treino: {y_treino.sum()}")
    print(f"Glosas no teste: {y_teste.sum()}")
    print(f"Data de corte: {data_corte.date()}")

    for nome, estimador in [
        ("Referência simples", referencia),
        ("Random Forest V2", modelo),
    ]:
        previsoes = estimador.predict(X_teste)
        probabilidades = estimador.predict_proba(X_teste)[:, 1]

        print(f"\n--- {nome} ---")
        print(classification_report(
            y_teste,
            previsoes,
            labels=[0, 1],
            target_names=["Sem glosa", "Com glosa"],
            zero_division=0,
        ))
        print("Matriz de confusão:")
        print(confusion_matrix(y_teste, previsoes, labels=[0, 1]))
        print(
            "Average Precision:",
            round(average_precision_score(y_teste, probabilidades), 4),
        )


    # Exporta somente previsoes fora do treinamento, para demonstracao no Power BI.
    # As probabilidades sao experimentais e nao estao calibradas.
    saida = teste[["operadora", "numero_guia", "codigo_tuss", "tipo_guia",
                   "data_atendimento", "valor_apresentado", "valor_glosado"]].copy()
    saida["glosa_real"] = y_teste.to_numpy()
    saida["probabilidade_glosa"] = modelo.predict_proba(X_teste)[:, 1]
    saida["previsao_glosa"] = modelo.predict(X_teste)
    saida["tipo_avaliacao"] = "Teste cronologico - dados sinteticos"
    destino = Path(__file__).resolve().parent.parent / "data" / "processed"
    destino.mkdir(parents=True, exist_ok=True)
    arquivo = destino / "previsoes_glosas_teste.csv"
    saida.to_csv(arquivo, index=False, sep=";", encoding="utf-8-sig",
                decimal=",", date_format="%Y-%m-%d")
    print(f"\nPrevisoes exportadas: {len(saida)} registros")
    print(f"Arquivo: {arquivo}")


if __name__ == "__main__":
    main()
