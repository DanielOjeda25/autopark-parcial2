# Tkinter permite crear ventanas y variables asociadas a los controles.
import tkinter as tk
# messagebox muestra avisos; ttk aporta componentes con estilos modernos.
from tkinter import messagebox, ttk

# La interfaz solicita los datos externos y el cálculo, pero no contiene
# reglas de negocio. Esto mantiene cada responsabilidad en su propio archivo.
from archivos import ErrorArchivoDatos, cargar_tarifas, guardar_liquidacion_manual
from calculos import calcular_liquidacion
# procesamiento coordina la lectura y exportación masiva de movimientos.
from procesamiento import procesar_lote
# Importamos el error controlado y la validación completa del formulario.
from validaciones import ErrorValidacion, validar_datos_liquidacion


class BotonRedondeado(tk.Canvas):
    """Botón reutilizable con esquinas redondeadas y efecto al pasar el mouse."""

    def __init__(
        self,
        contenedor,
        texto,
        comando,
        color="#2563eb",
        color_activo="#1d4ed8",
        color_texto="white",
        ancho=220,
        alto=48,
        radio=14,
    ):
        # Tomamos el fondo del contenedor para ocultar las esquinas del Canvas.
        fondo_contenedor = contenedor.cget("background")
        super().__init__(
            contenedor,
            width=ancho,
            height=alto,
            background=fondo_contenedor,
            highlightthickness=0,
            borderwidth=0,
            cursor="hand2",
            takefocus=True,
        )

        self.comando = comando
        self.color = color
        self.color_activo = color_activo

        # Dos rectángulos y cuatro círculos forman un rectángulo redondeado.
        self.create_rectangle(
            radio, 0, ancho - radio, alto, fill=color, outline=color, tags="fondo"
        )
        self.create_rectangle(
            0, radio, ancho, alto - radio, fill=color, outline=color, tags="fondo"
        )
        self.create_oval(
            0, 0, radio * 2, radio * 2, fill=color, outline=color, tags="fondo"
        )
        self.create_oval(
            ancho - radio * 2,
            0,
            ancho,
            radio * 2,
            fill=color,
            outline=color,
            tags="fondo",
        )
        self.create_oval(
            0,
            alto - radio * 2,
            radio * 2,
            alto,
            fill=color,
            outline=color,
            tags="fondo",
        )
        self.create_oval(
            ancho - radio * 2,
            alto - radio * 2,
            ancho,
            alto,
            fill=color,
            outline=color,
            tags="fondo",
        )

        self.create_text(
            ancho / 2,
            alto / 2,
            text=texto,
            fill=color_texto,
            font=("Segoe UI", 10, "bold"),
            tags="texto",
        )

        # Todo el Canvas responde al mouse y también a Enter o Espacio.
        self.bind("<Enter>", self._activar)
        self.bind("<Leave>", self._desactivar)
        self.bind("<Button-1>", self._ejecutar)
        self.bind("<Return>", self._ejecutar)
        self.bind("<space>", self._ejecutar)

    def _activar(self, evento=None):
        """Cambia el color cuando el puntero está sobre el botón."""
        self.itemconfigure("fondo", fill=self.color_activo, outline=self.color_activo)

    def _desactivar(self, evento=None):
        """Recupera el color normal cuando sale el puntero."""
        self.itemconfigure("fondo", fill=self.color, outline=self.color)

    def _ejecutar(self, evento=None):
        """Ejecuta la acción asociada al botón."""
        self.focus_set()
        if self.comando is not None:
            self.comando()


def centrar_ventana(ventana):
    """Coloca una ventana exactamente en el centro de la pantalla."""
    # Actualiza las medidas para que Tkinter conozca el tamaño real de la ventana.
    ventana.update_idletasks()

    # Obtenemos el ancho y el alto que ya fueron definidos con geometry.
    ancho_ventana = ventana.winfo_width()
    alto_ventana = ventana.winfo_height()

    # Consultamos las dimensiones completas de la pantalla del usuario.
    ancho_pantalla = ventana.winfo_screenwidth()
    alto_pantalla = ventana.winfo_screenheight()

    # Calculamos la esquina superior izquierda necesaria para centrarla.
    posicion_x = (ancho_pantalla - ancho_ventana) // 2
    posicion_y = (alto_pantalla - alto_ventana) // 2

    # Conservamos su tamaño y cambiamos únicamente su posición en la pantalla.
    ventana.geometry(
        f"{ancho_ventana}x{alto_ventana}+{posicion_x}+{posicion_y}"
    )


