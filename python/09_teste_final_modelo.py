
import importlib.util
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline

caminho = Path(__file__).with_name("06_modelo_previsao_glosas_v2.py")
spec = importlib.util.spec_from_file_location("modelo_v2", caminho)
modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)

df = modulo.carregar_dados()

for c in ["data_atendimento", "data_envio_lote"]:
    df[c] = pd.to_datetime(df[c], errors="coerce")

for c in ["valor_apresentado", "valor_glosado", "quantidade"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df = df.dropna(subset=["data_atendimento", "valor_glosado"]).copy()
df["teve_glosa"] = (df["valor_glosado"] > 0).astype(int)
df["mes"] = df["data_atendimento"].dt.month
df["dia_semana"] = df["data_atendimento"].dt.dayofweek
df["dias_ate_envio"] = (
    df["data_envio_lote"] - df["data_atendimento"]
).dt.days
df["possui_autorizacao"] = (
    df["senha_autorizacao"].fillna("").astype(str).str.strip().ne("")
).astype(int)

categoricas = ["operadora", "codigo_tuss", "tipo_guia"]
numericas = [
    "quantidade", "valor_apresentado", "mes",
    "dia_semana", "dias_ate_envio", "possui_autorizacao"
]
colunas = categoricas + numericas

for c in categoricas:
    df[c] = df[c].fillna("Desconhecido").astype(str)

df["chave_guia"] = (
    df["operadora"] + "|" +
    df["numero_guia"].fillna("SEM_GUIA").astype(str)
)

datas = df["data_atendimento"].drop_duplicates().sort_values()
corte1 = datas.iloc[int(len(datas) * 0.6)]
corte2 = datas.iloc[int(len(datas) * 0.8)]

treino = df[df["data_atendimento"] < corte1].copy()
validacao = df[
    (df["data_atendimento"] >= corte1) &
    (df["data_atendimento"] < corte2)
].copy()
teste = df[df["data_atendimento"] >= corte2].copy()

validacao = validacao[
    ~validacao["chave_guia"].isin(treino["chave_guia"])
]
teste = teste[
    ~teste["chave_guia"].isin(
        pd.concat([treino["chave_guia"], validacao["chave_guia"]])
    )
]

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder

resultados = []

for peso in [None, "balanced"]:
    for profundidade in [5, 10]:
        preparacao = ColumnTransformer([
            ("categoricas", OneHotEncoder(handle_unknown="ignore"), categoricas),
            ("numericas", SimpleImputer(strategy="median"), numericas)
        ])

        modelo = Pipeline([
            ("preparacao", preparacao),
            ("classificador", RandomForestClassifier(
                n_estimators=200,
                max_depth=profundidade,
                min_samples_leaf=10,
                class_weight=peso,
                random_state=42
            ))
        ])

        modelo.fit(treino[colunas], treino["teve_glosa"])
        probabilidades = modelo.predict_proba(validacao[colunas])[:, 1]

        ap = average_precision_score(
            validacao["teve_glosa"], probabilidades
        )

        resultados.append((ap, peso, profundidade))

print("Treino:", len(treino))
print("Validação:", len(validacao))
print("Teste reservado:", len(teste))
print("\nRESULTADOS DA VALIDAÇÃO")

for ap, peso, profundidade in sorted(resultados, reverse=True):
    print(
        f"Peso: {str(peso):8} | "
        f"Profundidade: {profundidade:2} | "
        f"Average Precision: {ap:.4f}"
    )

print("\nTeste final permanece reservado para avaliação posterior.")
