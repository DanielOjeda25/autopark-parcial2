# re permite comprobar si un texto cumple un patrón determinado.
import re


# Tipos de vehículos aceptados por el sistema y presentes en tarifas.json.
TIPOS_VEHICULO = {"moto", "auto", "camioneta"}


class ErrorValidacion(ValueError):
    """Error controlado para datos ingresados con formato o valores inválidos."""


def normalizar_patente(patente):
    """Elimina espacios y convierte la patente a mayúsculas."""
    # Si recibimos algo que no es texto, devolvemos vacío para poder rechazarlo.
    if not isinstance(patente, str):
        return ""

    # \s incluye espacios, tabulaciones y saltos de línea.
    return re.sub(r"\s+", "", patente).upper()


def validar_patente(patente):
    """Acepta patentes tradicionales AAA000 y Mercosur AA000AA."""
    patente_normalizada = normalizar_patente(patente)

    patron_tradicional = r"[A-Z]{3}[0-9]{3}"
    patron_mercosur = r"[A-Z]{2}[0-9]{3}[A-Z]{2}"

    return bool(
        re.fullmatch(patron_tradicional, patente_normalizada)
        or re.fullmatch(patron_mercosur, patente_normalizada)
    )


def normalizar_tipo_vehiculo(tipo_vehiculo):
    """Quita espacios y convierte el tipo de vehículo a minúsculas."""
    if not isinstance(tipo_vehiculo, str):
        return ""

    return tipo_vehiculo.strip().lower()


def validar_tipo_vehiculo(tipo_vehiculo):
    """Comprueba que el vehículo sea moto, auto o camioneta."""
    return normalizar_tipo_vehiculo(tipo_vehiculo) in TIPOS_VEHICULO


def validar_hora(hora):
    """Comprueba que una hora tenga formato estricto HH:MM de 00:00 a 23:59."""
    if not isinstance(hora, str):
        return False

    # [01][0-9] acepta de 00 a 19 y 2[0-3] acepta de 20 a 23.
    patron_hora = r"(?:[01][0-9]|2[0-3]):[0-5][0-9]"
    return re.fullmatch(patron_hora, hora.strip()) is not None


def hora_a_minutos(hora):
    """Convierte una hora válida, por ejemplo 08:30, a minutos desde medianoche."""
    if not validar_hora(hora):
        raise ErrorValidacion("La hora debe tener el formato HH:MM, por ejemplo 08:30.")

    horas, minutos = hora.strip().split(":")
    return int(horas) * 60 + int(minutos)


def convertir_dias(dias):
    """Convierte los días a entero y rechaza negativos, decimales o texto."""
    # bool hereda de int en Python; lo rechazamos de manera explícita.
    if isinstance(dias, bool):
        raise ErrorValidacion("La cantidad de días debe ser un número entero.")

    texto_dias = str(dias).strip()

    if not re.fullmatch(r"[0-9]+", texto_dias):
        raise ErrorValidacion("Los días deben ser un número entero igual o mayor que cero.")

    return int(texto_dias)


def validar_lavado(lavado):
    """Comprueba que lavado sea un valor booleano verdadero o falso."""
    return isinstance(lavado, bool)


def validar_datos_liquidacion(
    patente,
    tipo_vehiculo,
    hora_entrada,
    hora_salida,
    dias,
    lavado,
):
    """Valida y normaliza todos los datos de una liquidación manual."""
    patente_normalizada = normalizar_patente(patente)
    tipo_normalizado = normalizar_tipo_vehiculo(tipo_vehiculo)
    dias_convertidos = convertir_dias(dias)

    if not patente_normalizada:
        raise ErrorValidacion("La patente es obligatoria.")

    if not validar_patente(patente_normalizada):
        raise ErrorValidacion(
            "La patente debe tener formato ABC123 o AB123CD."
        )

    if not validar_tipo_vehiculo(tipo_normalizado):
        raise ErrorValidacion("El tipo debe ser moto, auto o camioneta.")

    if not validar_lavado(lavado):
        raise ErrorValidacion("El valor de lavado debe ser verdadero o falso.")

    entrada_normalizada = hora_entrada.strip() if isinstance(hora_entrada, str) else ""
    salida_normalizada = hora_salida.strip() if isinstance(hora_salida, str) else ""

    if dias_convertidos == 0:
        # En una estadía del mismo día ambas horas son obligatorias.
        if not entrada_normalizada or not salida_normalizada:
            raise ErrorValidacion(
                "Para una estadía del mismo día debes completar entrada y salida."
            )

        minutos_entrada = hora_a_minutos(entrada_normalizada)
        minutos_salida = hora_a_minutos(salida_normalizada)

        if minutos_salida <= minutos_entrada:
            raise ErrorValidacion(
                "La hora de salida debe ser posterior a la hora de entrada."
            )
    else:
        # Para días completos el enunciado indica que no se utiliza hora de salida.
        if salida_normalizada:
            raise ErrorValidacion(
                "No debes ingresar hora de salida cuando hay días completos."
            )

        # La entrada es opcional en este caso, pero si se escribe debe ser válida.
        if entrada_normalizada:
            hora_a_minutos(entrada_normalizada)

    # Entregamos datos limpios para que los cálculos no tengan que normalizarlos.
    return {
        "patente": patente_normalizada,
        "tipo_vehiculo": tipo_normalizado,
        "hora_entrada": entrada_normalizada,
        "hora_salida": salida_normalizada,
        "dias": dias_convertidos,
        "lavado": lavado,
    }


def validar_movimiento(movimiento):
    """Valida un movimiento del JSON y devuelve una copia normalizada."""
    if not isinstance(movimiento, dict):
        raise ErrorValidacion("El movimiento debe ser un objeto JSON.")

    campos_obligatorios = {
        "id",
        "patente",
        "tipo_vehiculo",
        "hora_entrada",
        "hora_salida",
        "lavado",
    }
    campos_faltantes = campos_obligatorios - movimiento.keys()

    if campos_faltantes:
        lista_campos = ", ".join(sorted(campos_faltantes))
        raise ErrorValidacion(f"Faltan campos obligatorios: {lista_campos}.")

    identificador = movimiento["id"]
    if not isinstance(identificador, str) or not identificador.strip():
        raise ErrorValidacion("El identificador del movimiento es obligatorio.")

    datos = validar_datos_liquidacion(
        movimiento["patente"],
        movimiento["tipo_vehiculo"],
        movimiento["hora_entrada"],
        movimiento["hora_salida"],
        0,
        movimiento["lavado"],
    )
    datos["id"] = identificador.strip()
    return datos
