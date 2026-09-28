# 🌱 Sistema de Riego Inteligente — ESP32 - ARDUINO ID + Python + MySQL

Proyecto académico de **Integración de Sistemas de Información** desarrollado para la Universidad Santo Tomás, segundo corte, 2026-2.

El proyecto integra **Hardware, Firmware, Sistema Operativo y Software de Aplicación** mediante un sistema de riego inteligente basado en un ESP32-CAM. El dispositivo adquiere información de sensores de humedad y luz, procesa inicialmente los datos, controla una bomba mediante un relé y envía telemetría a una aplicación Python.

La aplicación Python recibe los datos por comunicación serial, los valida, almacena información en MySQL y JSON, registra eventos, monitorea recursos del sistema operativo, maneja desconexiones y genera un reporte resumido de ejecución.

---

# 1. Objetivo del proyecto

Implementar una integración completa entre un dispositivo físico y una aplicación de software siguiendo el flujo:

```text
HARDWARE
   ↓
FIRMWARE
   ↓
COMUNICACIÓN SERIAL USB
   ↓
SISTEMA OPERATIVO
   ↓
PYTHON
   ↓
VALIDACIÓN Y PROCESAMIENTO
   ↓
MYSQL + JSON
   ↓
REPORTE DE EJECUCIÓN
```

El proyecto busca demostrar:

- Captura de datos desde hardware.
- Procesamiento inicial en firmware.
- Comunicación entre dispositivo y computador.
- Validación de información.
- Persistencia de datos.
- Registro de eventos.
- Manejo de errores.
- Reconexión automática.
- Observabilidad.
- Consulta de recursos del sistema operativo.
- Generación de evidencias y reporte.

---

# 2. Problema

El sistema busca automatizar el monitoreo de las condiciones de un cultivo o planta mediante la lectura de humedad del suelo y condiciones de iluminación.

Cuando el suelo presenta una condición seca, el sistema puede activar la bomba de agua durante un tiempo definido.

Además de realizar el control físico, el sistema registra las condiciones detectadas y permite consultar posteriormente la información generada durante la ejecución.

---

# 3. Arquitectura del sistema
<img width="1915" height="1001" alt="image" src="https://github.com/user-attachments/assets/b629d6a3-8fb4-485c-8ff5-c77729d2947f" />

La arquitectura está dividida en cinco componentes principales:

```text
┌───────────────────────┐
│       HARDWARE        │
│ ESP32-CAM + sensores  │
│ + relé + bomba        │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│       FIRMWARE        │
│ Lectura + clasificación│
│ + control + JSON      │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ COMUNICACIÓN SERIAL    │
│ USB - COM3 - 115200    │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│    APLICACIÓN PYTHON   │
│ Recepción + validación │
│ errores + reconexión   │
└───────────┬───────────┘
            ↓
       ┌────┴────┐
       ↓         ↓
┌──────────┐ ┌──────────────┐
│  MySQL   │ │ JSON histórico│
└──────────┘ └──────┬───────┘
                    ↓
             ┌──────────────┐
             │   REPORTE    │
             └──────────────┘
```

---

# 4. Hardware

Los componentes utilizados son:

- **ESP32-CAM**
- Sensor de humedad del suelo
- Sensor de luz
- Módulo relé de un canal
- Bomba de agua
- Adaptador USB-Serial
- Transistor BC548
- Resistencia de 1 kΩ
- Fuente de alimentación y cableado

## Responsabilidad del hardware

El hardware se encarga de:

- Capturar físicamente las condiciones del entorno.
- Convertir las condiciones físicas en señales eléctricas.
- Ejecutar físicamente las acciones ordenadas por el sistema.
- Permitir el control de la bomba mediante el relé.

El hardware no realiza el almacenamiento histórico ni genera reportes.

---

# 5. Pines utilizados

| Componente | Pin ESP32-CAM |
|---|---:|
| Sensor de humedad AO | GPIO 13 |
| Sensor de luz DO | GPIO 15 |
| Control del relé | GPIO 14 |

