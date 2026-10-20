# unittest forma parte de Python y permite automatizar casos de prueba.
import csv
import json
import tempfile
import unittest
from pathlib import Path

from archivos import (
    ErrorArchivoDatos,
    cargar_json,
    cargar_tarifas,
    guardar_liquidacion_manual,
    validar_estructura_movimientos,
    validar_estructura_tarifas,
)
from calculos import calcular_estacionamiento_recursivo, calcular_liquidacion
from procesamiento import procesar_lote
from validaciones import (
    ErrorValidacion,
    normalizar_patente,
    validar_datos_liquidacion,
    validar_hora,
    validar_movimiento,
    validar_patente,
)


class PruebasValidaciones(unittest.TestCase):
    """Comprueba formatos, normalización y coherencia de los datos."""

    def test_normaliza_patente_con_espacios_y_minusculas(self):
        self.assertEqual(normalizar_patente(" bf 901 gg "), "BF901GG")

    def test_acepta_los_dos_formatos_de_patente(self):
        self.assertTrue(validar_patente("ABC123"))
        self.assertTrue(validar_patente("AB123CD"))

    def test_rechaza_patente_invalida(self):
        self.assertFalse(validar_patente("PATENTE99"))

    def test_valida_limites_de_horarios(self):
        self.assertTrue(validar_hora("00:00"))
        self.assertTrue(validar_hora("23:59"))
        self.assertFalse(validar_hora("24:00"))
        self.assertFalse(validar_hora("12:60"))
        self.assertFalse(validar_hora("8:30"))

    def test_rechaza_salida_anterior_a_entrada(self):
        with self.assertRaises(ErrorValidacion):
            validar_datos_liquidacion(
                "AB123CD", "auto", "18:00", "15:00", "0", False
            )

    def test_estadia_prolongada_no_necesita_horarios(self):
        datos = validar_datos_liquidacion(
            "AB123CD", "auto", "", "", "2", True
        )
        self.assertEqual(datos["dias"], 2)

    def test_rechaza_tipo_de_vehiculo_desconocido(self):
        with self.assertRaises(ErrorValidacion):
            validar_datos_liquidacion(
                "AB123CD", "tractor", "08:00", "09:00", "0", False
            )

    def test_rechaza_movimiento_con_campos_faltantes(self):
        with self.assertRaises(ErrorValidacion):
            validar_movimiento({"id": "MOV001", "patente": "AB123CD"})


class PruebasCalculos(unittest.TestCase):
    """Comprueba bloques, recursividad, lavado, topes y días completos."""

    @classmethod
    def setUpClass(cls):
        cls.tarifas = cargar_tarifas()

    def test_limites_de_la_funcion_recursiva(self):
        casos_auto = {
            1: 700,
            30: 700,
            31: 1400,
            60: 1400,
            120: 2800,
            121: 4000,
            180: 4000,
            181: 5200,
        }

        for minutos, esperado in casos_auto.items():
            with self.subTest(minutos=minutos):
                obtenido = calcular_estacionamiento_recursivo(
                    minutos, "auto", self.tarifas
                )
                self.assertEqual(obtenido, esperado)

    def _liquidar(self, entrada="", salida="", dias="0", lavado=False):
        datos = validar_datos_liquidacion(
            "AB123CD",
            "auto",
            entrada,
            salida,
            dias,
            lavado,
        )
        return calcular_liquidacion(datos, self.tarifas)

    def test_lavado_bonifica_estadia_de_hasta_120_minutos(self):
        resultado = self._liquidar("08:00", "09:30", lavado=True)
        self.assertEqual(resultado["importe_base"], 2100)
        self.assertEqual(resultado["bonificacion"], 2100)
        self.assertEqual(resultado["costo_estacionamiento"], 0)
        self.assertEqual(resultado["total"], 5000)

    def test_lavado_cobra_solamente_el_excedente(self):
        resultado = self._liquidar("08:00", "10:30", lavado=True)
        self.assertEqual(resultado["importe_base"], 4000)
        self.assertEqual(resultado["bonificacion"], 2800)
        self.assertEqual(resultado["costo_estacionamiento"], 1200)
        self.assertEqual(resultado["total"], 6200)

    def test_aplica_tope_diario(self):
        resultado = self._liquidar("00:00", "23:59")
        self.assertEqual(resultado["costo_estacionamiento"], 16000)

    def test_calcula_dias_completos_con_lavado(self):
        resultado = self._liquidar(dias="2", lavado=True)
        self.assertEqual(resultado["importe_base"], 32000)
        self.assertEqual(resultado["costo_lavado"], 5000)
        self.assertEqual(resultado["total"], 37000)

    def test_desglose_contable_concilia_con_total(self):
        resultado = self._liquidar("08:00", "10:30", lavado=True)
        total_calculado = (
            resultado["importe_base"]
            - resultado["bonificacion"]
            + resultado["costo_lavado"]
        )
        self.assertEqual(total_calculado, resultado["total"])


