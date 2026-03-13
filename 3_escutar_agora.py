import sounddevice as sd
import numpy as np
import librosa
import tensorflow as tf
import os
import time
import queue

# --- CONFIGURAÇÕES ---
ARQUIVO_MODELO = 'cerebro_ia.h5'
TAXA_AMOSTRAGEM = 22050
DURACAO_MODELO = 4 # O modelo aprendeu com 4 segundos
TAMANHO_BUFFER = int(TAXA_AMOSTRAGEM * DURACAO_MODELO) # Tamanho da memória (88200 pontos)

# SE ESTIVER SURDO: Aumente este número (ex: 5.0 ou 10.0) para multiplicar o volume
VOLUME_BOOST = 5.0 

CATEGORIAS = [
    '🚗 MOTOR / TRAFFIC',      # 1
    '🏗️  HEAVY MACHINERY',    # 2
    '🔨 COLLISION / IMPACT',      # 3
    '🪚 ELECTRIC SAW',        # 4
    '🚨 SIREN / ALARM',       # 5
    '🎵 MUSIC',                # 6
    '🗣️ HUMAN VOICE',            # 7
    '🐶 DOG BARKING'       # 8
]

# --- INICIALIZAÇÃO ---
print("\n" + "="*50)
print("🎧 Continuous Listening System (Turbo)")
print("="*50)

if not os.path.exists(ARQUIVO_MODELO):
    print(f"❌ ERRO: O arquivo '{ARQUIVO_MODELO}' não existe.")
    print("Espere o Passo 2 (Treinamento) terminar!")
    exit()

print("1. Carregando IA...", end=" ")
try:
    model = tf.keras.models.load_model(ARQUIVO_MODELO)
    print("✅ OK!")
except:
    print("❌ Falha.")
    exit()

# Cria um buffer (memória) cheio de silêncio para começar
audio_buffer = np.zeros(TAMANHO_BUFFER, dtype=np.float32)

def callback_microfone(indata, frames, time, status):
    """Essa função roda em segundo plano o tempo todo, enchendo a memória."""
    global audio_buffer
    if status:
        print(status)
    
    # Pega o som novo que chegou do microfone
    som_novo = indata[:, 0] # Pega canal 1
    
    # Empurra o som antigo para fora e coloca o novo no final (Rolagem)
    audio_buffer = np.roll(audio_buffer, -len(som_novo))
    audio_buffer[-len(som_novo):] = som_novo

def processar_e_prever():
    # Pega uma CÓPIA da memória atual (com volume aumentado)
    audio_analise = audio_buffer * VOLUME_BOOST
    
    # Transforma em imagem (Espectrograma)
    spec = librosa.feature.melspectrogram(y=audio_analise, sr=TAXA_AMOSTRAGEM, n_mels=64)
    spec_db = librosa.power_to_db(spec, ref=np.max)
    
    # Ajuste fino de tamanho (173 pixels de largura)
    largura_alvo = 173
    if spec_db.shape[1] < largura_alvo:
        pad = largura_alvo - spec_db.shape[1]
        spec_db = np.pad(spec_db, ((0,0), (0, pad)))
    else:
        spec_db = spec_db[:, :largura_alvo]
        
    entrada = spec_db[np.newaxis, ..., np.newaxis]
    
    # A IA adivinha
    previsao = model.predict(entrada, verbose=0)[0]
    return previsao

# --- LOOP PRINCIPAL ---
print("\n🎤  I'M LISTENING NON-STOP! (Speak or play a sound)")
print(f"🔊 Amplified volume in {VOLUME_BOOST}x")
print("🛑  Ctrl + C for exit \n")

# Abre o microfone em modo contínuo
stream = sd.InputStream(callback=callback_microfone, 
                        channels=1, 
                        samplerate=TAXA_AMOSTRAGEM, 
                        blocksize=int(TAXA_AMOSTRAGEM * 0.5)) # Atualiza a cada 0.5s

try:
    with stream:
        while True:
            # Dorme um pouquinho para não travar o PC (0.5 segundos)
            time.sleep(0.5)
            
            # Pede para a IA analisar o que tem na memória AGORA
            preds = processar_e_prever()
            
            # --- MOSTRA O RESULTADO ---
            # Vamos limpar a linha para dar efeito de atualização real
            print(" " * 100, end="\r") 
            
            texto_saida = ""
            detectou = False
            
            # Barra de volume visual (para você saber se o mic está funcionando)
            vol_atual = np.max(np.abs(audio_buffer[-2000:])) * 100
            barrinha_vol = "|" * int(vol_atual)
            
            for i in range(len(CATEGORIAS)):
                chance = preds[i] * 100
                if chance > 40: # Sensibilidade: mostra acima de 40%
                    texto_saida += f"[{CATEGORIAS[i]}: {int(chance)}%] "
                    detectou = True
            
            if detectou:
                print(f"🔊 {texto_saida}", end="\r")
            else:
                # Mostra o volume se não detectar nada
                print(f"👂 Listening... Vol: {barrinha_vol}", end="\r")

except KeyboardInterrupt:
    print("\n\n🛑 System Stoped.")
except Exception as e:
    print(f"\n❌ Error: {e}")