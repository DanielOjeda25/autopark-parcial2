
# Tkinter contiene los componentes básicos para crear ventanas.
import tkinter as tk
# ttk ofrece versiones de los componentes con estilos modernos.
from tkinter import ttk

from archivos import ErrorArchivoDatos, cargar_historial_liquidaciones

# Importamos la función que abre el formulario desde el otro archivo.
from interfaz import (
    BotonRedondeado,
    COLOR_BORDE,
    COLOR_BOTON_SECUNDARIO,
    COLOR_CAMPO,
    COLOR_FONDO,
    COLOR_EXITO,
    COLOR_PRIMARIO,
    COLOR_PRIMARIO_ACTIVO,
    COLOR_SECUNDARIO,
    COLOR_TARJETA,
    COLOR_TEXTO,
    abrir_historial,
    abrir_liquidacion_manual,
    centrar_ventana,
    procesar_movimientos_desde_interfaz,
)


def configurar_estilos(ventana):
    """Configura los estilos visuales compartidos por toda la aplicación."""
    # Style permite personalizar los componentes pertenecientes a ttk.
    estilo = ttk.Style(ventana)
    # El tema clam admite colores personalizados de forma consistente.
    estilo.theme_use("clam")

    # Estilo usado por el título principal de la tarjeta.
    estilo.configure(
        "Titulo.TLabel",
        background=COLOR_TARJETA,
        foreground=COLOR_TEXTO,
        font=("Segoe UI", 24, "bold"),
    )
    # Estilo utilizado para textos secundarios y explicaciones.
    estilo.configure(
        "Subtitulo.TLabel",
        background=COLOR_TARJETA,
        foreground=COLOR_SECUNDARIO,
        font=("Segoe UI", 11),
    )
    # Estilo del botón que representa la acción principal.
    estilo.configure(
        "Primario.TButton",
        background=COLOR_PRIMARIO,
        foreground="white",
        font=("Segoe UI", 11, "bold"),
        padding=(20, 12),
        borderwidth=0,
    )
    # map cambia colores según el estado del botón.
    estilo.map(
        "Primario.TButton",
        background=[("active", COLOR_PRIMARIO_ACTIVO)],
        foreground=[("disabled", "#94a3b8")],
    )
    # Estilo para acciones secundarias o todavía no disponibles.
    estilo.configure(
        "Secundario.TButton",
        background=COLOR_BOTON_SECUNDARIO,
        foreground=COLOR_TEXTO,
        font=("Segoe UI", 10),
        padding=(20, 11),
        borderwidth=0,
    )
    estilo.map(
        "Secundario.TButton",
        background=[("active", "#cbd5e1"), ("disabled", "#f1f5f9")],
        foreground=[("disabled", "#94a3b8")],
    )
    # Estilos compartidos por las etiquetas y el checkbox del formulario.
    estilo.configure(
        "Formulario.TLabel",
        background=COLOR_TARJETA,
        foreground=COLOR_TEXTO,
        font=("Segoe UI", 10),
    )
    estilo.configure("Formulario.TCheckbutton", background=COLOR_TARJETA)
    # Campos con más espacio interno para que sean cómodos de leer y completar.
    estilo.configure(
        "Campo.TEntry",
        padding=(10, 9),
        fieldbackground=COLOR_CAMPO,
        bordercolor=COLOR_BORDE,
        lightcolor=COLOR_BORDE,
        darkcolor=COLOR_BORDE,
    )
    estilo.configure(
        "Campo.TCombobox",
        padding=(10, 8),
        fieldbackground=COLOR_CAMPO,
        background=COLOR_CAMPO,
        bordercolor=COLOR_BORDE,
        arrowcolor=COLOR_TEXTO,
    )
    # Selectores utilizados para elegir horas y minutos sin escribir texto libre.
    estilo.configure(
        "Hora.TSpinbox",
        padding=(7, 8),
        fieldbackground=COLOR_CAMPO,
        bordercolor=COLOR_BORDE,
        arrowcolor=COLOR_TEXTO,
        font=("Segoe UI", 10),
    )
    estilo.map(
        "Campo.TEntry",
        bordercolor=[("focus", COLOR_PRIMARIO)],
        lightcolor=[("focus", COLOR_PRIMARIO)],
        darkcolor=[("focus", COLOR_PRIMARIO)],
    )
    # La tabla del historial usa filas amplias y un encabezado destacado.
    estilo.configure(
        "Historial.Treeview",
        background=COLOR_TARJETA,
        fieldbackground=COLOR_TARJETA,
        foreground=COLOR_TEXTO,
        rowheight=32,
        font=("Segoe UI", 9),
        borderwidth=0,
    )
    estilo.configure(
        "Historial.Treeview.Heading",
        background=COLOR_BOTON_SECUNDARIO,
        foreground=COLOR_TEXTO,
        font=("Segoe UI", 9, "bold"),
        padding=(8, 8),
    )
    estilo.map(
        "Historial.Treeview",
        background=[("selected", COLOR_PRIMARIO)],
        foreground=[("selected", "white")],
    )


