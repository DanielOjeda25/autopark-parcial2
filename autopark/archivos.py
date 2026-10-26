# csv permite guardar las liquidaciones en filas y columnas.
import csv
# json transforma el contenido JSON en diccionarios y listas de Python.
import json
# datetime permite comprobar que una fecha tenga formato y valores reales.
from datetime import datetime
# Path crea rutas que funcionan aunque el proyecto esté en otra computadora.
from pathlib import Path


# Ubicaciones principales del proyecto.
CARPETA_AUTOPARK = Path(__file__).resolve().parent
CARPETA_PROYECTO = CARPETA_AUTOPARK.parent
CARPETA_DATOS = CARPETA_PROYECTO / "datos"
CARPETA_REPORTES = CARPETA_PROYECTO / "reportes"

# No usamos rutas absolutas para que el proyecto sea transportable.
RUTA_TARIFAS = CARPETA_DATOS / "tarifas.json"
RUTA_MOVIMIENTOS = CARPETA_DATOS / "movimientos.json"
RUTA_LIQUIDACION_MANUAL = CARPETA_REPORTES / "liquidacion-manual.csv"
RUTA_LIQUIDACION_LOTE = CARPETA_REPORTES / "liquidacion.csv"
RUTA_RECHAZADOS = CARPETA_REPORTES / "rechazados.csv"

# Evita intentar cargar por accidente un archivo exageradamente grande.
TAMANIO_MAXIMO_BYTES = 10 * 1024 * 1024


class ErrorArchivoDatos(Exception):
    """Error controlado para problemas al leer o validar archivos de datos."""


def cargar_json(ruta_archivo):
    """Lee un JSON y convierte errores técnicos en mensajes comprensibles."""
    ruta = Path(ruta_archivo)

    try:
        if not ruta.is_file():
            raise ErrorArchivoDatos(f"No se encontró el archivo {ruta.name}.")

        if ruta.stat().st_size == 0:
            raise ErrorArchivoDatos(f"El archivo {ruta.name} está vacío.")

        if ruta.stat().st_size > TAMANIO_MAXIMO_BYTES:
            raise ErrorArchivoDatos(f"El archivo {ruta.name} es demasiado grande.")

        # utf-8 permite leer correctamente tildes, eñes y otros caracteres.
        with ruta.open("r", encoding="utf-8") as archivo:
            return json.load(archivo)

    except json.JSONDecodeError as error:
        raise ErrorArchivoDatos(
            f"{ruta.name} contiene JSON inválido en la línea {error.lineno}, "
            f"columna {error.colno}."
        ) from error
    except UnicodeDecodeError as error:
        raise ErrorArchivoDatos(
            f"{ruta.name} no está guardado con codificación UTF-8."
        ) from error
    except PermissionError as error:
        raise ErrorArchivoDatos(
            f"No tienes permiso para leer {ruta.name}."
        ) from error
    except OSError as error:
        raise ErrorArchivoDatos(
            f"No se pudo leer {ruta.name}: {error}."
        ) from error


def _es_numero_no_negativo(valor):
    """Acepta enteros o decimales no negativos, pero rechaza booleanos."""
    return not isinstance(valor, bool) and isinstance(valor, (int, float)) and valor >= 0


def validar_estructura_tarifas(datos):
    """Comprueba la estructura y los valores indispensables de tarifas.json."""
    if not isinstance(datos, dict):
        raise ErrorArchivoDatos("La raíz de tarifas.json debe ser un objeto JSON.")

    configuracion = datos.get("configuracion")
    tarifas = datos.get("tarifas")

    if not isinstance(configuracion, dict):
        raise ErrorArchivoDatos("Falta el objeto 'configuracion' en tarifas.json.")

    if not isinstance(tarifas, dict):
        raise ErrorArchivoDatos("Falta el objeto 'tarifas' en tarifas.json.")

    campos_configuracion = {
        "minutos_bloque_inicial",
        "minutos_limite_primer_tramo",
        "minutos_hora_adicional",
        "minutos_dia_completo",
    }

    for campo in campos_configuracion:
        valor = configuracion.get(campo)
        if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
            raise ErrorArchivoDatos(
                f"La configuración '{campo}' debe ser un entero mayor que cero."
            )

    campos_tarifa = {
        "precio_bloque_30min",
        "precio_hora_adicional",
        "tope_dia",
        "precio_lavado",
    }

    for tipo in ("moto", "auto", "camioneta"):
        tarifa = tarifas.get(tipo)
        if not isinstance(tarifa, dict):
            raise ErrorArchivoDatos(f"Falta la tarifa correspondiente a '{tipo}'.")

        for campo in campos_tarifa:
            if campo not in tarifa:
                raise ErrorArchivoDatos(f"Falta '{campo}' en la tarifa de {tipo}.")

            if not _es_numero_no_negativo(tarifa[campo]):
                raise ErrorArchivoDatos(
                    f"'{campo}' de {tipo} debe ser un número igual o mayor que cero."
                )

    return datos