def formatear_importe(importe):
    """Convierte 16000 en un texto más legible, por ejemplo $16.000."""
    return f"${importe:,.0f}".replace(",", ".")


def crear_selector_hora(contenedor):
    """Crea selectores separados para hora y minuto sin permitir texto libre."""
    marco = tk.Frame(contenedor, background="white")

    # StringVar conserva el valor seleccionado en cada Spinbox.
    hora = tk.StringVar(value="00")
    minuto = tk.StringVar(value="00")

    # Las horas posibles van de 00 a 23.
    selector_hora = ttk.Spinbox(
        marco,
        values=[f"{numero:02d}" for numero in range(24)],
        textvariable=hora,
        width=4,
        state="readonly",
        wrap=True,
        justify="center",
        style="Hora.TSpinbox",
    )
    selector_hora.pack(side="left", fill="x", expand=True)

    # Los dos puntos separan visualmente horas y minutos.
    tk.Label(
        marco,
        text=":",
        background="white",
        foreground="#172033",
        font=("Segoe UI", 12, "bold"),
    ).pack(side="left", padx=5)

    # Los minutos posibles van de 00 a 59.
    selector_minuto = ttk.Spinbox(
        marco,
        values=[f"{numero:02d}" for numero in range(60)],
        textvariable=minuto,
        width=4,
        state="readonly",
        wrap=True,
        justify="center",
        style="Hora.TSpinbox",
    )
    selector_minuto.pack(side="left", fill="x", expand=True)

    # Devolvemos el marco, las variables y los controles para poder usarlos
    # desde el formulario y habilitarlos o deshabilitarlos cuando corresponda.
    return marco, hora, minuto, selector_hora, selector_minuto


def abrir_resumen_lote(ventana_padre, resumen):
    """Presenta el resultado final del procesamiento masivo."""
    ventana = tk.Toplevel(ventana_padre)
    ventana.title("Procesamiento finalizado")
    ventana.geometry("520x470")
    ventana.resizable(False, False)
    ventana.configure(background="#eef3f8")
    ventana.transient(ventana_padre)
    ventana.grab_set()
    centrar_ventana(ventana)

    encabezado = tk.Frame(ventana, background="#059669", height=100)
    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)

    tk.Label(
        encabezado,
        text="Lote procesado",
        background="#059669",
        foreground="white",
        font=("Segoe UI", 18, "bold"),
    ).pack(anchor="w", padx=32, pady=(20, 2))

    tk.Label(
        encabezado,
        text="Los reportes CSV fueron generados correctamente",
        background="#059669",
        foreground="#d1fae5",
        font=("Segoe UI", 10),
    ).pack(anchor="w", padx=32)

    tarjeta = tk.Frame(
        ventana,
        background="white",
        highlightbackground="#dbe3ec",
        highlightthickness=1,
        padx=30,
        pady=25,
    )
    tarjeta.pack(fill="both", expand=True, padx=30, pady=28)
    tarjeta.columnconfigure(1, weight=1)

    filas = [
        ("Movimientos procesados", resumen["procesados"]),
        ("Movimientos rechazados", resumen["rechazados"]),
        ("Total recaudado", formatear_importe(resumen["total_recaudado"])),
    ]

    for numero_fila, (etiqueta, valor) in enumerate(filas):
        tk.Label(
            tarjeta,
            text=etiqueta,
            background="white",
            foreground="#64748b",
            font=("Segoe UI", 10),
        ).grid(row=numero_fila, column=0, sticky="w", pady=10)

        tk.Label(
            tarjeta,
            text=valor,
            background="white",
            foreground="#172033",
            font=("Segoe UI", 11, "bold"),
        ).grid(row=numero_fila, column=1, sticky="e", pady=10)

    tk.Label(
        tarjeta,
        text="Archivos generados: liquidacion.csv y rechazados.csv",
        background="white",
        foreground="#64748b",
        font=("Segoe UI", 9),
        wraplength=390,
    ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(15, 5))

    BotonRedondeado(
        tarjeta,
        texto="Cerrar",
        comando=ventana.destroy,
        color="#e2e8f0",
        color_activo="#cbd5e1",
        color_texto="#172033",
        ancho=180,
        alto=44,
    ).grid(row=4, column=0, columnspan=2, pady=(20, 0))


