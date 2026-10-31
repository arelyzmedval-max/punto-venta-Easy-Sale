import flet as ft
from datetime import datetime


class CajaView(ft.Container):
    def __init__(self, page: ft.Page, db, usuario):
        super().__init__(expand=True)
        self.page_ref = page
        self.db = db
        self.usuario = usuario

        self.txt_fondo_inicial = ft.TextField(
            label="Fondo Inicial en Efectivo ($)",
            keyboard_type=ft.KeyboardType.NUMBER,
            value="500.00",
            width=300
        )

        self.txt_dinero_real = ft.TextField(
            label="Dinero contado físicamente en caja ($)",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=300,
            visible=False
        )

        self.lbl_estado_caja = ft.Text("Verificando estado de caja...", size=16, weight=ft.FontWeight.BOLD)
        self.lbl_info_turno = ft.Text("", size=14)

        self.btn_accion = ft.ElevatedButton(
            content=ft.Text("Abrir Caja"),
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
            on_click=self.accion_caja
        )

        self.content = ft.Container(
            padding=30,
            content=ft.Column([
                ft.Text("Gestión de Caja y Corte", size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.lbl_estado_caja,
                self.lbl_info_turno,
                ft.Container(height=20),
                self.txt_fondo_inicial,
                self.txt_dinero_real,
                ft.Container(height=10),
                self.btn_accion
            ], spacing=15, scroll=ft.ScrollMode.AUTO)
        )

        self.verificar_caja_activa()

    def verificar_caja_activa(self):
        query = "SELECT * FROM caja WHERE id_usuario = %s AND estado = 'ABIERTA' LIMIT 1"
        res = self.db.obtener_resultados(query, (self.usuario['id_usuario'],))

        if res:
            self.caja_actual = res[0]
            self.lbl_estado_caja.value = "🟢 Caja Abierta y Activa"
            self.lbl_info_turno.value = f"Apertura: {self.caja_actual['fecha_apertura']} | Fondo Inicial: ${float(self.caja_actual['monto_inicial']):.2f}"
            self.txt_fondo_inicial.visible = False
            self.txt_dinero_real.visible = True
            self.btn_accion.content = ft.Text("Realizar Corte de Caja (Cierre)")
            self.btn_accion.bgcolor = ft.Colors.RED_700
        else:
            self.caja_actual = None
            self.lbl_estado_caja.value = "🔴 No hay caja abierta"
            self.lbl_info_turno.value = "Ingrese el fondo inicial para comenzar su turno."
            self.txt_fondo_inicial.visible = True
            self.txt_dinero_real.visible = False
            self.btn_accion.content = ft.Text("Abrir Caja")
            self.btn_accion.bgcolor = ft.Colors.GREEN_700

        self.page_ref.update()

    def accion_caja(self, e):
        if not self.caja_actual:
            # Abrir caja
            try:
                fondo = float(self.txt_fondo_inicial.value)
            except ValueError:
                self.mostrar_snack("⚠️ Ingrese un monto inicial válido", ft.Colors.RED_700)
                return

            query = "INSERT INTO caja (id_usuario, monto_inicial, fecha_apertura, estado) VALUES (%s, %s, %s, 'ABIERTA')"
            self.db.ejecutar_query(query, (self.usuario['id_usuario'], fondo, datetime.now()))
            self.mostrar_snack("✅ Caja abierta correctamente", ft.Colors.GREEN_700)
            self.verificar_caja_activa()
        else:
            # Hacer Corte (Cierre)
            try:
                dinero_fisico = float(self.txt_dinero_real.value)
            except ValueError:
                self.mostrar_snack("⚠️ Ingrese el monto físico contado en caja", ft.Colors.RED_700)
                return

            # Calcular ventas uniendo con la tabla metodos_pago para identificar correctamente efectivo, tarjeta, transferencia
            q_ventas = """
                SELECT m.metodo, SUM(v.total_venta) as total 
                FROM ventas v
                JOIN metodos_pago m ON v.metodo_pago_id = m.id_metodo
                WHERE v.id_usuario = %s AND v.fecha >= %s 
                GROUP BY m.metodo
            """
            res_v = self.db.obtener_resultados(q_ventas,
                                               (self.usuario['id_usuario'], self.caja_actual['fecha_apertura']))

            totales_por_metodo = {'Efectivo': 0.0, 'Tarjeta': 0.0, 'Transferencia': 0.0}
            if res_v:
                for row in res_v:
                    metodo = row.get('metodo')
                    total = float(row.get('total') or 0.0)
                    for key in totales_por_metodo:
                        if key.lower() in metodo.lower():
                            totales_por_metodo[key] = total

            ventas_efectivo = totales_por_metodo['Efectivo']
            ventas_tarjeta = totales_por_metodo['Tarjeta']
            ventas_transferencia = totales_por_metodo['Transferencia']

            total_ventas = ventas_efectivo + ventas_tarjeta + ventas_transferencia
            fondo_inicial = float(self.caja_actual['monto_inicial'])

            # El dinero físico esperado solo suma el fondo inicial + efectivo
            esperado_efectivo = fondo_inicial + ventas_efectivo
            diferencia = dinero_fisico - esperado_efectivo

            q_cierre = """
                UPDATE caja SET monto_final = %s, total_ventas = %s, diferencia = %s, 
                fecha_cierre = %s, estado = 'CERRADA' WHERE id_caja = %s
            """
            self.db.ejecutar_query(q_cierre, (
                dinero_fisico, total_ventas, diferencia, datetime.now(), self.caja_actual['id_caja']
            ))

            self.mostrar_resumen_corte(fondo_inicial, ventas_efectivo, ventas_tarjeta, ventas_transferencia,
                                       total_ventas, dinero_fisico, diferencia)
            self.verificar_caja_activa()

    def mostrar_resumen_corte(self, fondo, efec, tarj, transf, total_v, real, dif):
        def cerrar_dialogo(e):
            if modal_resumen in self.page_ref.overlay:
                self.page_ref.overlay.remove(modal_resumen)
            self.page_ref.update()

        modal_resumen = ft.Stack([
            ft.Container(bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK), expand=True, on_click=cerrar_dialogo),
            ft.Row([
                ft.Container(
                    bgcolor=ft.Colors.WHITE,
                    padding=25,
                    border_radius=10,
                    width=420,
                    content=ft.Column([
                        ft.Text("🔒 Reporte de Corte de Caja", size=18, weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        ft.Text(f"Fondo Inicial: ${fondo:.2f}"),
                        ft.Text(f"Ventas en Efectivo: ${efec:.2f}", color=ft.Colors.GREEN_800),
                        ft.Text(f"Ventas con Tarjeta: ${tarj:.2f}", color=ft.Colors.BLUE_800),
                        ft.Text(f"Ventas por Transferencia: ${transf:.2f}", color=ft.Colors.PURPLE_800),
                        ft.Divider(),
                        ft.Text(f"Total Ingresos del Día: ${total_v:.2f}", weight=ft.FontWeight.BOLD),
                        ft.Text(f"Dinero Físico Contado: ${real:.2f}"),
                        ft.Text(f"Diferencia en Efectivo: ${dif:.2f}", weight=ft.FontWeight.BOLD,
                                color=ft.Colors.RED_700 if dif < 0 else ft.Colors.GREEN_700),
                        ft.Container(height=10),
                        ft.Row([
                            ft.ElevatedButton("Aceptar", bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE,
                                              on_click=cerrar_dialogo)
                        ], alignment=ft.MainAxisAlignment.END)
                    ], tight=True, spacing=10)
                )
            ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
        ])

        self.page_ref.overlay.append(modal_resumen)
        self.page_ref.update()

    def mostrar_snack(self, texto, color):
        snack = ft.SnackBar(content=ft.Text(texto, color=ft.Colors.WHITE), bgcolor=color, open=True)
        self.page_ref.overlay.append(snack)
        self.page_ref.update()