El control del relé se realiza mediante un transistor, evitando conectar directamente la carga de la bomba a un GPIO del ESP32.

---

# 6. Firmware

El firmware se encuentra en:

```text
firmware_sistema_de_riego/
```

El programa fue desarrollado para el ESP32-CAM utilizando Arduino IDE.

## Responsabilidades del firmware

El firmware se encarga de:

1. Inicializar la comunicación serial.
2. Configurar los pines.
3. Leer el sensor de humedad.
4. Leer el sensor de luz.
5. Clasificar la humedad.
6. Determinar cuándo iniciar el riego.
7. Controlar el relé.
8. Finalizar el riego después del tiempo configurado.
9. Generar la telemetría.
10. Enviar la información por el puerto serial.

## Variables principales

```cpp
const int SENSOR_HUMEDAD = 13;
const int SENSOR_LUZ     = 15;
const int RELE           = 14;
```

Configuración principal:

```cpp
const int UMBRAL_SECO = 3000;
const unsigned long TIEMPO_RIEGO = 5000;
const unsigned long INTERVALO_LECTURA = 15000;
const char* DEVICE_ID = "ESP32-CAM-001";
```

## Clasificación de humedad

La lectura del sensor se clasifica como:

```text
> 3000       → SECO
1800 - 3000  → MEDIO
< 1800       → HUMEDO
```

Estos valores corresponden a la calibración realizada para el prototipo.

## Flujo del firmware

```text
Leer humedad
     ↓
Clasificar estado
     ↓
Leer luz
     ↓
¿Está seco?
     ↓
Sí → Activar bomba
     ↓
Enviar telemetría
     ↓
Esperar siguiente lectura
```

---

# 7. Telemetría

El ESP32 genera mensajes en formato JSON.

Ejemplo:

```json
{
  "device_id": "ESP32-CAM-001",
  "humidity_raw": 2416,
  "humidity_state": "MEDIO",
  "light": "LUZ",
  "pump": "OFF"
}
```

## Variables

| Campo | Descripción |
|---|---|
| `device_id` | Identificador del dispositivo |
| `humidity_raw` | Lectura numérica de humedad |
| `humidity_state` | Estado de humedad |
| `light` | Estado de iluminación |
| `pump` | Estado de la bomba |

El sistema cuenta con más de las tres variables/estados mínimos requeridos para la telemetría.

---

# 8. Comunicación

La comunicación entre el ESP32 y el computador se realiza mediante USB/Serial.

```text
ESP32-CAM
    ↓
USB
    ↓
Adaptador Serial
    ↓
Windows
    ↓
COM3
    ↓
Python
```

Configuración:

```text
Puerto: COM3
Baudios: 115200
```

---

# 9. Aplicación Python

El archivo principal es:

```text
sistema_riego_reconexion.py
```

La aplicación es responsable de integrar el ESP32 con los servicios del computador.

## Funciones principales

### Conexión serial

Establece y mantiene la comunicación con el ESP32.

### Conexión MySQL

Establece la conexión con la base de datos:

```text
riego_inteligente
```

### Recepción de telemetría

Lee las líneas enviadas por el ESP32 y detecta los mensajes que contienen datos JSON.

### Validación

Comprueba:

- Estructura del mensaje.
- Existencia de campos.
- Tipos de datos.
- Rango de humedad.
- Estados permitidos.

Por ejemplo:

```text
0 ≤ humidity_raw ≤ 4095
```

Si el valor está fuera de este rango, el dato es rechazado.

### Almacenamiento

Los datos válidos se almacenan en MySQL y en el archivo JSON histórico.

### Registro de eventos

Los eventos importantes se registran en la tabla `eventos`.

### Reconexión

Si se pierde la comunicación, Python intenta conectarse nuevamente sin finalizar el programa.

### Monitoreo

La aplicación consulta recursos del sistema operativo mediante `psutil`.