def procesar_movimientos_desde_interfaz(ventana_padre):
    """Ejecuta el lote y muestra errores controlados o el resumen final."""
    try:
        resumen = procesar_lote()
    except ErrorArchivoDatos as error:
        messagebox.showerror(
            "No se pudo procesar el lote",
            str(error),
            parent=ventana_padre,
        )
        return
    except (KeyError, TypeError, RecursionError) as error:
        messagebox.showerror(
            "Datos incompatibles",
            f"No se pudo completar el procesamiento: {error}",
            parent=ventana_padre,
        )
        return

    abrir_resumen_lote(ventana_padre, resumen)


def abrir_resultado(ventana_padre, resultado):
    """Muestra una ventana con el detalle completo de la liquidación."""
    ventana = tk.Toplevel(ventana_padre)
    ventana.title("Resultado de la liquidación")
    ventana.geometry("520x590")
    ventana.resizable(False, False)
    ventana.configure(background="#eef3f8")
    ventana.transient(ventana_padre)
    ventana.grab_set()
    centrar_ventana(ventana)

    # Encabezado verde para diferenciar un resultado correcto del formulario.
    encabezado = tk.Frame(ventana, background="#059669", height=100)
    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)

    tk.Label(
        encabezado,
        text="Liquidación calculada",
        background="#059669",
        foreground="white",
        font=("Segoe UI", 18, "bold"),
    ).pack(anchor="w", padx=32, pady=(20, 2))

    tk.Label(
        encabezado,
        text=f"Patente {resultado['patente']} · guardada en liquidacion-manual.csv",
        background="#059669",
        foreground="#d1fae5",
        font=("Segoe UI", 10),
    ).pack(anchor="w", padx=32)

    tarjeta = tk.Frame(
        ventana,
        background="white",
        highlightbackground="#dbe3ec",
        highlightthickness=1,
        padx=30,
        pady=25,
    )
    tarjeta.pack(fill="both", expand=True, padx=30, pady=28)
    tarjeta.columnconfigure(1, weight=1)

    # Si existen días completos se muestran los días; de lo contrario,
    # mostramos la duración exacta calculada a partir de los horarios.
    if resultado["dias"] > 0:
        duracion = f"{resultado['dias']} día(s) completo(s)"
    else:
        duracion = f"{resultado['minutos_estadia']} minutos"

    # Cada tupla contiene el nombre y el valor de una fila del resumen.
    filas = [
        ("Vehículo", resultado["tipo_vehiculo"].capitalize()),
        ("Duración", duracion),
        ("Lavado", "Sí" if resultado["lavado"] else "No"),
        ("Importe base", formatear_importe(resultado["importe_base"])),
        ("Bonificación", formatear_importe(resultado["bonificacion"])),
        ("Estacionamiento a cobrar", formatear_importe(resultado["costo_estacionamiento"])),
        ("Servicio de lavado", formatear_importe(resultado["costo_lavado"])),
    ]

    # Este for solo construye filas visuales; no calcula el estacionamiento.
    # La restricción de no usar ciclos corresponde a la función recursiva.
    for numero_fila, (etiqueta, valor) in enumerate(filas):
        tk.Label(
            tarjeta,
            text=etiqueta,
            background="white",
            foreground="#64748b",
            font=("Segoe UI", 10),
        ).grid(row=numero_fila, column=0, sticky="w", pady=9)

        tk.Label(
            tarjeta,
            text=valor,
            background="white",
            foreground="#172033",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=numero_fila, column=1, sticky="e", pady=9)

    # Línea divisoria antes de destacar el total final.
    separador = ttk.Separator(tarjeta, orient="horizontal")
    separador.grid(row=len(filas), column=0, columnspan=2, sticky="ew", pady=16)

    tk.Label(
        tarjeta,
        text="TOTAL",
        background="white",
        foreground="#172033",
        font=("Segoe UI", 12, "bold"),
    ).grid(row=len(filas) + 1, column=0, sticky="w")

    tk.Label(
        tarjeta,
        text=formatear_importe(resultado["total"]),
        background="white",
        foreground="#059669",
        font=("Segoe UI", 20, "bold"),
    ).grid(row=len(filas) + 1, column=1, sticky="e")

    BotonRedondeado(
        tarjeta,
        texto="Cerrar",
        comando=ventana.destroy,
        color="#e2e8f0",
        color_activo="#cbd5e1",
        color_texto="#172033",
        ancho=180,
        alto=44,
    ).grid(row=len(filas) + 2, column=0, columnspan=2, pady=(25, 0))