class PruebasArchivos(unittest.TestCase):
    """Comprueba archivos faltantes, corruptos y estructuras inválidas."""

    def test_rechaza_archivo_inexistente(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "inexistente.json"
            with self.assertRaises(ErrorArchivoDatos):
                cargar_json(ruta)

    def test_rechaza_json_vacio(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "vacio.json"
            ruta.write_text("", encoding="utf-8")
            with self.assertRaises(ErrorArchivoDatos):
                cargar_json(ruta)

    def test_rechaza_json_corrupto(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "corrupto.json"
            ruta.write_text('{"movimientos": [1, 2,}', encoding="utf-8")
            with self.assertRaises(ErrorArchivoDatos):
                cargar_json(ruta)

    def test_rechaza_tarifas_incompletas(self):
        with self.assertRaises(ErrorArchivoDatos):
            validar_estructura_tarifas({"configuracion": {}, "tarifas": {}})

    def test_rechaza_fecha_imposible(self):
        datos = {"fecha_operacion": "2026-02-30", "movimientos": []}
        with self.assertRaises(ErrorArchivoDatos):
            validar_estructura_movimientos(datos)

    def test_csv_manual_acumula_sin_duplicar_encabezado(self):
        tarifas = cargar_tarifas()
        datos = validar_datos_liquidacion(
            "AB123CD", "auto", "08:00", "09:00", "0", False
        )
        resultado = calcular_liquidacion(datos, tarifas)

        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "manual.csv"
            guardar_liquidacion_manual(resultado, ruta)
            guardar_liquidacion_manual(resultado, ruta)

            with ruta.open(encoding="utf-8", newline="") as archivo:
                filas = list(csv.DictReader(archivo))

            self.assertEqual(len(filas), 2)
            self.assertEqual(filas[0]["patente"], "AB123CD")


class PruebasProcesamiento(unittest.TestCase):
    """Comprueba que un registro incorrecto no detenga todo el lote."""

    def test_separa_validos_rechazados_y_duplicados(self):
        movimientos = {
            "fecha_operacion": "2026-10-20",
            "movimientos": [
                {
                    "id": "MOV001",
                    "patente": "AB123CD",
                    "tipo_vehiculo": "auto",
                    "hora_entrada": "08:00",
                    "hora_salida": "09:00",
                    "lavado": False,
                },
                {
                    "id": "MOV002",
                    "patente": "PATENTE99",
                    "tipo_vehiculo": "auto",
                    "hora_entrada": "08:00",
                    "hora_salida": "09:00",
                    "lavado": False,
                },
                {
                    "id": "MOV001",
                    "patente": "AC234DD",
                    "tipo_vehiculo": "moto",
                    "hora_entrada": "10:00",
                    "hora_salida": "11:00",
                    "lavado": False,
                },
            ],
        }

        with tempfile.TemporaryDirectory() as carpeta:
            carpeta = Path(carpeta)
            salida = carpeta / "liquidacion.csv"
            rechazados = carpeta / "rechazados.csv"

            resumen = procesar_lote(
                datos_tarifas=cargar_tarifas(),
                datos_movimientos=movimientos,
                ruta_liquidacion=salida,
                ruta_rechazados=rechazados,
            )

            self.assertEqual(resumen["procesados"], 1)
            self.assertEqual(resumen["rechazados"], 2)

            with rechazados.open(encoding="utf-8", newline="") as archivo:
                filas_rechazadas = list(csv.DictReader(archivo))

            motivos = " ".join(fila["motivo"] for fila in filas_rechazadas)
            self.assertIn("patente", motivos.lower())
            self.assertIn("duplicado", motivos.lower())


if __name__ == "__main__":
    # Permite ejecutar directamente: python tests/test_autopark.py
    unittest.main(verbosity=2)