### Reporte

Al finalizar la ejecución se genera:

```text
reporte_ejecucion.txt
```

---

# 10. Servicios del sistema operativo utilizados

La aplicación Python utiliza servicios y recursos del sistema operativo relacionados principalmente con:

- Comunicación mediante puerto serial.
- Archivos del sistema.
- CPU.
- Memoria RAM.
- Almacenamiento.
- Procesos.
- Permisos de escritura.

La biblioteca utilizada para el monitoreo de recursos es:

```text
psutil
```

---

# 11. Base de datos MySQL

Base de datos:

```text
riego_inteligente
```

## Tabla `telemetria`

Almacena las mediciones válidas recibidas desde el ESP32.

Campos principales:

```text
id
fecha_hora
device_id
humedad_raw
humedad_estado
luz
bomba
```

## Tabla `eventos`

Registra los eventos relevantes de la ejecución.

Campos:

```text
id
fecha_hora
device_id
nivel
evento
resultado
```

Ejemplos:

```text
DEVICE_CONNECTED
DEVICE_DISCONNECTED
TELEMETRIA_VALIDADA
MYSQL_INSERT
INVALID_DATA
JSON_WRITE_ERROR
```

---

# 12. Archivo JSON histórico

El archivo:

```text
telemetria_actual.json
```

mantiene una lista de las telemetrías recibidas.

Ejemplo:

```json
[
  {
    "fecha_hora": "2026-09-23 22:41:24",
    "device_id": "ESP32-CAM-001",
    "humidity_raw": 2370,
    "humidity_state": "MEDIO",
    "light": "LUZ",
    "pump": "OFF"
  },
  {
    "fecha_hora": "2026-09-23 22:41:39",
    "device_id": "ESP32-CAM-001",
    "humidity_raw": 2412,
    "humidity_state": "MEDIO",
    "light": "LUZ",
    "pump": "OFF"
  }
]
```

El archivo conserva múltiples registros en lugar de reemplazar la información anterior.

Se utiliza un límite de registros para evitar un crecimiento indefinido del archivo.

---

# 13. Reporte de ejecución

El archivo:

```text
reporte_ejecucion.txt
```

se genera automáticamente cuando el usuario finaliza la ejecución mediante:

```text
Ctrl + C
```

El reporte contiene:

- Dispositivo.
- Puerto serial.
- Hora de inicio.
- Hora de finalización.
- Duración.
- Mensajes recibidos.
- Telemetrías válidas.
- Datos inválidos rechazados.
- JSON inválidos.
- Inserciones en MySQL.
- Registros actuales en JSON.
- Riegos iniciados.
- Riegos finalizados.
- Desconexiones.
- Reconexiones.
- CPU.
- RAM.
- Disco.
- Recursos utilizados por Python.

---

# 14. Observabilidad y logs

El sistema registra los principales eventos de ejecución.

Ejemplo:

```text
[EVENTO MYSQL] DEVICE_CONNECTED
[EVENTO MYSQL] TELEMETRIA_VALIDADA
[EVENTO MYSQL] MYSQL_INSERT
[EVENTO MYSQL] DEVICE_DISCONNECTED
[EVENTO MYSQL] INVALID_DATA
```

Esto permite conocer:

- Cuándo se conectó el dispositivo.
- Cuándo se perdió la comunicación.
- Cuándo se recuperó.
- Qué datos fueron validados.
- Qué datos fueron rechazados.
- Cuándo se almacenaron los datos.

---

# 15. Manejo de datos inválidos

Se realizaron pruebas enviando datos fuera del rango permitido.

Ejemplo:

```json
{
  "device_id": "ESP32-CAM-001",
  "humidity_raw": 5000,
  "humidity_state": "SECO",
  "light": "LUZ",
  "pump": "OFF"
}
```

Como `5000` está fuera del rango permitido para el sensor:

```text
[ALERTA] Humedad fuera de rango: 5000
[VALIDACIÓN] Datos rechazados.
[EVENTO MYSQL] INVALID_DATA
```