def main():
    """Crea el dashboard principal e inicia la aplicación AutoPark."""
    ventana = tk.Tk()
    ventana.title("AutoPark - Panel de control")
    ventana.geometry("1100x680")
    ventana.minsize(1000, 620)
    ventana.configure(background=COLOR_FONDO)
    centrar_ventana(ventana)
    configurar_estilos(ventana)

    # La estructura principal separa navegación y contenido como un dashboard.
    ventana.columnconfigure(1, weight=1)
    ventana.rowconfigure(0, weight=1)

    color_lateral = "#0f172a"
    color_lateral_secundario = "#94a3b8"
    lateral = tk.Frame(ventana, background=color_lateral, width=235)
    lateral.grid(row=0, column=0, sticky="ns")
    lateral.grid_propagate(False)

    tk.Label(
        lateral,
        text="AUTOPARK",
        background=color_lateral,
        foreground="white",
        font=("Segoe UI", 20, "bold"),
    ).pack(anchor="w", padx=25, pady=(30, 3))
    tk.Label(
        lateral,
        text="GESTIÓN DE ESTACIONAMIENTO",
        background=color_lateral,
        foreground=color_lateral_secundario,
        font=("Segoe UI", 8, "bold"),
    ).pack(anchor="w", padx=25, pady=(0, 38))

    tk.Label(
        lateral,
        text="OPERACIONES",
        background=color_lateral,
        foreground=color_lateral_secundario,
        font=("Segoe UI", 8, "bold"),
    ).pack(anchor="w", padx=25, pady=(0, 12))

    contenido = tk.Frame(ventana, background=COLOR_FONDO)
    contenido.grid(row=0, column=1, sticky="nsew")
    contenido.columnconfigure(0, weight=1)
    contenido.rowconfigure(3, weight=1)

    encabezado = tk.Frame(contenido, background=COLOR_FONDO)
    encabezado.grid(row=0, column=0, sticky="ew", padx=30, pady=(28, 18))

    tk.Label(
        encabezado,
        text="Panel de control",
        background=COLOR_FONDO,
        foreground=COLOR_TEXTO,
        font=("Segoe UI", 24, "bold"),
    ).pack(anchor="w")
    tk.Label(
        encabezado,
        text="Resumen general de las operaciones registradas",
        background=COLOR_FONDO,
        foreground=COLOR_SECUNDARIO,
        font=("Segoe UI", 10),
    ).pack(anchor="w", pady=(3, 0))

    tarjetas = tk.Frame(contenido, background=COLOR_FONDO)
    tarjetas.grid(row=1, column=0, sticky="ew", padx=30)
    tarjetas.columnconfigure((0, 1, 2), weight=1, uniform="indicadores")

    cantidad_texto = tk.StringVar(value="0")
    total_texto = tk.StringVar(value="$0")
    promedio_texto = tk.StringVar(value="0 min")
    estado_texto = tk.StringVar(value="")

    indicadores = [
        ("LIQUIDACIONES", cantidad_texto, COLOR_PRIMARIO),
        ("TOTAL RECAUDADO", total_texto, COLOR_EXITO),
        ("ESTADÍA PROMEDIO", promedio_texto, "#7c3aed"),
    ]
    for columna, (titulo, variable, acento) in enumerate(indicadores):
        tarjeta = tk.Frame(
            tarjetas,
            background=COLOR_TARJETA,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1,
            padx=20,
            pady=16,
        )
        tarjeta.grid(
            row=0,
            column=columna,
            sticky="ew",
            padx=(0 if columna == 0 else 8, 0),
        )
        tk.Frame(tarjeta, background=acento, height=4).pack(fill="x", pady=(0, 13))
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
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w", pady=(5, 0))

    titulo_recientes = tk.Frame(contenido, background=COLOR_FONDO)
    titulo_recientes.grid(row=2, column=0, sticky="ew", padx=30, pady=(24, 10))
    tk.Label(
        titulo_recientes,
        text="Movimientos recientes",
        background=COLOR_FONDO,
        foreground=COLOR_TEXTO,
        font=("Segoe UI", 14, "bold"),
    ).pack(side="left")
    tk.Label(
        titulo_recientes,
        textvariable=estado_texto,
        background=COLOR_FONDO,
        foreground=COLOR_SECUNDARIO,
        font=("Segoe UI", 9),
    ).pack(side="right")

    marco_tabla = tk.Frame(
        contenido,
        background=COLOR_TARJETA,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1,
    )
    marco_tabla.grid(row=3, column=0, sticky="nsew", padx=30, pady=(0, 30))
    marco_tabla.columnconfigure(0, weight=1)
    marco_tabla.rowconfigure(0, weight=1)

    columnas = ("fecha", "patente", "vehiculo", "duracion", "total", "origen")
    tabla = ttk.Treeview(
        marco_tabla,
        columns=columnas,
        show="headings",
        style="Historial.Treeview",
        height=8,
    )
    encabezados_tabla = {
        "fecha": "FECHA",
        "patente": "PATENTE",
        "vehiculo": "VEHÍCULO",
        "duracion": "DURACIÓN",
        "total": "TOTAL",
        "origen": "ORIGEN",
    }
    anchos_tabla = {
        "fecha": 150,
        "patente": 105,
        "vehiculo": 115,
        "duracion": 105,
        "total": 105,
        "origen": 90,
    }
    for columna in columnas:
        tabla.heading(columna, text=encabezados_tabla[columna])
        tabla.column(
            columna,
            width=anchos_tabla[columna],
            minwidth=75,
            anchor="center",
            stretch=True,
        )
    tabla.tag_configure("par", background="#f8fafc")
    tabla.tag_configure("impar", background=COLOR_TARJETA)
    tabla.grid(row=0, column=0, sticky="nsew")

    barra = ttk.Scrollbar(marco_tabla, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=barra.set)
    barra.grid(row=0, column=1, sticky="ns")

    def actualizar_dashboard():
        """Recarga indicadores y operaciones recientes desde los CSV."""
        try:
            registros = cargar_historial_liquidaciones()
            estado_texto.set("Datos actualizados")
        except ErrorArchivoDatos as error:
            registros = []
            estado_texto.set(f"No se pudieron cargar los datos: {error}")

        cantidad = len(registros)
        total = sum(registro["total"] for registro in registros)
        promedio = (
            round(sum(registro["duracion_minutos"] for registro in registros) / cantidad)
            if cantidad
            else 0
        )
        cantidad_texto.set(str(cantidad))
        total_texto.set(f"${total:,.0f}".replace(",", "."))
        promedio_texto.set(f"{promedio} min")

        tabla.delete(*tabla.get_children())
        recientes = sorted(registros, key=lambda registro: registro["fecha"], reverse=True)
        for indice, registro in enumerate(recientes[:10]):
            duracion = (
                f"{registro['dias']} día(s)"
                if registro["dias"] > 0
                else f"{registro['minutos_estadia']} min"
            )
            tabla.insert(
                "",
                "end",
                values=(
                    str(registro["fecha"]).replace("T", " ")[:16],
                    registro["patente"],
                    registro["tipo_vehiculo"].capitalize(),
                    duracion,
                    f"${registro['total']:,.0f}".replace(",", "."),
                    registro["origen"],
                ),
                tags=("par" if indice % 2 == 0 else "impar",),
            )

    def ejecutar_accion(accion):
        """Abre una sección y refresca el panel cuando esa ventana se cierra."""
        ventana_secundaria = accion()
        if ventana_secundaria is not None:
            ventana.wait_window(ventana_secundaria)
        actualizar_dashboard()

    BotonRedondeado(
        lateral,
        texto="Nueva liquidación",
        comando=lambda: ejecutar_accion(lambda: abrir_liquidacion_manual(ventana)),
        ancho=185,
        alto=46,
    ).pack(padx=25, pady=(0, 12))

    BotonRedondeado(
        lateral,
        texto="Procesar archivo JSON",
        comando=lambda: ejecutar_accion(
            lambda: procesar_movimientos_desde_interfaz(ventana)
        ),
        ancho=185,
        alto=46,
    ).pack(padx=25, pady=(0, 12))

    BotonRedondeado(
        lateral,
        texto="Historial y reportes",
        comando=lambda: ejecutar_accion(lambda: abrir_historial(ventana)),
        color="#334155",
        color_activo="#475569",
        ancho=185,
        alto=46,
    ).pack(padx=25, pady=(0, 12))

    tk.Label(
        lateral,
        text="Los reportes CSV se guardan\nen la carpeta del proyecto.",
        background=color_lateral,
        foreground=color_lateral_secundario,
        font=("Segoe UI", 9),
        justify="left",
    ).pack(side="bottom", anchor="w", padx=25, pady=28)

    actualizar_dashboard()

    # Mantiene la ventana abierta y atiende clics y otras interacciones.
    ventana.mainloop()


# Este control inicia el programa solamente al ejecutar directamente main.py.
# Si otro archivo importa main, la ventana no se abrirá automáticamente.
if __name__ == "__main__":
    main()
