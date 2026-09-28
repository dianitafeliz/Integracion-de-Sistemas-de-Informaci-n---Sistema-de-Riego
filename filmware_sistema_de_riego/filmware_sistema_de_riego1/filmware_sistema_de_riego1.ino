// =====================================================
// SISTEMA DE RIEGO INTELIGENTE - ESP32-CAM
// Integración Hardware + Firmware + Python + MySQL
// PRUEBA DE DATO INVALIDO
// =====================================================


// ---------------- PINES ----------------
const int SENSOR_HUMEDAD = 13;
const int SENSOR_LUZ     = 15;
const int RELE           = 14;


// ---------------- CONFIGURACIÓN ----------------
const int UMBRAL_SECO = 3000;

const unsigned long TIEMPO_RIEGO = 5000;       // 5 segundos
const unsigned long INTERVALO_LECTURA = 15000; // 15 segundos

const char* DEVICE_ID = "ESP32-CAM-001";


// ---------------- VARIABLES ----------------
unsigned long ultimaLectura = 0;
unsigned long inicioRiego = 0;

bool bombaEncendida = false;


// =====================================================
// SETUP
// =====================================================
void setup() {

  Serial.begin(115200);

  delay(1000);

  // Configuración de pines
  pinMode(SENSOR_HUMEDAD, INPUT);
  pinMode(SENSOR_LUZ, INPUT);
  pinMode(RELE, OUTPUT);

  // Asegurar bomba apagada al iniciar
  digitalWrite(RELE, LOW);

  // Mensaje de inicio
  Serial.println();
  Serial.println("====================================");
  Serial.println(" SISTEMA DE RIEGO INTELIGENTE");
  Serial.println("====================================");

  Serial.print("DEVICE_ID: ");
  Serial.println(DEVICE_ID);

  Serial.println("Sistema iniciado correctamente.");
  Serial.println();
}


// =====================================================
// LOOP PRINCIPAL
// =====================================================
void loop() {

  unsigned long ahora = millis();


  // ---------------------------------------------------
  // CONTROL DEL TIEMPO DE RIEGO
  // ---------------------------------------------------
  if (bombaEncendida) {

    if (ahora - inicioRiego >= TIEMPO_RIEGO) {

      digitalWrite(RELE, LOW);

      bombaEncendida = false;

      Serial.println("[EVENTO] RIEGO_FINALIZADO");
      Serial.println("[BOMBA] OFF");
      Serial.println();
    }
  }


  // ---------------------------------------------------
  // LECTURA PERIODICA
  // ---------------------------------------------------
  if (ahora - ultimaLectura >= INTERVALO_LECTURA) {

    ultimaLectura = ahora;

    leerSensores();
  }
}


// =====================================================
// LECTURA DE SENSORES
// =====================================================
void leerSensores() {

  // ===================================================
  // LECTURA REAL DEL SENSOR
  // ===================================================

  int humedad = analogRead(SENSOR_HUMEDAD);

  int luzDigital = digitalRead(SENSOR_LUZ);


  // ---------------------------------------------------
  // VALIDACIÓN DEL VALOR DE HUMEDAD
  // ---------------------------------------------------

  if (humedad < 0 || humedad > 4095) {

    Serial.println("[ALERTA] VALOR_HUMEDAD_FUERA_DE_RANGO");

    return;
  }


  // ---------------------------------------------------
  // CLASIFICACIÓN DE HUMEDAD
  // ---------------------------------------------------

  String estadoHumedad;


  if (humedad > UMBRAL_SECO) {

    estadoHumedad = "SECO";

  }
  else if (humedad >= 1800) {

    estadoHumedad = "MEDIO";

  }
  else {

    estadoHumedad = "HUMEDO";
  }


  // ---------------------------------------------------
  // CLASIFICACIÓN DE LUZ
  // ---------------------------------------------------
  //
  // En nuestro módulo:
  //
  // 0 = LUZ
  // 1 = OSCURIDAD
  //
  // ---------------------------------------------------

  String estadoLuz;


  if (luzDigital == 0) {

    estadoLuz = "LUZ";

  }
  else {

    estadoLuz = "OSCURIDAD";
  }


  // ---------------------------------------------------
  // MOSTRAR DATOS EN SERIAL
  // ---------------------------------------------------

  Serial.println("------------------------------------");

  Serial.print("DEVICE_ID: ");
  Serial.println(DEVICE_ID);

  Serial.print("HUMEDAD_RAW: ");
  Serial.println(humedad);

  Serial.print("HUMEDAD_ESTADO: ");
  Serial.println(estadoHumedad);

  Serial.print("LUZ: ");
  Serial.println(estadoLuz);

  Serial.print("BOMBA: ");

  

  if (bombaEncendida) {

    Serial.println("ON");

  }
  else {

    Serial.println("OFF");
  }


  // ---------------------------------------------------
  // DECISIÓN DE RIEGO
  // ---------------------------------------------------

  if (estadoHumedad == "SECO" && !bombaEncendida) {

    iniciarRiego();
  }


  // ---------------------------------------------------
  // ENVÍO DE TELEMETRÍA A PYTHON
  // ---------------------------------------------------

  Serial.print("DATA:{");

  Serial.print("\"device_id\":\"");
  Serial.print(DEVICE_ID);

  Serial.print("\",\"humidity_raw\":");
  Serial.print(humedad);

  Serial.print(",\"humidity_state\":\"");
  Serial.print(estadoHumedad);

  Serial.print("\",\"light\":\"");
  Serial.print(estadoLuz);

  Serial.print("\",\"pump\":\"");

  if (bombaEncendida) {

    Serial.print("ON");

  }
  else {

    Serial.print("OFF");
  }

  Serial.println("\"}");

  Serial.println("------------------------------------");
}


// =====================================================
// INICIAR RIEGO
// =====================================================
void iniciarRiego() {

  bombaEncendida = true;

  inicioRiego = millis();

  // Activar relé
  digitalWrite(RELE, HIGH);

  Serial.println();
  Serial.println("[ALERTA] HUMEDAD_BAJA");
  Serial.println("[EVENTO] RIEGO_INICIADO");
  Serial.println("[BOMBA] ON");
  Serial.println();
}