def validar_y_liquidar(
    ventana_padre,
    patente,
    tipo_vehiculo,
    hora_entrada,
    hora_salida,
    dias,
    lavado,
    mensaje_error=None,
):
    """Valida, carga tarifas, calcula y muestra una liquidación manual."""
    # Limpiamos cualquier mensaje correspondiente al intento anterior.
    if mensaje_error is not None:
        mensaje_error.set("")

    try:
        # La función devuelve valores normalizados o lanza ErrorValidacion.
        datos_validados = validar_datos_liquidacion(
            patente,
            tipo_vehiculo,
            hora_entrada,
            hora_salida,
            dias,
            lavado,
        )
        # Las tarifas se leen al liquidar para usar siempre los precios actuales.
        datos_tarifas = cargar_tarifas()

        # La lógica del importe se encuentra separada en calculos.py.
        resultado = calcular_liquidacion(datos_validados, datos_tarifas)

        # Solo guardamos después de validar y calcular correctamente.
        guardar_liquidacion_manual(resultado)

    except ErrorValidacion as error:
        # Los errores del formulario se muestran junto a los campos.
        if mensaje_error is not None:
            mensaje_error.set(str(error))
        else:
            messagebox.showerror("Datos incorrectos", str(error), parent=ventana_padre)
        return
    except ErrorArchivoDatos as error:
        # Un JSON roto, vacío o incompleto genera un mensaje controlado.
        messagebox.showerror("Problema con tarifas.json", str(error), parent=ventana_padre)
        return
    except (KeyError, TypeError, RecursionError) as error:
        # Protección adicional ante datos incompatibles durante el cálculo.
        messagebox.showerror(
            "No se pudo calcular",
            f"Los datos de la tarifa no permiten completar el cálculo: {error}",
            parent=ventana_padre,
        )
        return

    # Solo se abre el resultado cuando todas las etapas finalizaron bien.
    abrir_resultado(ventana_padre, resultado)


