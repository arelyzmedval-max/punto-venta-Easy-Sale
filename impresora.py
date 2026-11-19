import subprocess


class ImpresoraTexsonMac:
    def __init__(self, nombre_impresora: str | None = "EML_Printer", ancho: int = 32):
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

    def construir_ticket_venta(
        self,
        folio: str,
        fecha: str,
        items: list[dict],
        total: float,
        pago: float = 0.0,
    ) -> str:
        sep = "-" * self.ancho
        lineas = [
            self._centrar("MI NEGOCIO POS"),
            self._centrar("TICKET DE VENTA"),
            sep,
            f"Folio: {folio}"[: self.ancho],
            f"Fecha: {fecha}"[: self.ancho],
            sep,
        ]

        for item in items:
            desc = f"{item.get('cantidad', 1)}x {item.get('nombre', '')}"
            subtotal = float(item.get("subtotal", 0.0))
            lineas.append(self