def validar_estructura_movimientos(datos):
    """Valida el contenedor del archivo sin descartar movimientos individuales."""
    if not isinstance(datos, dict):
        raise ErrorArchivoDatos(
            "La raíz de movimientos.json debe ser un objeto JSON."
        )

    fecha = datos.get("fecha_operacion")
    movimientos = datos.get("movimientos")

    if not isinstance(fecha, str):
        raise ErrorArchivoDatos("Falta una fecha de operación válida.")

    try:
        # strptime también detecta fechas imposibles, por ejemplo 2026-02-30.
        datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError as error:
        raise ErrorArchivoDatos(
            "La fecha de operación debe tener formato AAAA-MM-DD y ser real."
        ) from error

    if not isinstance(movimientos, list):
        raise ErrorArchivoDatos("'movimientos' debe contener una lista JSON.")

    return datos


def cargar_tarifas():
    """Carga tarifas.json y rechaza el archivo si su estructura es incorrecta."""
    return validar_estructura_tarifas(cargar_json(RUTA_TARIFAS))


def cargar_movimientos():
    """Carga movimientos.json y valida su estructura general."""
    return validar_estructura_movimientos(cargar_json(RUTA_MOVIMIENTOS))


def guardar_liquidacion_manual(resultado, ruta_archivo=RUTA_LIQUIDACION_MANUAL):
    """Agrega una liquidación al CSV sin eliminar los registros anteriores."""
    ruta = Path(ruta_archivo)

    # Si la carpeta de reportes fue eliminada, la recreamos automáticamente.
    ruta.parent.mkdir(parents=True, exist_ok=True)

    # Estas columnas mantienen siempre el mismo orden dentro del archivo.
    columnas = [
        "fecha_registro",
        "patente",
        "tipo_vehiculo",
        "hora_entrada",
        "hora_salida",
        "dias",
        "minutos_estadia",
        "lavado",
        "importe_base",
        "bonificacion",
        "costo_estacionamiento",
        "costo_lavado",
        "total",
    ]

    # Comprobamos si debemos escribir los encabezados antes de abrir el archivo.
    escribir_encabezado = not ruta.exists() or ruta.stat().st_size == 0

    # Creamos una copia para no modificar el resultado original del cálculo.
    fila = resultado.copy()
    fila["fecha_registro"] = datetime.now().isoformat(timespec="seconds")

    # CSV utiliza textos claros para los booleanos, facilitando su lectura.
    fila["lavado"] = "Sí" if resultado["lavado"] else "No"

    try:
        # newline vacío evita filas en blanco adicionales en Windows.
        # El modo "a" agrega al final y nunca borra las filas existentes.
        with ruta.open("a", encoding="utf-8", newline="") as archivo:
            escritor = csv.DictWriter(
                archivo,
                fieldnames=columnas,
                extrasaction="ignore",
            )

            if escribir_encabezado:
                escritor.writeheader()

            escritor.writerow(fila)

    except PermissionError as error:
        # Suele ocurrir cuando el CSV está abierto y bloqueado por otro programa.
        raise ErrorArchivoDatos(
            f"No se pudo guardar {ruta.name}. Ciérralo si está abierto e intenta nuevamente."
        ) from error
    except OSError as error:
        raise ErrorArchivoDatos(
            f"No se pudo escribir {ruta.name}: {error}."
        ) from error

    # Devolvemos la ruta para que la interfaz pueda informar dónde se guardó.
    return ruta