El dato no se almacena como una telemetría válida.

---

# 16. Manejo de JSON inválido

También se realizó una prueba enviando un JSON incompleto o mal formado.

El sistema identifica el error:

```text
[ERROR] JSON inválido recibido desde ESP32.
[EVENTO MYSQL] INVALID_DATA → JSON inválido
```

La aplicación continúa ejecutándose y espera la siguiente telemetría válida.

---

# 17. Desconexión y reconexión

Se realizó una prueba desconectando físicamente el ESP32.

El sistema registra:

```text
DEVICE_DISCONNECTED
```

Python continúa ejecutándose e intenta recuperar la comunicación.

Cuando el dispositivo vuelve a conectarse:

```text
DEVICE_CONNECTED
```

y la recepción de telemetría continúa.

Este mecanismo evita que una pérdida temporal de comunicación termine toda la aplicación.

---

# 18. Monitoreo de recursos

Mediante `psutil` se obtienen indicadores como:

```text
CPU total
RAM total utilizada
Disco ocupado
Disco libre
CPU del proceso Python
RAM del proceso Python
```

Ejemplo de ejecución:

```text
CPU total: 5.1%
RAM total utilizada: 52.5%
Disco ocupado: 33.9%
Disco libre: 330.68 GB

CPU del proceso: 0.0%
RAM del proceso: 34.57 MB
```

---

# 19. Pruebas realizadas

| ID | Prueba | Resultado |
|---|---|---|
| T01 | Lectura de sensores | Correcta |
| T02 | Clasificación de humedad | Correcta |
| T03 | Recepción de telemetría | Correcta |
| T04 | Almacenamiento MySQL | Correcto |
| T05 | Actualización JSON | Correcta |
| T06 | Dato fuera de rango | Rechazado |
| T07 | JSON inválido | Rechazado |
| T08 | Desconexión ESP32 | Detectada |
| T09 | Reconexión ESP32 | Recuperada |
| T10 | Registro de eventos | Correcto |
| T11 | Monitoreo del sistema | Correcto |
| T12 | Generación de reporte | Correcta |

---



# 20. Instalación

## Requisitos

### Hardware

- ESP32-CAM.
- Sensor de humedad.
- Sensor de luz.
- Relé.
- Bomba.
- Adaptador USB-Serial.
- Componentes de conexión.

### Software

- Arduino IDE.
- Soporte ESP32.
- Python 3.
- MySQL.
- Visual Studio Code.

### Bibliotecas Python

```bash
pip install pyserial mysql-connector-python psutil
```

---

# 21. Configuración de la base de datos

La aplicación utiliza:

```text
Base de datos: riego_inteligente
```

Se deben configurar las credenciales de MySQL en el archivo Python según el entorno donde se ejecute el proyecto.

Las tablas utilizadas son:

```text
telemetria
eventos
```

---

# 22. Ejecución del firmware

1. Abrir Arduino IDE.
2. Abrir el firmware.
3. Seleccionar la placa:

```text
AI Thinker ESP32-CAM
```

4. Seleccionar el puerto correspondiente.
5. Cargar el programa.
6. Abrir el monitor serial.
7. Configurar:

```text
115200 baudios
```

---

# 23. Ejecución de Python

Desde la carpeta del proyecto:

```bash
python sistema_riego_reconexion.py
```

Durante la ejecución se mostrarán:

- Recursos del sistema.
- Conexión del ESP32.
- Datos recibidos.
- Validaciones.
- Inserciones en MySQL.
- Actualizaciones del JSON.
- Errores.
- Desconexiones.
- Reconexiones.

Para finalizar:

```text
Ctrl + C
```

Al finalizar se genera:

```text
reporte_ejecucion.txt
```

---

# 24. Autora

**Diana Moreno**

Ingeniería en Informática  
Universidad Santo Tomás  
Bogotá, Colombia

**Proyecto académico — 2026-2**
