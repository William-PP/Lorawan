"""
pruebas_rle.py

Pruebas del paquete compresionRLE, sin Huffman.
Ejecutar desde la raíz del proyecto:
    python -B -m tests.pruebas_rle
"""
import unittest

from compresionRLE.pipeline import preparar, reconstruir
from compresionRLE.serializador import deserializar, serializar

NUM = 5
EJEMPLO = "7.0&0&25.00&1&300|7.0&60&25.01&1&301|7.1&120&25.00&1&300|7.0&180&25.02&1&299|"
TEXTO_ESPERADO = (
    "4|"
    "7.0:2&7.1:1&7.0:1|"
    "0:1&60:1&120:1&180:1|"
    "25.00:1&25.01:1&25.00:1&25.02:1|"
    "1:4|"
    "300:1&301:1&300:1&299:1|"
)


class TestPreparar(unittest.TestCase):
    def test_formato_serializado_esperado(self):
        self.assertEqual(preparar(EJEMPLO, NUM), TEXTO_ESPERADO)

    def test_ida_y_vuelta(self):
        self.assertEqual(reconstruir(preparar(EJEMPLO, NUM), NUM), EJEMPLO)

    def test_una_sola_lectura(self):
        b = "7.0&0&25.00&1&300|"
        self.assertEqual(reconstruir(preparar(b, NUM), NUM), b)

    def test_lecturas_identicas(self):
        b = "7.0&0&25.00&1&300|" * 5
        self.assertEqual(reconstruir(preparar(b, NUM), NUM), b)

    def test_anchos_variables(self):
        b = "7.0&192&29.01&1&300|7.1&12345&29.05&1&4|7.2&9999999&29.00&1&99999|"
        self.assertEqual(reconstruir(preparar(b, NUM), NUM), b)


class TestErrores(unittest.TestCase):
    def test_lectura_con_campos_de_menos(self):
        with self.assertRaises(ValueError):
            preparar("7.0&0&25.00|", NUM)

    def test_bloque_sin_separador_final(self):
        with self.assertRaises(ValueError):
            preparar("7.0&0&25.00&1&300", NUM)

    def test_bloque_vacio(self):
        with self.assertRaises(ValueError):
            preparar("", NUM)

    def test_texto_con_n_incorrecto(self):
        texto = TEXTO_ESPERADO.replace("4|", "9|", 1)
        with self.assertRaises(ValueError):
            reconstruir(texto, NUM)

    def test_numero_de_columnas_incorrecto(self):
        with self.assertRaises(ValueError):
            deserializar("4|7.0:4|", NUM)


class TestSerializador(unittest.TestCase):
    def test_serializar_y_deserializar(self):
        columnas = [[("a", 2), ("b", 1)], [("1", 3)]]
        texto = serializar(3, columnas)
        self.assertEqual(deserializar(texto, 2), (3, columnas))


if __name__ == "__main__":
    unittest.main(verbosity=2)
