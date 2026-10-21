# AutoPark

Aplicación de escritorio en Python para liquidar estadías de estacionamiento, aplicar el beneficio por lavado y procesar movimientos desde archivos JSON.

## Requisitos

- Python 3.10 o posterior.
- Tkinter, incluido normalmente con Python en Windows.
- No requiere instalar paquetes externos.

Para comprobar que Tkinter está disponible:

```powershell
python -c "import tkinter; print(tkinter.TkVersion)"
```

## Estructura

```text
parcial2/
├── autopark/
│   ├── tests/
│   │   └── test_autopark.py
│   ├── archivos.py
│   ├── calculos.py
│   ├── interfaz.py
│   ├── main.py
│   ├── procesamiento.py
│   └── validaciones.py
├── movimientos.json
├── tarifas.json
├── README.md
└── .gitignore
```

Los reportes CSV se crean automáticamente en la carpeta `parcial2`.
Los tres CSV incluidos en el repositorio contienen datos de prueba para poder
recorrer el dashboard y el historial sin realizar una carga previa. Pueden
regenerarse desde la aplicación.

## Ejecución

Desde la carpeta `parcial2`:

```powershell
python autopark/main.py
```

También se puede ejecutar desde `autopark`:

```powershell
python main.py
```

Las rutas se calculan a partir de la ubicación de los archivos. No es necesario modificar el código cuando el proyecto se copia a otra computadora.

## Liquidación manual

La opción **Liquidación manual** permite ingresar:

- Patente tradicional `ABC123` o Mercosur `AB123CD`.
- Tipo de vehículo: moto, auto o camioneta.
- Tipo de estadía: mismo día o días completos.
- Hora de entrada y salida para estadías del mismo día.
- Cantidad de días para estadías prolongadas.
- Servicio de lavado opcional.

Si los datos son correctos, muestra:

- Duración en minutos o días.
- Importe base.
- Bonificación por lavado.
- Estacionamiento a cobrar.
- Precio del lavado.
- Total.

Cada operación se agrega a `liquidacion-manual.csv` sin eliminar registros anteriores.

## Procesamiento por lote

La opción **Procesar movimientos**:

1. Lee `tarifas.json` y `movimientos.json`.
2. Valida cada movimiento individualmente.
3. Calcula todos los registros correctos.
4. Continúa aunque encuentre datos inválidos.
5. Genera `liquidacion.csv` con los movimientos válidos.
6. Genera `rechazados.csv` con los movimientos descartados y su motivo.
7. Muestra procesados, rechazados y total recaudado.

Los reportes del lote se reemplazan en cada ejecución porque representan el contenido actual de `movimientos.json`.

## Historial de liquidaciones

La opción **Ver historial** consolida en una sola tabla las operaciones de
`liquidacion-manual.csv` y `liquidacion.csv`. Permite:

- Ver todas las cargas manuales y del lote.
- Buscar por patente, incluso escribiéndola parcialmente.
- Consultar la cantidad de estadías encontradas.
- Consultar el total pagado y el promedio de minutos por estadía.
- Identificar la fecha, el vehículo, la duración, el lavado y el origen de cada fila.
- Combinar filtros por patente, vehículo, lavado, origen y rango de fechas.
- Exportar a un nuevo CSV solamente los registros que coinciden con los filtros.

Al exportar, el selector de guardado se abre inicialmente en el Escritorio del
usuario. La ruta se detecta automáticamente y también contempla escritorios
sincronizados mediante OneDrive.

Si los reportes todavía no existen, la pantalla muestra un historial vacío sin producir un error.

## Reglas de cálculo

### Primeras dos horas

Los primeros 120 minutos se cobran en bloques de 30 minutos o fracción.

### Tiempo adicional

Después de 120 minutos se cobra una hora adicional por cada bloque de 60 minutos o fracción.

### Tope diario

El costo de estacionamiento del mismo día no puede superar el `tope_dia` correspondiente al vehículo.

### Días completos

Una estadía prolongada cuesta:

```text
cantidad de días × tope diario
```

No requiere horarios.

### Lavado

- Hasta 120 minutos: el estacionamiento queda totalmente bonificado.
- Más de 120 minutos: se cobra el lavado y únicamente el tiempo excedente.
- Varios días: se cobran los días completos más un servicio de lavado.

El desglose cumple:

```text
importe base - bonificación + lavado = total
```

## Recursividad obligatoria

La función se encuentra en `autopark/calculos.py`:

```python
calcular_estacionamiento_recursivo(
    minutos_restantes,
    tipo_vehiculo,
    datos_tarifas,
    minutos_cobrados=0,
)
```

Su caso base retorna cero cuando no quedan minutos. En cada paso recursivo resta un bloque de 30 o 60 minutos y suma su precio. No utiliza ciclos para calcular el tiempo estacionado.

## Validaciones y errores controlados

El sistema controla:

- Patentes con formato incorrecto.
- Vehículos desconocidos.
- Horarios inexistentes o con formato incorrecto.
- Salidas anteriores o iguales a la entrada.
- Días negativos, decimales o escritos como texto.
- Campos faltantes en movimientos.
- Identificadores duplicados.
- JSON inexistentes, vacíos o corruptos.
- Codificación diferente de UTF-8.
- Tarifas incompletas, negativas o con tipos incorrectos.
- Fechas inexistentes.
- Archivos CSV abiertos o sin permisos de escritura.

Un movimiento inválido se registra en `rechazados.csv` y no detiene el resto del lote.

## Pruebas

Desde la carpeta `autopark`:

```powershell
python -m unittest discover -s tests -v
```

Las pruebas utilizan archivos temporales para no modificar los JSON ni los reportes reales. Cubren validaciones, límites tarifarios, recursividad, lavado, topes, días completos, JSON corruptos y separación entre movimientos válidos y rechazados.

## Archivos principales

- `main.py`: inicia la aplicación y configura los estilos.
- `interfaz.py`: contiene las ventanas y controles gráficos.
- `validaciones.py`: normaliza y valida los datos.
- `archivos.py`: lee JSON y escribe CSV.
- `calculos.py`: contiene las reglas tarifarias y la recursividad.
- `procesamiento.py`: coordina el procesamiento por lote.
- `tests/test_autopark.py`: contiene las pruebas automáticas.
