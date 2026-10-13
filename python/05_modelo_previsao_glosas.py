
"""Protótipo de previsão de glosas com dados simulados."""

import pandas as pd
import pyodbc

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    average_precision_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

SERVIDOR = "PC03"
BANCO = "Projeto_Faturamento_Medico"

SQL = """
SELECT
    operadora,
    data_atendimento,
    valor_apresentado,
    valor_glosado
FROM v2.vw_faturamento_consolidado
WHERE operadora IN ('Unimed', 'Bradesco')
  AND data_atendimento IS NOT NULL
"""

def carregar_dados():
    drivers = pyodbc.drivers()
    disponiveis = [
        d for d in drivers if d.startswith("ODBC Driver") and "SQL Server" in d
    ]
    if not disponiveis:
        raise RuntimeError("Driver ODBC do SQL Server não encontrado.")

    driver = disponiveis[-1]
    conexao = pyodbc.connect(
        f"DRIVER={{{driver}}};"
        f"SERVER={SERVIDOR};DATABASE={BANCO};"
        "Trusted_Connection=yes;"
        "Encrypt=yes;TrustServerCertificate=yes;"
    )
    try:
        cursor = conexao.cursor()
        cursor.execute(SQL)
        colunas = [col[0] for col in cursor.description]
        return pd.DataFrame.from_records(cursor.fetchall(), columns=colunas)
    finally:
        conexao.close()


def main():
    df = carregar_dados()

    df["data_atendimento"] = pd.to_datetime(df["data_atendimento"])
    df["valor_apresentado"] = pd.to_numeric(
        df["valor_apresentado"], errors="coerce"
    )
    df["valor_glosado"] = pd.to_numeric(
        df["valor_glosado"], errors="coerce"
    )

    if df["valor_glosado"].isna().any():
        raise ValueError("Existem glosas sem informação de valor.")

    df["teve_glosa"] = (df["valor_glosado"] > 0).astype(int)
    df["mes"] = df["data_atendimento"].dt.month
    df["dia_semana"] = df["data_atendimento"].dt.dayofweek

    df = df.sort_values("data_atendimento").reset_index(drop=True)

    # Separação cronológica: 80% treino, 20% teste.
    corte = int(len(df) * 0.8)
    treino = df.iloc[:corte].copy()
    teste = df.iloc[corte:].copy()

    colunas = ["operadora", "valor_apresentado", "mes", "dia_semana"]
    X_treino, y_treino = treino[colunas], treino["teve_glosa"]
    X_teste, y_teste = teste[colunas], teste["teve_glosa"]

    if y_treino.nunique() < 2:
        raise ValueError("O conjunto de treino precisa ter as duas classes.")

    preparacao = ColumnTransformer(
        transformers=[
            (
                "operadora",
                OneHotEncoder(handle_unknown="ignore"),
                ["operadora"],
            ),
            (
                "numericas",
                SimpleImputer(strategy="median"),
                ["valor_apresentado", "mes", "dia_semana"],
            ),
        ]
    )

    modelo = Pipeline(
        steps=[
            ("preparacao", preparacao),
            (
                "classificador",
                RandomForestClassifier(
                    n_estimators=200,
                    max_depth=5,
                    min_samples_leaf=10,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )

    referencia = DummyClassifier(strategy="prior")
    referencia.fit(X_treino, y_treino)
    modelo.fit(X_treino, y_treino)

    print(f"Registros totais: {len(df)}")
    print(f"Treinamento: {len(treino)}")
    print(f"Teste: {len(teste)}")
    print(f"Glosas no treino: {y_treino.sum()}")
    print(f"Glosas no teste: {y_teste.sum()}")

    for nome, estimador in [
        ("Referência simples", referencia),
        ("Random Forest", modelo),
    ]:
        previsoes = estimador.predict(X_teste)
        probabilidades = estimador.predict_proba(X_teste)[:, 1]

        print(f"\n--- {nome} ---")
        print(
            classification_report(
                y_teste,
                previsoes,
                labels=[0, 1],
                target_names=["Sem glosa", "Com glosa"],
                zero_division=0,
            )
        )
        print("Matriz de confusão:")
        print(confusion_matrix(y_teste, previsoes, labels=[0, 1]))
        if y_teste.sum() > 0:
            print(
                "Average Precision:",
                round(average_precision_score(y_teste, probabilidades), 4),
            )


if __name__ == "__main__":
    main()
