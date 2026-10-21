# Tkinter permite crear ventanas y variables asociadas a los controles.
import tkinter as tk
# os expande variables como %USERPROFILE% guardadas por Windows.
import os
# Path permite localizar el Escritorio sin depender de la carpeta del proyecto.
from pathlib import Path
# filedialog permite elegir dónde exportar; messagebox muestra avisos y ttk
# aporta componentes con estilos modernos.
from tkinter import filedialog, messagebox, ttk

# La interfaz solicita los datos externos y el cálculo, pero no contiene
# reglas de negocio. Esto mantiene cada responsabilidad en su propio archivo.
from archivos import (
    ErrorArchivoDatos,
    cargar_historial_liquidaciones,
    cargar_tarifas,
    guardar_liquidacion_manual,
    guardar_reporte_csv,
)
from calculos import calcular_liquidacion
# procesamiento coordina la lectura y exportación masiva de movimientos.
from procesamiento import procesar_lote
# Importamos el error controlado y la validación completa del formulario.
from validaciones import ErrorValidacion, normalizar_patente, validar_datos_liquidacion


# Paleta visual compartida por todas las ventanas de AutoPark. Centralizar los
# colores evita que cada pantalla termine usando tonos y bordes diferentes.
COLOR_FONDO = "#eef3f8"
COLOR_TARJETA = "#ffffff"
COLOR_PRIMARIO = "#2563eb"
COLOR_PRIMARIO_ACTIVO = "#1d4ed8"
COLOR_PRIMARIO_SUAVE = "#dbeafe"
COLOR_EXITO = "#059669"
COLOR_EXITO_SUAVE = "#d1fae5"
COLOR_TEXTO = "#172033"
COLOR_SECUNDARIO = "#64748b"
COLOR_BORDE = "#dbe3ec"
COLOR_CAMPO = "#f8fafc"
COLOR_BOTON_SECUNDARIO = "#e2e8f0"
COLOR_BOTON_SECUNDARIO_ACTIVO = "#cbd5e1"


class BotonRedondeado(tk.Canvas):
    """Botón reutilizable con esquinas redondeadas y efecto al pasar el mouse."""

    def __init__(
        self,
        contenedor,
        texto,
        comando,
        color=COLOR_PRIMARIO,
        color_activo=COLOR_PRIMARIO_ACTIVO,
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


def crear_encabezado(ventana, titulo, subtitulo, color=COLOR_PRIMARIO):
    """Crea el encabezado uniforme utilizado por las ventanas secundarias."""
    color_descripcion = (
        COLOR_EXITO_SUAVE if color == COLOR_EXITO else COLOR_PRIMARIO_SUAVE
    )
    encabezado = tk.Frame(ventana, background=color, height=94)
    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)

    tk.Label(
        encabezado,
        text=titulo,
        background=color,
        foreground="white",
        font=("Segoe UI", 18, "bold"),
    ).pack(anchor="w", padx=34, pady=(18, 2))

    tk.Label(
        encabezado,
        text=subtitulo,
        background=color,
        foreground=color_descripcion,
        font=("Segoe UI", 10),
    ).pack(anchor="w", padx=34)

    return encabezado


def formatear_importe(importe):
    """Convierte 16000 en un texto más legible, por ejemplo $16.000."""
    return f"${importe:,.0f}".replace(",", ".")


def formatear_fecha_historial(fecha):
    """Convierte una fecha ISO en un texto corto y fácil de leer en la tabla."""
    return str(fecha).replace("T", " ")[:16]


def obtener_carpeta_escritorio():
    """Localiza el Escritorio habitual, incluso cuando está dentro de OneDrive."""
    carpeta_usuario = Path.home()

    # Windows guarda aquí la ubicación real del Escritorio. Consultarla evita
    # confundir un Desktop local con el Escritorio activo dentro de OneDrive.
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
        ) as clave:
            valor_escritorio, _ = winreg.QueryValueEx(clave, "Desktop")
            escritorio_windows = Path(os.path.expandvars(valor_escritorio))
            if escritorio_windows.is_dir():
                return escritorio_windows
    except (ImportError, FileNotFoundError, OSError):
        # En otros sistemas operativos se utilizan las rutas alternativas.
        pass

    ubicaciones_posibles = [
        carpeta_usuario / "Desktop",
        carpeta_usuario / "Escritorio",
        carpeta_usuario / "OneDrive" / "Desktop",
        carpeta_usuario / "OneDrive" / "Escritorio",
    ]

    for ubicacion in ubicaciones_posibles:
        if ubicacion.is_dir():
            return ubicacion

    # Si Windows usa otra configuración, el selector abre al menos la carpeta
    # personal del usuario en lugar de una ruta inexistente.
    return carpeta_usuario


