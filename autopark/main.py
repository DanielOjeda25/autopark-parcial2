
# Tkinter contiene los componentes básicos para crear ventanas.
import tkinter as tk
# ttk ofrece versiones de los componentes con estilos modernos.
from tkinter import ttk

# Importamos la función que abre el formulario desde el otro archivo.
from interfaz import (
    BotonRedondeado,
    abrir_liquidacion_manual,
    centrar_ventana,
    procesar_movimientos_desde_interfaz,
)


# Colores reutilizables de la aplicación. Al definirlos aquí podemos cambiar
# toda la apariencia sin buscar cada color por separado.
COLOR_FONDO = "#eef3f8"
COLOR_TARJETA = "#ffffff"
COLOR_PRIMARIO = "#2563eb"
COLOR_PRIMARIO_ACTIVO = "#1d4ed8"
COLOR_TEXTO = "#172033"
COLOR_SECUNDARIO = "#64748b"


def configurar_estilos(ventana):
    """Configura los estilos visuales que usarán las dos ventanas."""
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
        background="#e2e8f0",
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
        fieldbackground="#f8fafc",
        bordercolor="#cbd5e1",
        lightcolor="#cbd5e1",
        darkcolor="#cbd5e1",
    )
    estilo.configure(
        "Campo.TCombobox",
        padding=(10, 8),
        fieldbackground="#f8fafc",
        background="#f8fafc",
        bordercolor="#cbd5e1",
        arrowcolor=COLOR_TEXTO,
    )
    # Selectores utilizados para elegir horas y minutos sin escribir texto libre.
    estilo.configure(
        "Hora.TSpinbox",
        padding=(7, 8),
        fieldbackground="#f8fafc",
        bordercolor="#cbd5e1",
        arrowcolor=COLOR_TEXTO,
        font=("Segoe UI", 10),
    )
    estilo.map(
        "Campo.TEntry",
        bordercolor=[("focus", COLOR_PRIMARIO)],
        lightcolor=[("focus", COLOR_PRIMARIO)],
        darkcolor=[("focus", COLOR_PRIMARIO)],
    )


def main():
    """Crea la ventana principal e inicia la aplicación AutoPark."""
    # Tk crea la ventana raíz. La aplicación debe tener una sola ventana raíz.
    ventana = tk.Tk()

    # Configuración general de la ventana principal.
    ventana.title("AutoPark")
    ventana.geometry("760x520")
    ventana.resizable(False, False)
    ventana.configure(background=COLOR_FONDO)
    # Centramos la ventana después de establecer sus dimensiones.
    centrar_ventana(ventana)
    # Aplicamos los estilos antes de crear los componentes ttk.
    configurar_estilos(ventana)

    # Franja superior azul utilizada como encabezado.
    encabezado = tk.Frame(ventana, background=COLOR_PRIMARIO, height=90)
    encabezado.pack(fill="x")
    # Evita que el encabezado cambie de altura según su contenido.
    encabezado.pack_propagate(False)

    # Nombre de la aplicación colocado dentro del encabezado.
    tk.Label(
        encabezado,
        text="AUTOPARK",
        background=COLOR_PRIMARIO,
        foreground="white",
        font=("Segoe UI", 18, "bold"),
    ).pack(side="left", padx=35, pady=25)

    # Contenedor blanco donde se muestran las acciones principales.
    tarjeta = tk.Frame(
        ventana,
        background=COLOR_TARJETA,
        highlightbackground="#dbe3ec",
        highlightthickness=1,
    )
    tarjeta.pack(padx=90, pady=45, fill="both", expand=True)

    # Título y texto explicativo de la pantalla principal.
    titulo = ttk.Label(tarjeta, text="Gestión de estacionamiento", style="Titulo.TLabel")
    titulo.pack(pady=(45, 8))

    subtitulo = ttk.Label(
        tarjeta,
        text="Selecciona una opción para comenzar",
        style="Subtitulo.TLabel",
    )
    subtitulo.pack(pady=(0, 30))

    # Las dos acciones principales se presentan juntas para que tengan la
    # misma jerarquía visual y sean más fáciles de localizar.
    acciones = tk.Frame(tarjeta, background=COLOR_TARJETA)
    acciones.pack(pady=(8, 28))

    boton_manual = BotonRedondeado(
        acciones,
        texto="Liquidación manual",
        comando=lambda: abrir_liquidacion_manual(ventana),
        ancho=220,
        alto=50,
    )
    boton_manual.grid(row=0, column=0, padx=10)

    boton_procesar = BotonRedondeado(
        acciones,
        texto="Procesar movimientos",
        comando=lambda: procesar_movimientos_desde_interfaz(ventana),
        color="#0f766e",
        color_activo="#115e59",
        ancho=220,
        alto=50,
    )
    boton_procesar.grid(row=0, column=1, padx=10)

    tk.Label(
        acciones,
        text="Carga una operación",
        background=COLOR_TARJETA,
        foreground=COLOR_SECUNDARIO,
        font=("Segoe UI", 9),
    ).grid(row=1, column=0, pady=(7, 0))

    tk.Label(
        acciones,
        text="Genera los reportes CSV",
        background=COLOR_TARJETA,
        foreground=COLOR_SECUNDARIO,
        font=("Segoe UI", 9),
    ).grid(row=1, column=1, pady=(7, 0))

    # Mantiene la ventana abierta y atiende clics y otras interacciones.
    ventana.mainloop()


# Este control inicia el programa solamente al ejecutar directamente main.py.
# Si otro archivo importa main, la ventana no se abrirá automáticamente.
if __name__ == "__main__":
    main()
