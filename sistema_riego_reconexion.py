import serial
import json
import mysql.connector
import psutil
import os
import time
from datetime import datetime


# =====================================================
# CONFIGURACIÓN
# =====================================================

PUERTO = "COM3"
BAUDRATE = 115200

# El ESP32 envía datos cada 15 segundos.
# Si no llega ningún dato durante este tiempo,
# se considera pérdida de comunicación.
TIMEOUT_COMUNICACION = 30

# Intentar reconectar cada 5 segundos.
INTERVALO_RECONEXION = 5

# Consultar recursos del sistema cada 60 segundos.
INTERVALO_SISTEMA = 60

# Máximo de registros conservados en el archivo JSON.
MAX_REGISTROS_JSON = 1000

# Reporte resumido de ejecución (se reemplaza en cada ejecución).
RUTA_REPORTE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "reporte_ejecucion.txt"
)


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "riego_inteligente"
}


DEVICE_ID = "ESP32-CAM-001"

# Archivo JSON único: se reemplaza en cada telemetría válida.
RUTA_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "telemetria_actual.json"
)


# =====================================================
# MYSQL
# =====================================================

def conectar_mysql():

    try:

        conexion = mysql.connector.connect(**DB_CONFIG)

        if conexion.is_connected():

            print("===================================")
            print(" CONEXIÓN MYSQL EXITOSA")
            print("===================================")
            print("Base de datos: riego_inteligente")

            return conexion

    except mysql.connector.Error as error:

        print("[ERROR MYSQL] No se pudo conectar.")
        print(error)

    return None


def registrar_evento(
    conexion,
    device_id,
    nivel,
    evento,
    resultado
):

    try:

        cursor = conexion.cursor()

        sql = """
        INSERT INTO eventos
        (
            fecha_hora,
            device_id,
            nivel,
            evento,
            resultado
        )
        VALUES (%s, %s, %s, %s, %s)
        """

        valores = (
            datetime.now(),
            device_id,
            nivel,
            evento,
            resultado
        )

        cursor.execute(sql, valores)
        conexion.commit()
        cursor.close()

        print(
            f"[EVENTO MYSQL] {evento} -> {resultado}"
        )

    except mysql.connector.Error as error:

        print(
            "[ERROR MYSQL] No se pudo registrar el evento."
        )
        print(error)


