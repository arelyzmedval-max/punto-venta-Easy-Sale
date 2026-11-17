import flet as ft

class CajaView(ft.Container):
    def __init__(self, page: ft.Page, db, usuario):
        super().__init__(expand=True)
        self.page_ref = page
        self.db = db
        self.usuario = usuario
        
        self.crear_interfaz()
        self.verificar_estado_caja()

    def crear_interfaz(self):
        self.txt_fondo_inicial = ft.TextField(
            label="Fondo Inicial en Efectivo ($)",
            value="500.00",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=300
        )

        self.btn_abrir = ft.ElevatedButton(
            text="Abrir Caja",
            icon=ft.icons.LOCK_OPEN,
            bgcolor=ft.colors.GREEN_700,
            color=ft.colors.WHITE,
            on_click=self.abrir_caja
        )

        self.btn_cerrar = ft.ElevatedButton(
            text="Cerrar Caja (Corte)",
            icon=ft.icons.LOCK,
            bgcolor=ft.colors.RED_700,
            color=ft.colors.WHITE,
            on_click=self.cerrar_caja
        )

        self.lbl_estado = ft.Text("Verificando estado de caja...", size=16, weight=ft.FontWeight.BOLD)
        self.lbl_ganancia = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700)
        self.contenedor_acciones = ft.Column(spacing=15)

        self.content = ft.Container(
            padding=20,
            alignment=ft.alignment.top_left,
            content=ft.Column([
                ft.Text("Gestión de Caja y Corte", size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.lbl_estado,
                self.lbl_ganancia,
                ft.Container(height=10),
                self.contenedor_acciones
            ], tight=True, spacing=15, scroll=ft.ScrollMode.AUTO),
            expand=True
        )

    def verificar_estado_caja(self):
        q = "SELECT id_caja, fondo_inicial, fecha_apertura FROM caja WHERE id_usuario = %s AND estado = 'ABIERTA' LIMIT 1"
        caja_activa = self.db.obtener_resultados(q, (self.usuario['id_usuario'],))

        self.contenedor_acciones.controls.clear()

        if caja_activa:
            caja = caja_activa[0]
            fecha_apertura = caja['fecha_apertura']
            
            # Consultar el total vendido y la ganancia neta desde que se abrió esta caja
            q_ventas = """
                SELECT SUM(v.total_venta) as total_vendido,
                       SUM((vd.precio_unitario - p.precio_costoi) * vd.cantidad) as ganancia_neta
                FROM ventas v
                JOIN ventas_detalle vd ON v.id_venta = vd.id_venta
                JOIN productos p ON vd.codigo_producto = p.codigo
                WHERE v.id_usuario = %s AND v.fecha >= %s
            """
            res_stats = self.db.obtener_resultados(q_ventas, (self.usuario['id_usuario'], fecha_apertura))
            
            total_vendido = 0.0
            ganancia_neta = 0.0
            if res_stats and res_stats[0]['total_vendido']:
                total_vendido = float(res_stats[0]['total_vendido'])
                ganancia_neta = float(res_stats[0]['ganancia_neta'] or 0.0)

            self.lbl_estado.value = f"🟢 Caja Abierta el {fecha_apertura} | Fondo Inicial: ${float(caja['fondo_inicial']):.2f} | Vendido en Turno: ${total_vendido:.2f}"
            self.lbl_estado.color = ft.colors.GREEN_700
            
            self.lbl_ganancia.value = f"💰 Ganancia Neta (Utilidad) en este turno: ${ganancia_neta:.2f}"
            self.lbl_ganancia.visible = True

            self.contenedor_acciones.controls.append(self.btn_cerrar)
        else:
            self.lbl_estado.value = "🔴 No hay caja abierta. Ingrese el fondo inicial para comenzar su turno."
            self.lbl_estado.color = ft.colors.RED_700
            self.lbl_ganancia.visible = False
            
            self.contenedor_acciones.controls.extend([
                self.txt_fondo_inicial,
                self.btn_abrir
            ])

        self.page_ref.update()

    def abrir_caja(self, e):
        try:
            fondo = float(self.txt_fondo_inicial.value.replace(",", "."))
            if fondo < 0:
                raise ValueError
        except ValueError:
            self.mostrar_snack("⚠️ Ingrese un fondo inicial válido", ft.colors.RED_700)
            return

        q = "INSERT INTO caja (id_usuario, fondo_inicial, estado) VALUES (%s, %s, 'ABIERTA')"
        self.db.ejecutar_query(q, (self.usuario['id_usuario'], fondo))
        
        self.mostrar_snack("✅ Caja abierta con éxito", ft.colors.GREEN_700)
        self.verificar_estado_caja()

    def cerrar_caja(self, e):
        q = "UPDATE caja SET estado = 'CERRADA', fecha_cierre = NOW() WHERE id_usuario = %s AND estado = 'ABIERTA'"
        self.db.ejecutar_query(q, (self.usuario['id_usuario'],))
        
        self.mostrar_snack("🔒 Caja cerrada (Corte realizado)", ft.colors.ORANGE_800)
        self.verificar_estado_caja()

    def mostrar_snack(self, texto, color):
        snack = ft.SnackBar(content=ft.Text(texto, color=ft.colors.WHITE), bgcolor=color, open=True)
        self.page_ref.overlay.append(snack)
        self.page_ref.update()
