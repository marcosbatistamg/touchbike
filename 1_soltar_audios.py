import tarfile
import glob
import os

print("--- ETAPA 1: SOLTANDO OS ÁUDIOS ---")

# Cria uma pasta para guardar os audios wav
pasta_destino = "audios_wav"
if not os.path.exists(pasta_destino):
    os.makedirs(pasta_destino)

# Pega a lista de todos os pacotes trancados
pacotes = glob.glob("audio-*.tar.gz")
print(f"Encontrei {len(pacotes)} pacotes para abrir.")

for pacote in pacotes:
    print(f"Abrindo {pacote}... aguarde.")
    try:
        with tarfile.open(pacote, "r:gz") as tar:
            tar.extractall(path=pasta_destino)
    except:
        print(f"Erro ao abrir {pacote}, pulando.")

print("\nSUCESSO! Todos os áudios foram para a pasta 'audios_wav'.")