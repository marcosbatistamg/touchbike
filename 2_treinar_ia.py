import os
import pandas as pd
import numpy as np
import librosa
import tensorflow as tf
from sklearn.model_selection import train_test_split

# --- CONFIGURAÇÕES ---
PASTA_AUDIOS = 'audios_wav' 
CSV_FILE = 'annotations.csv'

# CORREÇÃO: Os nomes exatos das colunas conforme seu arquivo
LABELS = [
    '1_engine_presence', 
    '2_machinery-impact_presence', 
    '3_non-machinery-impact_presence', 
    '4_powered-saw_presence', 
    '5_alert-signal_presence', 
    '6_music_presence', 
    '7_human-voice_presence', 
    '8_dog_presence'
]

print("--- TREINAMENTO CORRIGIDO ---")
print("1. Lendo a planilha e filtrando dados...")
df = pd.read_csv(CSV_FILE)

# CORREÇÃO IMPORTANTE: 
# Vamos filtrar apenas onde 'split' é 'train' ou 'validate'.
# O 'test' costuma ter valor -1 (sem resposta), o que confunde a IA.
df = df[df['split'].isin(['train', 'validate'])]

# Agrupa as respostas dos vários anotadores
df_agrupado = df.groupby('audio_filename')[LABELS].mean()

# Se a média for maior que 0.5, consideramos que o som existe
df_final = (df_agrupado >= 0.5).astype(int)

# Pegando todos os arquivos disponíveis no treino
lista_arquivos = df_final.index 
total_arquivos = len(lista_arquivos)

print(f"   Encontrei {total_arquivos} áudios válidos para treino.")

X = []
y = []

print(f"2. Processando áudios (Isso vai demorar, tenha paciência)...")

def achar_caminho(nome_arquivo):
    for root, dirs, files in os.walk(PASTA_AUDIOS):
        if nome_arquivo in files:
            return os.path.join(root, nome_arquivo)
    return None

contador = 0
audios_perdidos = 0

for nome_arquivo in lista_arquivos:
    caminho = achar_caminho(nome_arquivo)
    
    if caminho:
        try:
            # Tenta carregar o áudio
            audio, sr = librosa.load(caminho, sr=22050, duration=4.0)
            
            # Garante tamanho exato (4 segundos)
            fixo = 22050 * 4
            if len(audio) < fixo:
                audio = np.pad(audio, (0, fixo - len(audio)))
            else:
                audio = audio[:fixo]
            
            # Transforma em imagem
            spec = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=64)
            spec_db = librosa.power_to_db(spec, ref=np.max)
            
            X.append(spec_db)
            y.append(df_final.loc[nome_arquivo].values)
            
            contador += 1
            if contador % 100 == 0: 
                print(f"Progresso: {contador}/{total_arquivos}")
                
        except Exception as e:
            print(f"Erro no arquivo {nome_arquivo}: {e}")
            audios_perdidos += 1
    else:
        # Se não achar o arquivo, passa pro próximo
        audios_perdidos += 1

print(f"\nResumo: {contador} processados, {audios_perdidos} não encontrados.")

if contador == 0:
    print("ERRO CRÍTICO: Nenhum áudio foi processado. Verifique se a pasta 'audios_wav' está cheia.")
    exit()

# Formata para a IA
X = np.array(X)[..., np.newaxis]
y = np.array(y)

print(f"3. Treinando a IA com {len(X)} exemplos...")

model = tf.keras.models.Sequential([
    tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(64, 173, 1)),
    tf.keras.layers.MaxPooling2D((2, 2)),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(8, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Treina
model.fit(X, y, epochs=10, batch_size=32)

print("4. Salvando...")
model.save('cerebro_ia.h5')
print("PRONTO! O arquivo 'cerebro_ia.h5' foi criado com sucesso!")