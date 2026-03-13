import pandas as pd

# Lê o seu arquivo
df = pd.read_csv('annotations.csv')

print("\n--- AQUI ESTÃO OS NOMES REAIS DAS SUAS COLUNAS ---")
print(list(df.columns))
print("--------------------------------------------------\n")

# Mostra as primeiras 3 linhas para a gente entender o formato
print("EXEMPLO DOS DADOS:")
print(df.head(3))