def guardar_reporte_csv(ruta_archivo, columnas, filas):
    """Reemplaza un reporte CSV de forma segura y conserva sus encabezados."""
    ruta = Path(ruta_archivo)

    # Garantiza que los reportes puedan generarse también en una copia nueva.
    ruta.parent.mkdir(parents=True, exist_ok=True)

    # Escribimos primero un archivo temporal para no dejar un reporte incompleto
    # si ocurre un problema durante el guardado.
    ruta_temporal = ruta.with_suffix(f"{ruta.suffix}.tmp")

    try:
        with ruta_temporal.open("w", encoding="utf-8", newline="") as archivo:
            escritor = csv.DictWriter(
                archivo,
                fieldnames=columnas,
                extrasaction="ignore",
            )
            escritor.writeheader()
            escritor.writerows(filas)

        # replace cambia el reporte anterior únicamente cuando el nuevo terminó.
        ruta_temporal.replace(ruta)

    except PermissionError as error:
        raise ErrorArchivoDatos(
            f"No se pudo guardar {ruta.name}. Ciérralo si está abierto e intenta nuevamente."
        ) from error
    except OSError as error:
        raise ErrorArchivoDatos(
            f"No se pudo escribir {ruta.name}: {error}."
        ) from error

    return ruta


def _leer_liquidaciones_csv(ruta_archivo, origen):
    """Lee un CSV de liquidaciones y adapta sus filas al historial común."""
    ruta = Path(ruta_archivo)

    # Un reporte todavía no generado representa un historial vacío, no un error.
    if not ruta.exists() or ruta.stat().st_size == 0:
        return []

    campos_obligatorios = {
        "patente",
        "tipo_vehiculo",
        "dias",
        "minutos_estadia",
        "lavado",
        "total",
    }

    try:
        with ruta.open("r", encoding="utf-8", newline="") as archivo:
            lector = csv.DictReader(archivo)
            encabezados = set(lector.fieldnames or [])
            faltantes = campos_obligatorios - encabezados

            if faltantes:
                lista = ", ".join(sorted(faltantes))
                raise ErrorArchivoDatos(
                    f"{ruta.name} no contiene las columnas requeridas: {lista}."
                )

            registros = []
            for numero_fila, fila in enumerate(lector, start=1):
                try:
                    dias = int(fila["dias"])
                    minutos = int(fila["minutos_estadia"])
                    total = float(fila["total"])
                except (TypeError, ValueError) as error:
                    raise ErrorArchivoDatos(
                        f"{ruta.name} contiene números inválidos en la fila {numero_fila + 1}."
                    ) from error

                # Para días completos convertimos la duración a minutos para
                # poder calcular un promedio comparable entre estadías.
                duracion_minutos = minutos if dias == 0 else dias * 1440

                registros.append(
                    {
                        "fecha": fila.get("fecha_registro")
                        or fila.get("fecha_operacion")
                        or "",
                        "id": fila.get("id") or f"MANUAL-{numero_fila:04d}",
                        "patente": fila["patente"],
                        "tipo_vehiculo": fila["tipo_vehiculo"],
                        "dias": dias,
                        "minutos_estadia": minutos,
                        "duracion_minutos": duracion_minutos,
                        "lavado": fila["lavado"],
                        "total": total,
                        "origen": origen,
                    }
                )

            return registros

    except UnicodeDecodeError as error:
        raise ErrorArchivoDatos(f"{ruta.name} no está guardado en UTF-8.") from error
    except csv.Error as error:
        raise ErrorArchivoDatos(f"{ruta.name} contiene un CSV inválido: {error}.") from error
    except PermissionError as error:
        raise ErrorArchivoDatos(f"No se pudo leer {ruta.name}.") from error
    except OSError as error:
        raise ErrorArchivoDatos(f"No se pudo leer {ruta.name}: {error}.") from error


def cargar_historial_liquidaciones(
    ruta_manual=RUTA_LIQUIDACION_MANUAL,
    ruta_lote=RUTA_LIQUIDACION_LOTE,
):
    """Consolida operaciones manuales y del lote en una sola colección."""
    manuales = _leer_liquidaciones_csv(
        ruta_manual,
        "Manual",
    )
    lote = _leer_liquidaciones_csv(
        ruta_lote,
        "Lote",
    )

    return manuales + lote
