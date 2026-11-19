import subprocess


class ImpresoraTexsonMac:
    def __init__(self, nombre_impresora: str | None = None, ancho: int = 32):
        # Si nombre_impresora es None, usará la impresora predeterminada de tu Mac
        self.nombre_impresora = nombre_impresora
        self.ancho = ancho

    def _centrar(self, texto: str) -> str:
        return texto[: self.ancho].center(self.ancho)

    def _linea_izq_der(self, izq: str, der: str) -> str:
        espacios = self.ancho - len(izq) - len(der)
        if espacios < 1:
            izq = izq[: max(0, self.ancho - len(der) - 1)]
            espacios = 1
        return f"{izq}{' ' * espacios}{der}"

    def construir_ticket_prueba(self) -> str:
        sep = "-" * self.ancho
        lineas = [
            self._centrar("MI NEGOCIO POS"),
            self._centrar("TICKET DE PRUEBA"),
            sep,
            self._linea_izq_der("2x Refresco", "$36.00"),
            self._linea_izq_der("1x Pan dulce", "$14.00"),
            sep,
            self._linea_izq_der("TOTAL:", "$50.00"),
            sep,
            self._centrar("Gracias por su compra"),
            "\n\n\n",
        ]
        return "\n".join(lineas)

    def imprimir_texto(self, texto: str):
        comando = ["lp"]
        if self.nombre_impresora:
            comando.extend(["-d", self.nombre_impresora])

        # Codificamos en latin-1 / cp850 para evitar errores con acentos o $
        datos = texto.encode("latin-1", errors="replace")

        proceso = subprocess.run(
            comando,
            input=datos,
            capture_output=True,
        )
        if proceso.returncode != 0:
            error_msg = proceso.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"Error al imprimir en Mac: {error_msg}")


if __name__ == "__main__":
    # Cambia "None" por el nombre de tu impresora si quieres ser específica, ej: "POS-58"
    impresora = ImpresoraTexsonMac(nombre_impresora=None, ancho=32)
    ticket = impresora.construir_ticket_prueba()
    impresora.imprimir_texto(ticket)
    print("Listo: se envió el ticket de prueba.")
