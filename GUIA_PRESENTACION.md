# Guía breve para presentar AutoPark

## Cómo iniciar

En Windows, hacer doble clic en `INICIAR_AUTOPARK.bat`.

También se puede abrir una terminal en esta carpeta y ejecutar:

```powershell
python autopark/main.py
```

## Recorrido sugerido

1. Mostrar el dashboard y explicar que resume las liquidaciones registradas.
2. Abrir **Nueva liquidación** y cargar un vehículo manualmente.
3. Explicar que los campos limitan los datos inválidos antes de calcular.
4. Abrir **Procesar archivo JSON** para demostrar el procesamiento por lote.
5. Aclarar que un movimiento incorrecto se envía a rechazados sin detener los demás.
6. Abrir **Historial y reportes**, aplicar filtros y exportar solamente lo visible.
7. Mostrar en `calculos.py` la función recursiva obligatoria.

## Organización del proyecto

- `autopark/`: código fuente y pruebas automáticas.
- `datos/`: JSON utilizados como entrada.
- `reportes/`: CSV manuales, procesados y rechazados.
- `documentacion/`: enunciado y material entregado por la cátedra.

## Archivos del programa

- `main.py`: inicia el dashboard.
- `interfaz.py`: ventanas y componentes visuales.
- `validaciones.py`: controla formatos y datos de entrada.
- `calculos.py`: aplica tarifas, topes, lavado y recursividad.
- `archivos.py`: lee JSON y escribe CSV.
- `procesamiento.py`: coordina el procesamiento de todos los movimientos.
- `tests/test_autopark.py`: comprueba automáticamente los casos principales.

## Antes de exponer

- Cerrar los CSV si están abiertos en Excel.
- Confirmar que `datos/tarifas.json` y `datos/movimientos.json` estén presentes.
- Ejecutar las pruebas desde `autopark` con:

```powershell
python -m unittest discover -s tests -v
```

Los CSV incluidos son datos de demostración. Procesar nuevamente el JSON reemplaza
los reportes de lote, pero conserva las liquidaciones manuales.
