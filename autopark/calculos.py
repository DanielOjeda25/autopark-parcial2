from validaciones import hora_a_minutos


def calcular_estacionamiento_recursivo(
    minutos_restantes,
    tipo_vehiculo,
    datos_tarifas,
    minutos_cobrados=0,
):
    """
    Calcula el costo del estacionamiento utilizando recursividad.

    Los primeros 120 minutos se cobran en bloques de 30 minutos.
    Después se cobran bloques de 60 minutos o fracción.
    """
    # Caso base: cuando no quedan minutos por cobrar termina la recursión.
    # Sin este caso, la función continuaría llamándose indefinidamente.
    if minutos_restantes <= 0:
        return 0

    # Obtenemos la configuración general almacenada en tarifas.json.
    configuracion = datos_tarifas["configuracion"]

    # Seleccionamos únicamente los precios del tipo de vehículo recibido.
    tarifa_vehiculo = datos_tarifas["tarifas"][tipo_vehiculo]

    # Duración en minutos de cada bloque perteneciente al primer tramo.
    minutos_bloque = configuracion["minutos_bloque_inicial"]

    # Cantidad máxima de minutos cobrados con bloques iniciales.
    limite_inicial = configuracion["minutos_limite_primer_tramo"]

    # Duración de cada bloque cobrado como hora adicional.
    minutos_adicionales = configuracion["minutos_hora_adicional"]

    # Durante los primeros 120 minutos cobramos bloques de 30 minutos.
    if minutos_cobrados < limite_inicial:
        precio_bloque = tarifa_vehiculo["precio_bloque_30min"]

        # Paso recursivo: sumamos un bloque y volvemos a llamar a la función
        # con una cantidad menor de minutos pendientes.
        return precio_bloque + calcular_estacionamiento_recursivo(
            minutos_restantes - minutos_bloque,
            tipo_vehiculo,
            datos_tarifas,
            minutos_cobrados + minutos_bloque,
        )

    # Después del primer tramo cobramos bloques de una hora o fracción.
    precio_hora = tarifa_vehiculo["precio_hora_adicional"]

    # Paso recursivo correspondiente a las horas adicionales.
    return precio_hora + calcular_estacionamiento_recursivo(
        minutos_restantes - minutos_adicionales,
        tipo_vehiculo,
        datos_tarifas,
        minutos_cobrados + minutos_adicionales,
    )


def calcular_minutos_estadia(hora_entrada, hora_salida):
    """Calcula los minutos transcurridos entre dos horas del mismo día."""
    # hora_a_minutos convierte, por ejemplo, 08:30 en 510 minutos.
    minutos_entrada = hora_a_minutos(hora_entrada)
    minutos_salida = hora_a_minutos(hora_salida)

    # La validación previa garantiza que la salida sea posterior a la entrada.
    return minutos_salida - minutos_entrada


def calcular_liquidacion(datos, datos_tarifas):
    """Calcula estacionamiento, lavado y total de una liquidación validada."""
    # Recuperamos los datos ya normalizados por validaciones.py.
    tipo_vehiculo = datos["tipo_vehiculo"]
    dias = datos["dias"]
    tiene_lavado = datos["lavado"]

    # Seleccionamos los precios correspondientes al vehículo.
    tarifa_vehiculo = datos_tarifas["tarifas"][tipo_vehiculo]
    tope_dia = tarifa_vehiculo["tope_dia"]
    precio_lavado = tarifa_vehiculo["precio_lavado"]

    # Inicializamos los importes para cubrir también los casos sin lavado.
    importe_base = 0
    bonificacion = 0
    costo_estacionamiento = 0
    costo_lavado = 0
    minutos_estadia = 0

    if dias > 0:
        # Una estadía de varios días cobra un tope diario por cada día.
        importe_base = dias * tope_dia
        costo_estacionamiento = importe_base

        # El lavado se cobra una sola vez, aunque la estadía dure varios días.
        if tiene_lavado:
            costo_lavado = precio_lavado

    else:
        # Para una estadía del mismo día calculamos la diferencia horaria.
        minutos_estadia = calcular_minutos_estadia(
            datos["hora_entrada"],
            datos["hora_salida"],
        )

        # El importe base representa cuánto costaría normalmente la estadía
        # antes de aplicar la bonificación correspondiente al lavado.
        importe_base_sin_tope = calcular_estacionamiento_recursivo(
            minutos_estadia,
            tipo_vehiculo,
            datos_tarifas,
        )
        importe_base = min(importe_base_sin_tope, tope_dia)

        if tiene_lavado:
            # El lavado incluye las primeras dos horas de estacionamiento.
            costo_lavado = precio_lavado

            if minutos_estadia > 120:
                # Solo cobramos como estacionamiento el tiempo posterior a 120.
                minutos_excedentes = minutos_estadia - 120

                # minutos_cobrados=120 hace que la recursión comience
                # directamente en el tramo de horas adicionales.
                costo_estacionamiento = calcular_estacionamiento_recursivo(
                    minutos_excedentes,
                    tipo_vehiculo,
                    datos_tarifas,
                    minutos_cobrados=120,
                )
                costo_estacionamiento = min(costo_estacionamiento, tope_dia)

            # La bonificación es la parte del importe base que no se cobra.
            # Se calcula después del tope para que el desglose sea conciliable:
            # base - bonificación + lavado = total.
            bonificacion = max(importe_base - costo_estacionamiento, 0)
        else:
            # Sin lavado se cobra el importe base ya limitado por el tope diario.
            costo_estacionamiento = importe_base

    costo_total = costo_estacionamiento + costo_lavado

    # Devolvemos un diccionario para facilitar su uso en la interfaz y el CSV.
    return {
        "patente": datos["patente"],
        "tipo_vehiculo": tipo_vehiculo,
        "hora_entrada": datos["hora_entrada"],
        "hora_salida": datos["hora_salida"],
        "dias": dias,
        "minutos_estadia": minutos_estadia,
        "lavado": tiene_lavado,
        "importe_base": importe_base,
        "bonificacion": bonificacion,
        "costo_estacionamiento": costo_estacionamiento,
        "costo_lavado": costo_lavado,
        "total": costo_total,
    }


# Este bloque permite probar el archivo directamente.
# No se ejecutará cuando calculos.py sea importado desde otro módulo.
if __name__ == "__main__":
    # Importamos aquí para que la función principal no dependa de archivos.
    from archivos import cargar_tarifas

    tarifas = cargar_tarifas()

    costo_25 = calcular_estacionamiento_recursivo(25, "auto", tarifas)
    costo_120 = calcular_estacionamiento_recursivo(120, "auto", tarifas)
    costo_150 = calcular_estacionamiento_recursivo(150, "auto", tarifas)

    print("Auto durante 25 minutos:", costo_25)
    print("Auto durante 120 minutos:", costo_120)
    print("Auto durante 150 minutos:", costo_150)
