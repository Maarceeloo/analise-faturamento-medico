
import pandas as pd
from pathlib import Path

pasta = Path(__file__).resolve().parent.parent
arquivo = pasta / "data" / "processed" / "previsoes_glosas_teste.csv"

df = pd.read_csv(arquivo, sep=";", decimal=",")

print("Registros avaliados:", len(df))
print("Glosas reais:", df["glosa_real"].sum())

print("\nComparação dos limites:")
print("Limite | Identificadas | Perdidas | Alertas incorretos")

for limite in [0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]:
    previsao = df["probabilidade_glosa"] >= limite
    real = df["glosa_real"] == 1

    identificadas = (previsao & real).sum()
    perdidas = (~previsao & real).sum()
    incorretos = (previsao & ~real).sum()

    print(
        f"{limite:.0%} | {identificadas} | "
        f"{perdidas} | {incorretos}"
    )