def filtrar_registros_historial(
    registros,
    patente="",
    tipo_vehiculo="Todos",
    lavado="Todos",
    origen="Todos",
    fecha_desde="Todas",
    fecha_hasta="Todas",
):
    """Aplica simultáneamente los filtros seleccionados en el historial."""
    patente_normalizada = normalizar_patente(patente)
    resultado = []

    for registro in registros:
        # Los primeros diez caracteres corresponden a AAAA-MM-DD tanto en
        # fechas simples como en marcas de tiempo ISO.
        fecha_registro = str(registro["fecha"])[:10]
        coincide_patente = (
            not patente_normalizada
            or patente_normalizada in normalizar_patente(registro["patente"])
        )
        coincide_tipo = (
            tipo_vehiculo == "Todos"
            or registro["tipo_vehiculo"].lower() == tipo_vehiculo.lower()
        )
        coincide_lavado = (
            lavado == "Todos"
            or str(registro["lavado"]).strip().lower() == lavado.lower()
        )
        coincide_origen = (
            origen == "Todos"
            or registro["origen"].lower() == origen.lower()
        )
        coincide_desde = fecha_desde == "Todas" or fecha_registro >= fecha_desde
        coincide_hasta = fecha_hasta == "Todas" or fecha_registro <= fecha_hasta

        if (
            coincide_patente
            and coincide_tipo
            and coincide_lavado
            and coincide_origen
            and coincide_desde
            and coincide_hasta
        ):
            resultado.append(registro)

    return resultado


def crear_selector_hora(contenedor):
    """Crea selectores separados para hora y minuto sin permitir texto libre."""
    marco = tk.Frame(contenedor, background=COLOR_TARJETA)

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
        background=COLOR_TARJETA,
        foreground=COLOR_TEXTO,
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
    ventana.configure(background=COLOR_FONDO)
    ventana.transient(ventana_padre)
    ventana.grab_set()
    centrar_ventana(ventana)

    crear_encabezado(
        ventana,
        "Lote procesado",
        "Los reportes CSV fueron generados correctamente",
        COLOR_EXITO,
    )

    tarjeta = tk.Frame(
        ventana,
        background=COLOR_TARJETA,
        highlightbackground=COLOR_BORDE,
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
            background=COLOR_TARJETA,
            foreground=COLOR_SECUNDARIO,
            font=("Segoe UI", 10),
        ).grid(row=numero_fila, column=0, sticky="w", pady=10)

        tk.Label(
            tarjeta,
            text=valor,
            background=COLOR_TARJETA,
            foreground=COLOR_TEXTO,
            font=("Segoe UI", 11, "bold"),
        ).grid(row=numero_fila, column=1, sticky="e", pady=10)

    tk.Label(
        tarjeta,
        text="Archivos generados: liquidacion.csv y rechazados.csv",
        background=COLOR_TARJETA,
        foreground=COLOR_SECUNDARIO,
        font=("Segoe UI", 9),
        wraplength=390,
    ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(15, 5))

    BotonRedondeado(
        tarjeta,
        texto="Aceptar",
        comando=ventana.destroy,
        color=COLOR_PRIMARIO,
        color_activo=COLOR_PRIMARIO_ACTIVO,
        color_texto="white",
        ancho=180,
        alto=44,
    ).grid(row=4, column=0, columnspan=2, pady=(20, 0))

    return ventana


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

    return abrir_resumen_lote(ventana_padre, resumen)