def abrir_liquidacion_manual(ventana_principal):
    """Abre un formulario guiado para cargar una liquidación manual."""
    # Toplevel crea una ventana secundaria sin iniciar otra aplicación.
    ventana = tk.Toplevel(ventana_principal)
    ventana.title("Liquidación manual")
    ventana.geometry("680x700")
    ventana.resizable(False, False)
    ventana.configure(background="#eef3f8")
    ventana.transient(ventana_principal)
    ventana.grab_set()
    centrar_ventana(ventana)

    # Encabezado del formulario.
    encabezado = tk.Frame(ventana, background="#2563eb", height=105)
    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)

    tk.Label(
        encabezado,
        text="Nueva liquidación",
        background="#2563eb",
        foreground="white",
        font=("Segoe UI", 18, "bold"),
    ).pack(anchor="w", padx=38, pady=(19, 2))

    tk.Label(
        encabezado,
        text="Completa únicamente los datos correspondientes a la estadía",
        background="#2563eb",
        foreground="#dbeafe",
        font=("Segoe UI", 10),
    ).pack(anchor="w", padx=38)

    # Tarjeta que agrupa los campos del formulario.
    formulario = tk.Frame(
        ventana,
        background="white",
        highlightbackground="#dbe3ec",
        highlightthickness=1,
        padx=34,
        pady=27,
    )
    formulario.pack(fill="both", expand=True, padx=35, pady=28)
    formulario.columnconfigure(0, weight=1)
    formulario.columnconfigure(1, weight=1)

    # La patente se normaliza mientras se escribe: solo conserva letras y
    # números, la convierte a mayúsculas y limita su longitud a 7 caracteres.
    patente = tk.StringVar()

    def normalizar_patente_visual(*argumentos):
        valor_actual = patente.get()
        valor_limpio = "".join(
            caracter for caracter in valor_actual.upper() if caracter.isalnum()
        )[:7]

        if valor_actual != valor_limpio:
            patente.set(valor_limpio)

    patente.trace_add("write", normalizar_patente_visual)

    ttk.Label(formulario, text="PATENTE", style="Formulario.TLabel").grid(
        row=0, column=0, columnspan=2, sticky="w"
    )
    entrada_patente = ttk.Entry(
        formulario,
        textvariable=patente,
        style="Campo.TEntry",
        font=("Segoe UI", 11),
    )
    entrada_patente.grid(
        row=1, column=0, columnspan=2, sticky="ew", pady=(6, 3)
    )

    tk.Label(
        formulario,
        text="6 caracteres para formato tradicional o 7 para Mercosur",
        background="white",
        foreground="#64748b",
        font=("Segoe UI", 9),
    ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 16))

    # El tipo de vehículo es una lista cerrada porque solo existen tres tarifas.
    ttk.Label(formulario, text="TIPO DE VEHÍCULO", style="Formulario.TLabel").grid(
        row=3, column=0, sticky="w", padx=(0, 10)
    )
    ttk.Label(formulario, text="TIPO DE ESTADÍA", style="Formulario.TLabel").grid(
        row=3, column=1, sticky="w", padx=(10, 0)
    )

    selector_tipo = ttk.Combobox(
        formulario,
        values=["moto", "auto", "camioneta"],
        state="readonly",
        style="Campo.TCombobox",
    )
    selector_tipo.grid(row=4, column=0, sticky="ew", padx=(0, 10), pady=(6, 20))
    selector_tipo.current(1)

    modalidad = tk.StringVar(value="Mismo día")
    selector_modalidad = ttk.Combobox(
        formulario,
        textvariable=modalidad,
        values=["Mismo día", "Días completos"],
        state="readonly",
        style="Campo.TCombobox",
    )
    selector_modalidad.grid(
        row=4, column=1, sticky="ew", padx=(10, 0), pady=(6, 20)
    )

    # Este contenedor muestra horarios o días según la modalidad seleccionada.
    contenedor_periodo = tk.Frame(formulario, background="white")
    contenedor_periodo.grid(row=5, column=0, columnspan=2, sticky="ew")
    contenedor_periodo.columnconfigure(0, weight=1)
    contenedor_periodo.columnconfigure(1, weight=1)

    marco_horarios = tk.Frame(contenedor_periodo, background="white")
    marco_horarios.grid(row=0, column=0, columnspan=2, sticky="ew")
    marco_horarios.columnconfigure(0, weight=1)
    marco_horarios.columnconfigure(1, weight=1)

    ttk.Label(marco_horarios, text="HORA DE ENTRADA", style="Formulario.TLabel").grid(
        row=0, column=0, sticky="w", padx=(0, 10)
    )
    ttk.Label(marco_horarios, text="HORA DE SALIDA", style="Formulario.TLabel").grid(
        row=0, column=1, sticky="w", padx=(10, 0)
    )

    (
        selector_entrada,
        hora_entrada,
        minuto_entrada,
        _,
        _,
    ) = crear_selector_hora(marco_horarios)
    selector_entrada.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(6, 3))

    (
        selector_salida,
        hora_salida,
        minuto_salida,
        _,
        _,
    ) = crear_selector_hora(marco_horarios)
    selector_salida.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(6, 3))

    # Valores iniciales distintos para que el formulario sea coherente al abrir.
    hora_entrada.set("08")
    hora_salida.set("09")

    tk.Label(
        marco_horarios,
        text="Selecciona la hora y los minutos. La salida debe ser posterior.",
        background="white",
        foreground="#64748b",
        font=("Segoe UI", 9),
    ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 18))

    # En modalidad por días mostramos un selector numérico, no texto libre.
    marco_dias = tk.Frame(contenedor_periodo, background="white")
    marco_dias.grid(row=0, column=0, columnspan=2, sticky="ew")
    marco_dias.columnconfigure(0, weight=1)

    ttk.Label(marco_dias, text="CANTIDAD DE DÍAS COMPLETOS", style="Formulario.TLabel").grid(
        row=0, column=0, sticky="w"
    )

    dias = tk.StringVar(value="1")

    # Tkinter llamará esta validación antes de aceptar cada cambio.
    # Se permiten únicamente números y no se impone un máximo académico.
    validar_numero_dias = ventana.register(
        lambda nuevo_valor: nuevo_valor == "" or nuevo_valor.isdigit()
    )

    selector_dias = ttk.Spinbox(
        marco_dias,
        from_=1,
        to=1000000,
        textvariable=dias,
        validate="key",
        validatecommand=(validar_numero_dias, "%P"),
        justify="center",
        style="Hora.TSpinbox",
    )
    selector_dias.grid(row=1, column=0, sticky="ew", pady=(6, 3))

    tk.Label(
        marco_dias,
        text="Usa las flechas o escribe una cantidad entera mayor que cero.",
        background="white",
        foreground="#64748b",
        font=("Segoe UI", 9),
    ).grid(row=2, column=0, sticky="w", pady=(0, 18))

    def actualizar_modalidad(evento=None):
        """Muestra únicamente los campos necesarios para la modalidad elegida."""
        if modalidad.get() == "Mismo día":
            marco_dias.grid_remove()
            marco_horarios.grid()
        else:
            marco_horarios.grid_remove()
            marco_dias.grid()

    selector_modalidad.bind("<<ComboboxSelected>>", actualizar_modalidad)
    actualizar_modalidad()

    # El lavado se representa con un booleano: marcado o no marcado.
    tiene_lavado = tk.BooleanVar(value=False)
    ttk.Checkbutton(
        formulario,
        text="Agregar servicio de lavado",
        variable=tiene_lavado,
        style="Formulario.TCheckbutton",
    ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(3, 17))

    # Los errores de entrada aparecen dentro del formulario sin abrir ventanas.
    mensaje_error = tk.StringVar()
    tk.Label(
        formulario,
        textvariable=mensaje_error,
        background="white",
        foreground="#dc2626",
        font=("Segoe UI", 9, "bold"),
        justify="left",
        wraplength=520,
    ).grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 8))

    def ejecutar_liquidacion():
        """Recoge solo los datos visibles y ejecuta la liquidación."""
        if modalidad.get() == "Mismo día":
            entrada_seleccionada = f"{hora_entrada.get()}:{minuto_entrada.get()}"
            salida_seleccionada = f"{hora_salida.get()}:{minuto_salida.get()}"
            dias_seleccionados = "0"
        else:
            entrada_seleccionada = ""
            salida_seleccionada = ""
            dias_seleccionados = dias.get()

        validar_y_liquidar(
            ventana,
            patente.get(),
            selector_tipo.get(),
            entrada_seleccionada,
            salida_seleccionada,
            dias_seleccionados,
            tiene_lavado.get(),
            mensaje_error,
        )

    BotonRedondeado(
        formulario,
        texto="Calcular y guardar liquidación",
        comando=ejecutar_liquidacion,
        ancho=500,
        alto=50,
    ).grid(row=8, column=0, columnspan=2, pady=(8, 0))

    # El cursor comienza en el único campo que necesita escritura manual.
    entrada_patente.focus()
