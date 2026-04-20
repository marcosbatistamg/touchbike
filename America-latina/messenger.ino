#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <driver/i2s.h>
#include <mg_batista-project-1_inferencing.h> 

// --- ENDEREÇO MAC DO GUIDÃO (RECEPTOR) ---
uint8_t enderecoReceptor[] = {0x28, 0x05, 0xA5, 0x0F, 0xEF, 0x70};

// --- PINOS I2S (MICROFONE) ---
#define I2S_WS 25
#define I2S_SD 32
#define I2S_SCK 33
#define I2S_PORT I2S_NUM_0

// --- PINOS DO SENSOR DE PROXIMIDADE (RADAR) ---
const int pinoTrig = 5;
const int pinoEcho = 18;

typedef struct struct_mensagem {
  bool alertaPerigo;
} struct_mensagem;
struct_mensagem envioData;
esp_now_peer_info_t peerInfo;

float *buffer_audio;

void setupI2S() {
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = 16000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = i2s_comm_format_t(I2S_COMM_FORMAT_I2S | I2S_COMM_FORMAT_I2S_MSB),
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 128,
    .use_apll = false
  };
  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };
  i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_PORT, &pin_config);
}

void setup() {
  Serial.begin(115200);
  
  // Inicia Pinos do Radar
  pinMode(pinoTrig, OUTPUT);
  pinMode(pinoEcho, INPUT);
  
  setupI2S();

  WiFi.mode(WIFI_STA);
  if (esp_now_init() != ESP_OK) { return; }
  
  memcpy(peerInfo.peer_addr, enderecoReceptor, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;
  esp_now_add_peer(&peerInfo);

  buffer_audio = (float *)malloc(EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE * sizeof(float));
  Serial.println(">>> MODO DEFESA: SIRENE RÁPIDA + RADAR (20cm) <<<");
}

void loop() {
  bool enviarSinal = false;

  // ==========================================
  // 1. VERIFICAÇÃO DO RADAR (Sensor HC-SR04)
  // ==========================================
  digitalWrite(pinoTrig, LOW); 
  delayMicroseconds(2);
  digitalWrite(pinoTrig, HIGH); 
  delayMicroseconds(10);
  digitalWrite(pinoTrig, LOW);
  
  // Timeout super baixo (3000 microsegundos = 3ms). 
  // Mede rapidamente distâncias de até 50cm sem travar o microfone!
  long duracao = pulseIn(pinoEcho, HIGH, 3000); 
  int distancia = (duracao == 0) ? 999 : duracao * 0.034 / 2;

  // Se o objeto estiver a 20 centímetros ou menos
  if (distancia > 0 && distancia <= 20) { 
    enviarSinal = true;
    Serial.print("⚠️ RADAR DISPARADO: Objeto a ");
    Serial.print(distancia);
    Serial.println(" cm!");
  }

  // ==========================================
  // 2. CAPTURA DE ÁUDIO E IA
  // ==========================================
  size_t bytes_lidos;
  int32_t amostra_raw;
  for (int i = 0; i < EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE; i++) {
    i2s_read(I2S_PORT, &amostra_raw, sizeof(int32_t), &bytes_lidos, portMAX_DELAY);
    buffer_audio[i] = (float)(amostra_raw >> 16) * 10.0f;
  }

  signal_t signal;
  numpy::signal_from_buffer(buffer_audio, EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE, &signal);
  ei_impulse_result_t result = { 0 };
  run_classifier(&signal, &result, false);

  // Filtro Rápido para Sirene
  for (uint16_t i = 0; i < EI_CLASSIFIER_LABEL_COUNT; i++) {
    String label = String(result.classification[i].label);
    label.toLowerCase();
    label.trim();

    if (label == "sirene de ambulância" && result.classification[i].value > 0.80) {
        enviarSinal = true;
        Serial.print("🚨 SIRENE CONFIRMADA! Confiança: ");
        Serial.println(result.classification[i].value);
    }
  }

  // ==========================================
  // 3. ENVIO PARA O GUIDÃO
  // ==========================================
  if (enviarSinal) {
    envioData.alertaPerigo = true;
    esp_now_send(enderecoReceptor, (uint8_t *) &envioData, sizeof(envioData));
    Serial.println("Sinal enviado! Vibrando guidão...");
    
    delay(300); // Pequena pausa para evitar sobrecarga de sinal
  } else {
    Serial.print("."); 
  }
  
  yield();
}