def guardar_telemetria(conexion, datos):

    try:

        cursor = conexion.cursor()

        sql = """
        INSERT INTO telemetria
        (
            fecha_hora,
            device_id,
            humedad_raw,
            humedad_estado,
            luz,
            bomba
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        valores = (
            datetime.now(),
            datos["device_id"],
            datos["humidity_raw"],
            datos["humidity_state"],
            datos["light"],
            datos["pump"]
        )

        cursor.execute(sql, valores)
        conexion.commit()
        cursor.close()

        print(
            "[MYSQL] Telemetría almacenada correctamente."
        )

        estadisticas["mysql_inserts"] += 1

        registrar_evento(
            conexion,
            datos["device_id"],
            "INFO",
            "MYSQL_INSERT",
            "Telemetría almacenada correctamente"
        )

    except mysql.connector.Error as error:

        print(
            "[ERROR MYSQL] No se pudo guardar la telemetría."
        )
        print(error)


# =====================================================
# PERSISTENCIA JSON
# =====================================================

def guardar_json(datos):

    try:

        registro = {
            "fecha_hora": datetime.now().isoformat(sep=" ", timespec="seconds"),
            **datos
        }

        # Leer el historial existente si ya existe.
        registros = []

        if os.path.exists(RUTA_JSON):

            try:

                with open(RUTA_JSON, "r", encoding="utf-8") as archivo:
                    contenido = json.load(archivo)

                if isinstance(contenido, list):
                    registros = contenido

            except (json.JSONDecodeError, OSError):

                # Si el archivo está vacío o corrupto, se inicia un historial nuevo.
                registros = []

        # Agregar la nueva telemetría válida.
        registros.append(registro)

        # Conservar solamente los últimos N registros.
        registros = registros[-MAX_REGISTROS_JSON:]

        with open(RUTA_JSON, "w", encoding="utf-8") as archivo:

            json.dump(
                registros,
                archivo,
                ensure_ascii=False,
                indent=4
            )

        print(
            f"[JSON] Telemetría agregada. Registros almacenados: {len(registros)}"
        )

    except (OSError, TypeError) as error:

        print(
            "[ERROR JSON] No se pudo guardar la telemetría."
        )
        print(error)

        registrar_evento(
            conexion,
            datos.get("device_id", DEVICE_ID),
            "ERROR",
            "JSON_WRITE_ERROR",
            str(error)
        )


# =====================================================
# VALIDACIÓN
# =====================================================

def validar_datos(datos):

    campos_requeridos = [
        "device_id",
        "humidity_raw",
        "humidity_state",
        "light",
        "pump"
    ]

    for campo in campos_requeridos:

        if campo not in datos:

            print(
                f"[ERROR] Campo faltante: {campo}"
            )

            return False, "Campo faltante"


    humedad = datos["humidity_raw"]

    if not isinstance(humedad, int):

        print(
            "[ERROR] humidity_raw no es un entero."
        )

        return False, "humidity_raw no es entero"


    if humedad < 0 or humedad > 4095:

        print(
            f"[ALERTA] Humedad fuera de rango: {humedad}"
        )

        return False, "Humedad fuera de rango"


    if datos["humidity_state"] not in [
        "SECO",
        "MEDIO",
        "HUMEDO"
    ]:

        print(
            "[ERROR] Estado de humedad inválido."
        )

        return False, "Estado de humedad inválido"


    if datos["light"] not in [
        "LUZ",
        "OSCURIDAD"
    ]:

        print(
            "[ERROR] Estado de luz inválido."
        )

        return False, "Estado de luz inválido"


    if datos["pump"] not in [
        "ON",
        "OFF"
    ]:

        print(
            "[ERROR] Estado de bomba inválido."
        )

        return False, "Estado de bomba inválido"


    return True, "Datos válidos"


# =====================================================
# RECURSOS DEL SISTEMA OPERATIVO
# =====================================================

def consultar_recursos_sistema():

    cpu_sistema = psutil.cpu_percent(
        interval=1
    )

    memoria = psutil.virtual_memory()

    disco = psutil.disk_usage("/")

    proceso = psutil.Process(
        os.getpid()
    )

    return {

        "cpu_sistema":
            cpu_sistema,

        "ram_sistema":
            memoria.percent,

        "disco_usado":
            disco.percent,

        "disco_libre_gb":
            disco.free / (1024 ** 3),

        "cpu_proceso":
            proceso.cpu_percent(
                interval=0.1
            ),

        "ram_proceso_mb":
            proceso.memory_info().rss
            / (1024 ** 2)
    }


def mostrar_recursos_sistema():

    recursos = consultar_recursos_sistema()

    print()
    print(
        "==================================="
    )
    print(
        "[RECURSOS DEL SISTEMA OPERATIVO]"
    )
    print(
        "==================================="
    )

    print(
        f"CPU total: "
        f"{recursos['cpu_sistema']:.1f}%"
    )

    print(
        f"RAM total utilizada: "
        f"{recursos['ram_sistema']:.1f}%"
    )

    print(
        f"Disco ocupado: "
        f"{recursos['disco_usado']:.1f}%"
    )

    print(
        f"Disco libre: "
        f"{recursos['disco_libre_gb']:.2f} GB"
    )

    print()

    print("[PROCESO PYTHON]")

    print(
        f"CPU del proceso: "
        f"{recursos['cpu_proceso']:.1f}%"
    )

    print(
        f"RAM del proceso: "
        f"{recursos['ram_proceso_mb']:.2f} MB"
    )

    print()


# =====================================================
# ABRIR ESP32
# =====================================================

def conectar_esp32():

    try:

        esp32 = serial.Serial(
            port=PUERTO,
            baudrate=BAUDRATE,
            timeout=2
        )

        time.sleep(2)

        return esp32

    except serial.SerialException:

        return None


# =====================================================
# REPORTE RESUMIDO DE EJECUCIÓN (RF08)
# =====================================================

def generar_reporte_ejecucion():

    fecha_fin = datetime.now()
    duracion = fecha_fin - estadisticas["inicio"]

    try:
        minutos, segundos = divmod(int(duracion.total_seconds()), 60)
        horas, minutos = divmod(minutos, 60)
        duracion_texto = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
    except Exception:
        duracion_texto = str(duracion)

    try:
        recursos = consultar_recursos_sistema()
    except Exception:
        recursos = {}

    # Contar registros actualmente almacenados en el JSON.
    registros_json = 0
    try:
        if os.path.exists(RUTA_JSON):
            with open(RUTA_JSON, "r", encoding="utf-8") as archivo:
                contenido = json.load(archivo)
                if isinstance(contenido, list):
                    registros_json = len(contenido)
                elif isinstance(contenido, dict):
                    registros_json = 1
    except Exception:
        registros_json = 0

    lineas = [
        "====================================================",
        " REPORTE RESUMIDO DE EJECUCIÓN - RF08",
        " SISTEMA DE RIEGO INTELIGENTE",
        "====================================================",
        f"Dispositivo: {DEVICE_ID}",
        f"Puerto serial: {PUERTO}",
        f"Inicio: {estadisticas['inicio'].strftime('%Y-%m-%d %H:%M:%S')}",
        f"Fin: {fecha_fin.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Duración: {duracion_texto}",
        "",
        "--- TELEMETRÍA ---",
        f"Mensajes DATA recibidos: {estadisticas['telemetrias_recibidas']}",
        f"Telemetrías válidas: {estadisticas['telemetrias_validas']}",
        f"Datos inválidos rechazados: {estadisticas['datos_invalidos']}",
        f"JSON inválidos recibidos: {estadisticas['json_invalidos']}",
        f"Inserciones en MySQL: {estadisticas['mysql_inserts']}",
        f"Registros actuales en JSON: {registros_json}",
        "",
        "--- EVENTOS ---",
        f"Riegos iniciados: {estadisticas['riego_iniciado']}",
        f"Riegos finalizados: {estadisticas['riego_finalizado']}",
        f"Desconexiones detectadas: {estadisticas['desconexiones']}",
        f"Reconexiones realizadas: {estadisticas['reconexiones']}",
        "",
        "--- RECURSOS DEL SISTEMA AL FINALIZAR ---",
    ]

    if recursos:
        lineas.extend([
            f"CPU total: {recursos['cpu_sistema']:.1f}%",
            f"RAM utilizada: {recursos['ram_sistema']:.1f}%",
            f"Disco ocupado: {recursos['disco_usado']:.1f}%",
            f"Disco libre: {recursos['disco_libre_gb']:.2f} GB",
            f"CPU del proceso Python: {recursos['cpu_proceso']:.1f}%",
            f"RAM del proceso Python: {recursos['ram_proceso_mb']:.2f} MB",
        ])
    else:
        lineas.append("No fue posible consultar los recursos del sistema.")

    lineas.extend([
        "",
        "--- RESULTADO ---",
        "La ejecución finalizó de forma controlada por el usuario.",
        "Los datos válidos fueron persistidos en MySQL y JSON.",
        "Los datos inválidos fueron rechazados y registrados como eventos.",
        "====================================================",
    ])

    with open(RUTA_REPORTE, "w", encoding="utf-8") as archivo:
        archivo.write("\n".join(lineas))

    print()
    print("[RF08] Reporte de ejecución generado:")
    print(RUTA_REPORTE)


# =====================================================
# PROGRAMA PRINCIPAL
# =====================================================

conexion = None
esp32 = None

estadisticas = {
    "inicio": datetime.now(),
    "telemetrias_recibidas": 0,
    "telemetrias_validas": 0,
    "datos_invalidos": 0,
    "json_invalidos": 0,
    "mysql_inserts": 0,
    "riego_iniciado": 0,
    "riego_finalizado": 0,
    "desconexiones": 0,
    "reconexiones": 0,
}

ultima_consulta_sistema = 0
ultimo_dato = time.time()

dispositivo_desconectado = False

proximo_intento_reconexion = 0


try:

    # -------------------------------------------------
    # MYSQL
    # -------------------------------------------------

    conexion = conectar_mysql()

    if conexion is None:

        raise SystemExit


    # -------------------------------------------------
    # PRIMERA CONEXIÓN ESP32
    # -------------------------------------------------

    esp32 = conectar_esp32()


    if esp32 is not None:

        print()
        print(
            "==================================="
        )
        print(
            " ESP32 CONECTADO"
        )
        print(
            "==================================="
        )
        print(
            f"Puerto: {PUERTO}"
        )
        print(
            f"Baudrate: {BAUDRATE}"
        )
        print()
        print(
            "Esperando telemetría..."
        )
        print()


        registrar_evento(
            conexion,
            DEVICE_ID,
            "INFO",
            "DEVICE_CONNECTED",
            "Puerto serial abierto correctamente"
        )

    else:

        print()
        print(
            "[RECONEXIÓN] ESP32 no disponible."
        )

        dispositivo_desconectado = True

        registrar_evento(
            conexion,
            DEVICE_ID,
            "ERROR",
            "DEVICE_DISCONNECTED",
            "Puerto COM3 no disponible al iniciar"
        )


    # =================================================
    # BUCLE PRINCIPAL
    # =================================================

    while True:

        tiempo_actual = time.time()


        # =============================================
        # RECURSOS DEL SISTEMA
        # =============================================

        if (
            tiempo_actual
            - ultima_consulta_sistema
            >= INTERVALO_SISTEMA
        ):

            mostrar_recursos_sistema()

            ultima_consulta_sistema = tiempo_actual


        # =============================================
        # SI ESP32 ESTÁ DESCONECTADO
        # =============================================

        if esp32 is None:

            if (
                tiempo_actual
                >= proximo_intento_reconexion
            ):

                print(
                    "[RECONEXIÓN] "
                    "Intentando conectar ESP32..."
                )

                nuevo_esp32 = conectar_esp32()


                if nuevo_esp32 is not None:

                    esp32 = nuevo_esp32

                    print()
                    print(
                        "[RECONEXIÓN] ESP32 conectado."
                    )

                    estadisticas["reconexiones"] += 1

                    registrar_evento(
                        conexion,
                        DEVICE_ID,
                        "INFO",
                        "DEVICE_CONNECTED",
                        "Comunicación restaurada"
                    )

                    dispositivo_desconectado = False

                    ultimo_dato = time.time()


                else:

                    print(
                        "[RECONEXIÓN] "
                        "ESP32 todavía no disponible."
                    )

                    proximo_intento_reconexion = (
                        time.time()
                        + INTERVALO_RECONEXION
                    )

            time.sleep(0.5)

            continue


        # =============================================
        # DETECTAR TIMEOUT DE COMUNICACIÓN
        # =============================================

        if (
            tiempo_actual - ultimo_dato
            > TIMEOUT_COMUNICACION
            and not dispositivo_desconectado
        ):

            print()
            print(
                "[ALERTA] No se reciben datos "
                "del ESP32."
            )

            estadisticas["desconexiones"] += 1

            registrar_evento(
                conexion,
                DEVICE_ID,
                "ERROR",
                "DEVICE_DISCONNECTED",
                "No se recibió telemetría durante 30 segundos"
            )

            dispositivo_desconectado = True


        # =============================================
        # LEER ESP32
        # =============================================

        try:

            if esp32.in_waiting > 0:

                linea = (
                    esp32.readline()
                    .decode(
                        "utf-8",
                        errors="replace"
                    )
                    .strip()
                )


                if not linea:

                    continue


                # -------------------------------------
                # Comunicación recuperada
                # -------------------------------------

                ultimo_dato = time.time()

                if dispositivo_desconectado:

                    print(
                        "[EVENTO] "
                        "Comunicación restaurada."
                    )

                    registrar_evento(
                        conexion,
                        DEVICE_ID,
                        "INFO",
                        "DEVICE_CONNECTED",
                        "Comunicación restaurada"
                    )

                    dispositivo_desconectado = False


                # -------------------------------------
                # Mensajes del firmware
                # -------------------------------------

                if not linea.startswith("DATA:"):

                    print(
                        f"[ESP32] {linea}"
                    )


                # -------------------------------------
                # Eventos de riego
                # -------------------------------------

                if (
                    "[EVENTO] RIEGO_INICIADO"
                    in linea
                ):

                    estadisticas["riego_iniciado"] += 1

                    registrar_evento(
                        conexion,
                        DEVICE_ID,
                        "INFO",
                        "RIEGO_INICIADO",
                        "Bomba activada por humedad baja"
                    )


                if (
                    "[EVENTO] RIEGO_FINALIZADO"
                    in linea
                ):

                    estadisticas["riego_finalizado"] += 1

                    registrar_evento(
                        conexion,
                        DEVICE_ID,
                        "INFO",
                        "RIEGO_FINALIZADO",
                        "Bomba apagada"
                    )


                # -------------------------------------
                # JSON
                # -------------------------------------

                if linea.startswith("DATA:"):

                    estadisticas["telemetrias_recibidas"] += 1

                    json_texto = linea[5:]

                    print()
                    print(
                        "[TELEMETRÍA] Datos recibidos:"
                    )
                    print(json_texto)


                    try:

                        datos = json.loads(
                            json_texto
                        )

                    except json.JSONDecodeError:

                        estadisticas["json_invalidos"] += 1

                        print(
                            "[ERROR] JSON inválido "
                            "recibido desde ESP32."
                        )

                        registrar_evento(
                            conexion,
                            DEVICE_ID,
                            "ERROR",
                            "INVALID_DATA",
                            "JSON inválido"
                        )

                        continue


                    datos_validos, resultado = (
                        validar_datos(datos)
                    )


                    if datos_validos:

                        estadisticas["telemetrias_validas"] += 1

                        print(
                            "[VALIDACIÓN] Datos válidos."
                        )

                        registrar_evento(
                            conexion,
                            datos["device_id"],
                            "INFO",
                            "TELEMETRIA_VALIDADA",
                            resultado
                        )

                        guardar_telemetria(
                            conexion,
                            datos
                        )

                        # Mantener un único archivo JSON con la
                        # telemetría válida más reciente.
                        guardar_json(datos)

                    else:

                        estadisticas["datos_invalidos"] += 1

                        print(
                            "[VALIDACIÓN] "
                            "Datos rechazados."
                        )

                        registrar_evento(
                            conexion,
                            datos.get(
                                "device_id",
                                DEVICE_ID
                            ),
                            "ERROR",
                            "INVALID_DATA",
                            resultado
                        )


        # =============================================
        # FALLO FÍSICO DEL PUERTO
        # =============================================

        except (
            serial.SerialException,
            PermissionError,
            OSError
        ) as error:

            print()
            print(
                "ERROR DE COMUNICACIÓN CON EL ESP32"
            )
            print(error)


            # Registrar el fallo una sola vez
            if not dispositivo_desconectado:

                estadisticas["desconexiones"] += 1

                registrar_evento(
                    conexion,
                    DEVICE_ID,
                    "ERROR",
                    "DEVICE_DISCONNECTED",
                    f"Error serial: {error}"
                )


            dispositivo_desconectado = True


            # Cerrar objeto serial actual
            try:

                if esp32 is not None:

                    if esp32.is_open:

                        esp32.close()

            except Exception:

                pass


            esp32 = None

            proximo_intento_reconexion = (
                time.time()
                + INTERVALO_RECONEXION
            )


            print(
                "[RECONEXIÓN] "
                "Python continuará ejecutándose."
            )

            print(
                "[RECONEXIÓN] "
                "Próximo intento en 5 segundos."
            )


            time.sleep(1)


except KeyboardInterrupt:

    print()
    print(
        "Programa detenido por el usuario."
    )


except mysql.connector.Error as error:

    print()
    print(
        "ERROR DE MYSQL"
    )
    print(error)


except Exception as error:

    print()
    print(
        "ERROR NO CONTROLADO"
    )
    print(error)


finally:

    try:
        generar_reporte_ejecucion()
    except Exception as error:
        print("[RF08] No se pudo generar el reporte de ejecución.")
        print(error)

    if esp32 is not None:

        try:

            if esp32.is_open:

                esp32.close()

        except Exception:

            pass


    if conexion is not None:

        try:

            if conexion.is_connected():

                conexion.close()

        except Exception:

            pass


    print()
    print(
        "Conexiones cerradas."
    )