def abrir_historial(ventana_padre):
    """Muestra en una tabla las liquidaciones manuales y las procesadas por lote."""
    try:
        registros = cargar_historial_liquidaciones()
    except ErrorArchivoDatos as error:
        messagebox.showerror(
            "No se pudo cargar el historial",
            str(error),
            parent=ventana_padre,
        )
        return

    ventana = tk.Toplevel(ventana_padre)
    ventana.title("Historial de liquidaciones")
    ventana.geometry("1060x700")
    ventana.minsize(900, 560)
    ventana.configure(background=COLOR_FONDO)
    ventana.transient(ventana_padre)
    centrar_ventana(ventana)

    crear_encabezado(
        ventana,
        "Historial de liquidaciones",
        "Consulta todas las cargas manuales y las procesadas desde movimientos.json",
    )

    contenido = tk.Frame(ventana, background=COLOR_FONDO)
    contenido.pack(fill="both", expand=True, padx=28, pady=24)

    # Los filtros pueden combinarse y actualizan la tabla de forma inmediata.
    buscador = tk.Frame(
        contenido,
        background=COLOR_TARJETA,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1,
        padx=18,
        pady=14,
    )
    buscador.pack(fill="x", pady=(0, 14))

    patente_busqueda = tk.StringVar()
    tipo_busqueda = tk.StringVar(value="Todos")
    lavado_busqueda = tk.StringVar(value="Todos")
    origen_busqueda = tk.StringVar(value="Todos")
    fecha_desde_busqueda = tk.StringVar(value="Todas")
    fecha_hasta_busqueda = tk.StringVar(value="Todas")

    # Se ofrecen solamente fechas realmente presentes en los reportes. Esto
    # evita errores de formato y no requiere instalar un calendario externo.
    fechas_disponibles = sorted(
        {
            str(registro["fecha"])[:10]
            for registro in registros
            if str(registro["fecha"]).strip()
        }
    )
    opciones_fechas = ["Todas", *fechas_disponibles]

    etiquetas_filtros = [
        ("PATENTE", 0),
        ("VEHÍCULO", 1),
        ("LAVADO", 2),
        ("ORIGEN", 3),
    ]
    for etiqueta, columna in etiquetas_filtros:
        tk.Label(
            buscador,
            text=etiqueta,
            background=COLOR_TARJETA,
            foreground="#475569",
            font=("Segoe UI", 8, "bold"),
        ).grid(row=0, column=columna, sticky="w", padx=(0, 12))

    campo_busqueda = ttk.Entry(
        buscador,
        textvariable=patente_busqueda,
        width=24,
        style="Campo.TEntry",
    )
    campo_busqueda.grid(row=1, column=0, sticky="ew", padx=(0, 12), pady=(5, 0))

    selector_tipo = ttk.Combobox(
        buscador,
        textvariable=tipo_busqueda,
        values=["Todos", "Auto", "Moto", "Camioneta"],
        state="readonly",
        width=15,
        style="Campo.TCombobox",
    )
    selector_tipo.grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=(5, 0))

    selector_lavado = ttk.Combobox(
        buscador,
        textvariable=lavado_busqueda,
        values=["Todos", "Sí", "No"],
        state="readonly",
        width=11,
        style="Campo.TCombobox",
    )
    selector_lavado.grid(row=1, column=2, sticky="ew", padx=(0, 12), pady=(5, 0))

    selector_origen = ttk.Combobox(
        buscador,
        textvariable=origen_busqueda,
        values=["Todos", "Manual", "Lote"],
        state="readonly",
        width=11,
        style="Campo.TCombobox",
    )
    selector_origen.grid(row=1, column=3, sticky="ew", padx=(0, 12), pady=(5, 0))

    buscador.columnconfigure(0, weight=2)
    buscador.columnconfigure((1, 2, 3), weight=1)

    BotonRedondeado(
        buscador,
        texto="Limpiar filtros",
        comando=lambda: limpiar_filtros(),
        color=COLOR_BOTON_SECUNDARIO,
        color_activo=COLOR_BOTON_SECUNDARIO_ACTIVO,
        color_texto=COLOR_TEXTO,
        ancho=135,
        alto=38,
        radio=11,
    ).grid(row=1, column=4, padx=(5, 0), pady=(5, 0))

    tk.Label(
        buscador,
        text="FECHA DESDE",
        background=COLOR_TARJETA,
        foreground="#475569",
        font=("Segoe UI", 8, "bold"),
    ).grid(row=2, column=0, sticky="w", pady=(12, 0))

    tk.Label(
        buscador,
        text="FECHA HASTA",
        background=COLOR_TARJETA,
        foreground="#475569",
        font=("Segoe UI", 8, "bold"),
    ).grid(row=2, column=1, sticky="w", pady=(12, 0))

    selector_fecha_desde = ttk.Combobox(
        buscador,
        textvariable=fecha_desde_busqueda,
        values=opciones_fechas,
        state="readonly",
        style="Campo.TCombobox",
    )
    selector_fecha_desde.grid(
        row=3, column=0, sticky="ew", padx=(0, 12), pady=(5, 0)
    )

    selector_fecha_hasta = ttk.Combobox(
        buscador,
        textvariable=fecha_hasta_busqueda,
        values=opciones_fechas,
        state="readonly",
        style="Campo.TCombobox",
    )
    selector_fecha_hasta.grid(
        row=3, column=1, sticky="ew", padx=(0, 12), pady=(5, 0)
    )

    tk.Label(
        buscador,
        text="El rango incluye ambas fechas seleccionadas.",
        background=COLOR_TARJETA,
        foreground=COLOR_SECUNDARIO,
        font=("Segoe UI", 9),
    ).grid(row=3, column=2, columnspan=3, sticky="w", pady=(5, 0))

    # Estas tarjetas resumen los valores que solicita el desafío de historial.
    resumen = tk.Frame(contenido, background=COLOR_FONDO)
    resumen.pack(fill="x", pady=(0, 14))
    resumen.columnconfigure((0, 1, 2), weight=1, uniform="resumen")

    cantidad_texto = tk.StringVar(value="0")
    total_texto = tk.StringVar(value="$0")
    promedio_texto = tk.StringVar(value="0 min")

    for columna, (titulo, variable) in enumerate(
        [
            ("ESTADÍAS ENCONTRADAS", cantidad_texto),
            ("TOTAL PAGADO", total_texto),
            ("PROMEDIO POR ESTADÍA", promedio_texto),
        ]
    ):
        tarjeta = tk.Frame(
            resumen,
            background=COLOR_TARJETA,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1,
            padx=18,
            pady=12,
        )
        tarjeta.grid(row=0, column=columna, sticky="ew", padx=(0 if columna == 0 else 7, 0))
        tk.Label(
            tarjeta,
            text=titulo,
            background=COLOR_TARJETA,
            foreground=COLOR_SECUNDARIO,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")
        tk.Label(
            tarjeta,
            textvariable=variable,
            background=COLOR_TARJETA,
            foreground=COLOR_TEXTO,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w", pady=(4, 0))

    marco_tabla = tk.Frame(
        contenido,
        background=COLOR_TARJETA,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1,
    )
    marco_tabla.rowconfigure(0, weight=1)
    marco_tabla.columnconfigure(0, weight=1)

    # El identificador se conserva en los CSV para auditoría, pero no se
    # muestra porque no aporta información útil en una consulta cotidiana.
    columnas = ("fecha", "patente", "tipo", "duracion", "lavado", "total", "origen")
    tabla = ttk.Treeview(
        marco_tabla,
        columns=columnas,
        show="headings",
        style="Historial.Treeview",
    )
    # Las filas alternadas permiten seguir cada registro horizontalmente.
    tabla.tag_configure("par", background=COLOR_CAMPO)
    tabla.tag_configure("impar", background=COLOR_TARJETA)

    encabezados = {
        "fecha": "FECHA",
        "patente": "PATENTE",
        "tipo": "VEHÍCULO",
        "duracion": "DURACIÓN",
        "lavado": "LAVADO",
        "total": "TOTAL",
        "origen": "ORIGEN",
    }
    anchos = {
        "fecha": 155,
        "patente": 120,
        "tipo": 130,
        "duracion": 130,
        "lavado": 100,
        "total": 120,
        "origen": 100,
    }
    for columna in columnas:
        tabla.heading(columna, text=encabezados[columna])
        tabla.column(columna, width=anchos[columna], minwidth=65, anchor="center")

    barra_vertical = ttk.Scrollbar(marco_tabla, orient="vertical", command=tabla.yview)
    tabla.configure(
        yscrollcommand=barra_vertical.set,
    )
    tabla.grid(row=0, column=0, sticky="nsew")
    barra_vertical.grid(row=0, column=1, sticky="ns")

    pie = tk.Frame(contenido, background=COLOR_FONDO)
    # Se reserva primero el pie para impedir que la tabla oculte el botón.
    pie.pack(side="bottom", fill="x", pady=(14, 0))
    estado_texto = tk.StringVar()
    tk.Label(
        pie,
        textvariable=estado_texto,
        background=COLOR_FONDO,
        foreground=COLOR_SECUNDARIO,
        font=("Segoe UI", 9),
    ).pack(side="left")

    BotonRedondeado(
        pie,
        texto="Cerrar",
        comando=ventana.destroy,
        color=COLOR_BOTON_SECUNDARIO,
        color_activo=COLOR_BOTON_SECUNDARIO_ACTIVO,
        color_texto=COLOR_TEXTO,
        ancho=160,
        alto=44,
        radio=12,
    ).pack(side="right")

    BotonRedondeado(
        pie,
        texto="Exportar CSV",
        comando=lambda: exportar_resultado_filtrado(),
        color=COLOR_PRIMARIO,
        color_activo=COLOR_PRIMARIO_ACTIVO,
        color_texto="white",
        ancho=160,
        alto=44,
        radio=12,
    ).pack(side="right", padx=(0, 10))

    # La tabla ocupa solamente el espacio restante entre el resumen y el pie.
    marco_tabla.pack(fill="both", expand=True)

    def actualizar_tabla(*_):
        """Filtra, calcula los indicadores y reconstruye las filas visibles."""
        rango_invalido = (
            fecha_desde_busqueda.get() != "Todas"
            and fecha_hasta_busqueda.get() != "Todas"
            and fecha_desde_busqueda.get() > fecha_hasta_busqueda.get()
        )
        visibles = filtrar_registros_historial(
            registros,
            patente_busqueda.get(),
            tipo_busqueda.get(),
            lavado_busqueda.get(),
            origen_busqueda.get(),
            fecha_desde_busqueda.get(),
            fecha_hasta_busqueda.get(),
        )
        if rango_invalido:
            visibles = []

        tabla.delete(*tabla.get_children())
        for indice, registro in enumerate(visibles):
            if registro["dias"] > 0:
                duracion = f"{registro['dias']} día(s)"
            else:
                duracion = f"{registro['minutos_estadia']} min"

            tabla.insert(
                "",
                "end",
                values=(
                    formatear_fecha_historial(registro["fecha"]),
                    registro["patente"],
                    registro["tipo_vehiculo"].capitalize(),
                    duracion,
                    registro["lavado"],
                    formatear_importe(registro["total"]),
                    registro["origen"],
                ),
                tags=("par" if indice % 2 == 0 else "impar",),
            )

        cantidad = len(visibles)
        total = sum(registro["total"] for registro in visibles)
        promedio = (
            round(sum(registro["duracion_minutos"] for registro in visibles) / cantidad)
            if cantidad
            else 0
        )
        cantidad_texto.set(str(cantidad))
        total_texto.set(formatear_importe(total))
        promedio_texto.set(f"{promedio} min")
        if rango_invalido:
            estado_texto.set("La fecha desde no puede ser posterior a la fecha hasta.")
        elif not visibles:
            estado_texto.set("No hay liquidaciones para mostrar con esos filtros.")
        else:
            estado_texto.set(
                f"Mostrando {cantidad} de {len(registros)} liquidación(es)."
            )

    def limpiar_filtros():
        """Restablece todos los filtros sin modificar los registros guardados."""
        patente_busqueda.set("")
        tipo_busqueda.set("Todos")
        lavado_busqueda.set("Todos")
        origen_busqueda.set("Todos")
        fecha_desde_busqueda.set("Todas")
        fecha_hasta_busqueda.set("Todas")
        actualizar_tabla()

    def exportar_resultado_filtrado():
        """Guarda en un nuevo CSV exactamente los registros visibles."""
        rango_invalido = (
            fecha_desde_busqueda.get() != "Todas"
            and fecha_hasta_busqueda.get() != "Todas"
            and fecha_desde_busqueda.get() > fecha_hasta_busqueda.get()
        )
        if rango_invalido:
            messagebox.showwarning(
                "Rango de fechas inválido",
                "La fecha desde no puede ser posterior a la fecha hasta.",
                parent=ventana,
            )
            return

        visibles = filtrar_registros_historial(
            registros,
            patente_busqueda.get(),
            tipo_busqueda.get(),
            lavado_busqueda.get(),
            origen_busqueda.get(),
            fecha_desde_busqueda.get(),
            fecha_hasta_busqueda.get(),
        )
        if not visibles:
            messagebox.showwarning(
                "Sin registros",
                "No hay liquidaciones que coincidan con los filtros actuales.",
                parent=ventana,
            )
            return

        ruta_destino = filedialog.asksaveasfilename(
            parent=ventana,
            title="Guardar historial filtrado",
            initialdir=str(obtener_carpeta_escritorio()),
            defaultextension=".csv",
            initialfile="historial_filtrado.csv",
            filetypes=[("Archivo CSV", "*.csv")],
        )
        if not ruta_destino:
            return

        columnas = [
            "fecha",
            "patente",
            "tipo_vehiculo",
            "dias",
            "minutos_estadia",
            "lavado",
            "total",
            "origen",
        ]
        filas_exportadas = [
            {columna: registro[columna] for columna in columnas}
            for registro in visibles
        ]

        try:
            guardar_reporte_csv(ruta_destino, columnas, filas_exportadas)
        except ErrorArchivoDatos as error:
            messagebox.showerror(
                "No se pudo exportar",
                str(error),
                parent=ventana,
            )
            return

        messagebox.showinfo(
            "Exportación completada",
            f"Se guardaron {len(filas_exportadas)} liquidación(es) en el CSV.",
            parent=ventana,
        )

    patente_busqueda.trace_add("write", actualizar_tabla)
    selector_tipo.bind("<<ComboboxSelected>>", actualizar_tabla)
    selector_lavado.bind("<<ComboboxSelected>>", actualizar_tabla)
    selector_origen.bind("<<ComboboxSelected>>", actualizar_tabla)
    selector_fecha_desde.bind("<<ComboboxSelected>>", actualizar_tabla)
    selector_fecha_hasta.bind("<<ComboboxSelected>>", actualizar_tabla)
    actualizar_tabla()
    campo_busqueda.focus_set()

    return ventana


def abrir_resultado(ventana_padre, resultado):
    """Muestra una ventana con el detalle completo de la liquidación."""
    ventana = tk.Toplevel(ventana_padre)
    ventana.title("Resultado de la liquidación")
    # La altura permite mostrar el desglose y el botón sin recortes.
    ventana.geometry("520x690")
    ventana.resizable(False, False)
    ventana.configure(background=COLOR_FONDO)
    ventana.transient(ventana_padre)
    ventana.grab_set()
    centrar_ventana(ventana)

    crear_encabezado(
        ventana,
        "Liquidación calculada",
        f"Patente {resultado['patente']} · guardada en liquidacion-manual.csv",
        COLOR_EXITO,
    )

    tarjeta = tk.Frame(
        ventana,
        background=COLOR_TARJETA,
        highlightbackground=COLOR_BORDE,
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
            background=COLOR_TARJETA,
            foreground=COLOR_SECUNDARIO,
            font=("Segoe UI", 10),
        ).grid(row=numero_fila, column=0, sticky="w", pady=9)

        tk.Label(
            tarjeta,
            text=valor,
            background=COLOR_TARJETA,
            foreground=COLOR_TEXTO,
            font=("Segoe UI", 10, "bold"),
        ).grid(row=numero_fila, column=1, sticky="e", pady=9)

    # Línea divisoria antes de destacar el total final.
    separador = ttk.Separator(tarjeta, orient="horizontal")
    separador.grid(row=len(filas), column=0, columnspan=2, sticky="ew", pady=16)

    tk.Label(
        tarjeta,
        text="TOTAL",
        background=COLOR_TARJETA,
        foreground=COLOR_TEXTO,
        font=("Segoe UI", 12, "bold"),
    ).grid(row=len(filas) + 1, column=0, sticky="w")

    tk.Label(
        tarjeta,
        text=formatear_importe(resultado["total"]),
        background=COLOR_TARJETA,
        foreground=COLOR_EXITO,
        font=("Segoe UI", 20, "bold"),
    ).grid(row=len(filas) + 1, column=1, sticky="e")

    BotonRedondeado(
        tarjeta,
        texto="Aceptar",
        comando=ventana.destroy,
        color=COLOR_PRIMARIO,
        color_activo=COLOR_PRIMARIO_ACTIVO,
        color_texto="white",
        ancho=180,
        alto=44,
    ).grid(row=len(filas) + 2, column=0, columnspan=2, pady=(25, 0))

    return ventana


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
    ventana.configure(background=COLOR_FONDO)
    ventana.transient(ventana_principal)
    ventana.grab_set()
    centrar_ventana(ventana)

    crear_encabezado(
        ventana,
        "Nueva liquidación",
        "Completa únicamente los datos correspondientes a la estadía",
    )

    # Tarjeta que agrupa los campos del formulario.
    formulario = tk.Frame(
        ventana,
        background=COLOR_TARJETA,
        highlightbackground=COLOR_BORDE,
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
        background=COLOR_TARJETA,
        foreground=COLOR_SECUNDARIO,
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
    contenedor_periodo = tk.Frame(formulario, background=COLOR_TARJETA)
    contenedor_periodo.grid(row=5, column=0, columnspan=2, sticky="ew")
    contenedor_periodo.columnconfigure(0, weight=1)
    contenedor_periodo.columnconfigure(1, weight=1)

    marco_horarios = tk.Frame(contenedor_periodo, background=COLOR_TARJETA)
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
        background=COLOR_TARJETA,
        foreground=COLOR_SECUNDARIO,
        font=("Segoe UI", 9),
    ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 18))

    # En modalidad por días mostramos un selector numérico, no texto libre.
    marco_dias = tk.Frame(contenedor_periodo, background=COLOR_TARJETA)
    marco_dias.grid(row=0, column=0, columnspan=2, sticky="ew")
    marco_dias.columnconfigure(0, weight=1)

    ttk.Label(marco_dias, text="CANTIDAD DE DÍAS COMPLETOS", style="Formulario.TLabel").grid(
        row=0, column=0, sticky="w"
    )

    dias = tk.StringVar(value="1")

    def validar_numero_dias(nuevo_valor):
        """Permite únicamente enteros positivos en la modalidad por días."""
        # El vacío se acepta momentáneamente para permitir reemplazar el valor.
        if nuevo_valor == "":
            return True

        return nuevo_valor.isdigit() and int(nuevo_valor) >= 1

    # Tkinter llamará esta validación antes de aceptar cada cambio.
    validar_numero_dias_registrada = ventana.register(validar_numero_dias)

    selector_dias = ttk.Spinbox(
        marco_dias,
        from_=1,
        to=1000000,
        textvariable=dias,
        validate="key",
        validatecommand=(validar_numero_dias_registrada, "%P"),
        justify="center",
        style="Hora.TSpinbox",
    )
    selector_dias.grid(row=1, column=0, sticky="ew", pady=(6, 3))

    def restaurar_dias_si_esta_vacio(evento=None):
        """Recupera el mínimo permitido si el usuario deja vacío el selector."""
        if dias.get().strip() == "":
            dias.set("1")

    selector_dias.bind("<FocusOut>", restaurar_dias_si_esta_vacio)

    tk.Label(
        marco_dias,
        text="Usa las flechas o escribe una cantidad entera mayor que cero.",
        background=COLOR_TARJETA,
        foreground=COLOR_SECUNDARIO,
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
        background=COLOR_TARJETA,
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

    return ventana
