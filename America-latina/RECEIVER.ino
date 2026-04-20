#include <esp_now.h>
#include <WiFi.h>

const int pinoMotor = 19;
const int pinoLED = 21;

typedef struct struct_mensagem {
  bool alertaPerigo;
} struct_mensagem;
struct_mensagem dadosRecebidos;

void aoReceberDados(const esp_now_recv_info * info, const uint8_t *incomingData, int len) {
  memcpy(&dadosRecebidos, incomingData, sizeof(dadosRecebidos));
  
  if (dadosRecebidos.alertaPerigo) {
    Serial.println("VIBRANDO: Perigo real detectado!");
    digitalWrite(pinoMotor, HIGH);
    digitalWrite(pinoLED, HIGH);
    
    delay(1000); // 1 segundo de vibracao forte
    
    digitalWrite(pinoMotor, LOW);
    digitalWrite(pinoLED, LOW);
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(pinoMotor, OUTPUT);
  pinMode(pinoLED, OUTPUT);
  digitalWrite(pinoMotor, LOW);
  digitalWrite(pinoLED, LOW);

  WiFi.mode(WIFI_STA);
  if (esp_now_init() != ESP_OK) { return; }
  
  esp_now_register_recv_cb(aoReceberDados);
  Serial.println("Guidao TouchBike: Escutando apenas perigos...");
}

void loop() {
  // O loop fica livre para o ESP-NOW trabalhar via interrupção
}