# Este módulo coordina la lectura, validación, liquidación y exportación del lote.

from archivos import (
    RUTA_LIQUIDACION_LOTE,
    RUTA_RECHAZADOS,
    cargar_movimientos,
    cargar_tarifas,
    guardar_reporte_csv,
)
from calculos import calcular_liquidacion
from validaciones import ErrorValidacion, validar_movimiento


# Orden de columnas del reporte con movimientos procesados correctamente.
COLUMNAS_LIQUIDACION = [
    "fecha_operacion",
    "id",
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

# El reporte de rechazados conserva los datos originales y agrega el motivo.
COLUMNAS_RECHAZADOS = [
    "fecha_operacion",
    "numero_fila",
    "id",
    "patente",
    "tipo_vehiculo",
    "hora_entrada",
    "hora_salida",
    "lavado",
    "motivo",
]


def crear_fila_rechazada(fecha_operacion, numero_fila, movimiento, motivo):
    """Prepara una fila legible para rechazados.csv."""
    # Un elemento que no es diccionario tampoco permite utilizar get.
    if not isinstance(movimiento, dict):
        return {
            "fecha_operacion": fecha_operacion,
            "numero_fila": numero_fila,
            "id": "",
            "patente": "",
            "tipo_vehiculo": "",
            "hora_entrada": "",
            "hora_salida": "",
            "lavado": "",
            "motivo": motivo,
        }

    return {
        "fecha_operacion": fecha_operacion,
        "numero_fila": numero_fila,
        "id": movimiento.get("id", ""),
        "patente": movimiento.get("patente", ""),
        "tipo_vehiculo": movimiento.get("tipo_vehiculo", ""),
        "hora_entrada": movimiento.get("hora_entrada", ""),
        "hora_salida": movimiento.get("hora_salida", ""),
        "lavado": movimiento.get("lavado", ""),
        "motivo": motivo,
    }


def procesar_lote(
    datos_tarifas=None,
    datos_movimientos=None,
    ruta_liquidacion=RUTA_LIQUIDACION_LOTE,
    ruta_rechazados=RUTA_RECHAZADOS,
):
    """Procesa todos los movimientos y genera los dos reportes CSV."""
    # Los parámetros opcionales facilitan las pruebas sin modificar archivos.
    if datos_tarifas is None:
        datos_tarifas = cargar_tarifas()

    if datos_movimientos is None:
        datos_movimientos = cargar_movimientos()

    fecha_operacion = datos_movimientos["fecha_operacion"]
    movimientos = datos_movimientos["movimientos"]

    liquidaciones = []
    rechazados = []
    identificadores_vistos = set()

    # enumerate permite registrar la posición exacta del movimiento rechazado.
    for numero_fila, movimiento in enumerate(movimientos, start=1):
        try:
            movimiento_validado = validar_movimiento(movimiento)
            identificador = movimiento_validado["id"]

            # Un identificador duplicado podría producir cobros repetidos.
            if identificador in identificadores_vistos:
                raise ErrorValidacion(
                    f"El identificador {identificador} está duplicado."
                )

            identificadores_vistos.add(identificador)

            resultado = calcular_liquidacion(
                movimiento_validado,
                datos_tarifas,
            )
            resultado["fecha_operacion"] = fecha_operacion
            resultado["id"] = identificador
            resultado["lavado"] = "Sí" if resultado["lavado"] else "No"
            liquidaciones.append(resultado)

        except ErrorValidacion as error:
            rechazados.append(
                crear_fila_rechazada(
                    fecha_operacion,
                    numero_fila,
                    movimiento,
                    str(error),
                )
            )
        except (KeyError, TypeError, RecursionError) as error:
            # Un problema de estructura individual también se registra sin
            # interrumpir el resto del lote.
            rechazados.append(
                crear_fila_rechazada(
                    fecha_operacion,
                    numero_fila,
                    movimiento,
                    f"Datos incompatibles para calcular: {error}",
                )
            )

    # Los reportes del lote se reemplazan en cada ejecución.
    ruta_liquidacion = guardar_reporte_csv(
        ruta_liquidacion,
        COLUMNAS_LIQUIDACION,
        liquidaciones,
    )
    ruta_rechazados = guardar_reporte_csv(
        ruta_rechazados,
        COLUMNAS_RECHAZADOS,
        rechazados,
    )

    total_recaudado = sum(fila["total"] for fila in liquidaciones)

    resumen = {
        "procesados": len(liquidaciones),
        "rechazados": len(rechazados),
        "total_recaudado": total_recaudado,
        "ruta_liquidacion": ruta_liquidacion,
        "ruta_rechazados": ruta_rechazados,
    }

    # El enunciado solicita mostrar también un resumen en la consola.
    print("\n=== RESUMEN DEL PROCESAMIENTO ===")
    print(f"Procesados: {resumen['procesados']}")
    print(f"Rechazados: {resumen['rechazados']}")
    print(f"Total recaudado: ${resumen['total_recaudado']}")

    return resumen
