import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from database import Database

HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Easy Sale - Punto de Venta (iPad)</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif; margin: 0; background: #f1f5f9; color: #0f172a; }
  header { background: #1e3a8a; color: #fff; padding: 14px 18px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
  header h1 { margin: 0; font-size: 18px; }
  .wrap { max-width: 1080px; margin: 16px auto; padding: 0 14px; display: flex; flex-wrap: wrap; gap: 16px; }
  .col-left { flex: 2; min-width: 320px; }
  .col-right { flex: 1; min-width: 280px; }
  .card { background: #fff; border-radius: 10px; padding: 16px; margin-bottom: 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
  h3 { margin: 0 0 12px 0; font-size: 16px; }
  input, select, button { font-size: 16px; padding: 10px 12px; border-radius: 8px; border: 1px solid #cbd5e1; }
  button { background: #1d4ed8; color: #fff; border: none; font-weight: 600; cursor: pointer; }
  button.green { background: #15803d; width: 100%; padding: 13px; font-size: 17px; }
  button.gray { background: #475569; padding: 7px 11px; font-size: 14px; }
  button.prod-btn { display: block; width: 100%; text-align: left; background: #eff6ff; color: #0f172a; border: 1px solid #bfdbfe; margin-top: 8px; }
  .row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .field { margin-bottom: 12px; }
  .field label { display: block; font-size: 13px; color: #475569; margin-bottom: 4px; font-weight: 600; }
  table { width: 100%; border-collapse: collapse; }
  th, td { border-bottom: 1px solid #e2e8f0; padding: 9px 6px; text-align: left; font-size: 14px; }
  .totales { border-top: 1px solid #cbd5e1; margin-top: 12px; padding-top: 10px; }
  .tot-row { display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 15px; }
  .tot-final { font-size: 20px; font-weight: 700; color: #15803d; }
  .msg { margin-top: 10px; font-weight: 600; font-size: 14px; }
  .sug-box { border: 1px solid #e2e8f0; border-radius: 8px; margin-top: 6px; background: #f8fafc; }
  .sug-item { padding: 9px 12px; border-bottom: 1px solid #e2e8f0; cursor: pointer; font-size: 14px; }
  .sug-item:last-child { border-bottom: none; }
</style>
</head>
<body>
<header>
  <h1>Easy Sale — Punto de Venta (iPad)</h1>
  <div class="row">
    <select id="usuario_id" onchange="cargarMetodos()"></select>
  </div>
</header>

<div class="wrap">
  <div class="col-left">
    <div class="card">
      <h3>Buscar o escanear producto</h3>
      <div class="row">
        <input id="txt_buscar" type="text" placeholder="Código o nombre..." style="flex:1; min-width:180px;" onkeydown="if(event.key==='Enter'){buscarProductos(true);}">
        <button onclick="buscarProductos(true)">Buscar / Agregar</button>
      </div>
      <div id="resultados_prod"></div>
    </div>

    <div class="card">
      <h3>Carrito de venta</h3>
      <table>
        <thead>
          <tr>
            <th>Código</th>
            <th>Producto</th>
            <th>Cant. / Peso</th>
            <th>Precio U.</th>
            <th>Subtotal</th>
            <th></th>
          </tr>
        </thead>
        <tbody id="carrito_body"></tbody>
      </table>
    </div>
  </div>

  <div class="col-right">
    <div class="card">
      <h3>Resumen de venta</h3>

      <div class="field">
        <label>Método de pago</label>
        <select id="metodo_pago" style="width:100%;" onchange="toggleCliente()"></select>
      </div>

      <div class="field" id="bloque_cliente" style="display:none;">
        <label>Cliente (requerido para fiados)</label>
        <input id="txt_cliente" type="text" placeholder="Nombre o teléfono..." style="width:100%;" oninput="buscarClientes()">
        <div id="sug_clientes" class="sug-box" style="display:none;"></div>
        <div id="cliente_elegido" style="font-size:13px; color:#15803d; margin-top:4px; font-weight:600;"></div>
      </div>

      <div class="field">
        <label>Impuesto (%)</label>
        <input id="impuesto" type="number" step="any" value="0" style="width:100%;" oninput="renderCarrito()">
      </div>

      <div class="totales">
        <div class="tot-row"><span>Subtotal:</span><span id="lbl_sub">$0.00</span></div>
        <div class="tot-row"><span>Impuesto:</span><span id="lbl_imp">$0.00</span></div>
        <div class="tot-row tot-final"><span>Total:</span><span id="lbl_tot">$0.00</span></div>
      </div>

      <div style="margin-top:14px;">
        <button class="green" onclick="procesarVenta()">Procesar Venta</button>
      </div>
      <div id="msg" class="msg"></div>
    </div>
  </div>
</div>

<script>
var carrito = [];
var clienteId = null;

function xhrJson(method, url, bodyObj, cb) {
  var xhr = new XMLHttpRequest();
  xhr.open(method, url, true);
  if (bodyObj !== null) {
    xhr.setRequestHeader("Content-Type", "application/json");
  }
  xhr.onreadystatechange = function() {
    if (xhr.readyState === 4) {
      var parsed = null;
      try { parsed = JSON.parse(xhr.responseText); } catch (e) {}
      cb(xhr.status, parsed);
    }
  };
  xhr.send(bodyObj !== null ? JSON.stringify(bodyObj) : null);
}

function setMsg(texto, color) {
  var el = document.getElementById("msg");
  el.textContent = texto;
  el.style.color = color || "#0f172a";
}

function cargarInicial() {
  xhrJson("GET", "/api/init", null, function(status, data) {
    if (status !== 200 || !data) {
      setMsg("Error cargando datos iniciales.", "#b91c1c");
      return;
    }
    var selUser = document.getElementById("usuario_id");
    selUser.innerHTML = "";
    for (var i = 0; i < data.usuarios.length; i++) {
      var u = data.usuarios[i];
      var opt = document.createElement("option");
      opt.value = u.id_usuario;
      opt.textContent = u.nombre + " (" + u.rol + ")";
      selUser.appendChild(opt);
    }

    var selMet = document.getElementById("metodo_pago");
    selMet.innerHTML = "";
    for (var j = 0; j < data.metodos_pago.length; j++) {
      var m = data.metodos_pago[j];
      var mOpt = document.createElement("option");
      mOpt.value = m.id_metodo;
      mOpt.textContent = m.metodo;
      selMet.appendChild(mOpt);
    }
    toggleCliente();
  });
}

function toggleCliente() {
  var sel = document.getElementById("metodo_pago");
  var texto = sel.options.length > 0 ? sel.options[sel.selectedIndex].text.toLowerCase() : "";
  var esFiado = texto.indexOf("fiado") !== -1 || texto.indexOf("crédito") !== -1 || texto.indexOf("credito") !== -1;
  document.getElementById("bloque_cliente").style.display = esFiado ? "block" : "none";
}

function buscarClientes() {
  var q = encodeURIComponent(document.getElementById("txt_cliente").value.trim());
  var box = document.getElementById("sug_clientes");
  if (!q) {
    box.style.display = "none";
    clienteId = null;
    document.getElementById("cliente_elegido").textContent = "";
    return;
  }
  xhrJson("GET", "/api/clientes?q=" + q, null, function(status, data) {
    box.innerHTML = "";
    if (status !== 200 || !data || !data.clientes || data.clientes.length === 0) {
      box.style.display = "none";
      return;
    }
    for (var i = 0; i < data.clientes.length; i++) {
      var c = data.clientes[i];
      var div = document.createElement("div");
      div.className = "sug-item";
      div.textContent = c.nombre + " (" + (c.telefono || "Sin tel") + ")";
      div.onclick = (function(cli) {
        return function() {
          clienteId = cli.id_cliente;
          document.getElementById("txt_cliente").value = cli.nombre;
          document.getElementById("cliente_elegido").textContent = "Seleccionado: " + cli.nombre;
          box.style.display = "none";
        };
      })(c);
      box.appendChild(div);
    }
    box.style.display = "block";
  });
}

function buscarProductos(autoAgregarExacto) {
  var raw = document.getElementById("txt_buscar").value.trim();
  if (!raw) return;
  xhrJson("GET", "/api/productos?q=" + encodeURIComponent(raw), null, function(status, data) {
    var cont = document.getElementById("resultados_prod");
    cont.innerHTML = "";
    if (status !== 200 || !data || !data.productos || data.productos.length === 0) {
      cont.innerHTML = "<p style='color:#b91c1c; margin-top:8px;'>Producto no encontrado.</p>";
      return;
    }
    if (autoAgregarExacto && data.productos.length === 1 && String(data.productos[0].codigo) === raw) {
      seleccionarProducto(data.productos[0]);
      document.getElementById("txt_buscar").value = "";
      cont.innerHTML = "";
      return;
    }
    for (var i = 0; i < data.productos.length; i++) {
      var p = data.productos[i];
      var btn = document.createElement("button");
      btn.className = "prod-btn";
      btn.textContent = p.nombre + " — $" + Number(p.precio).toFixed(2) + " (Stock: " + Number(p.stock) + " | " + (p.tipo_venta || "por unidad") + ")";
      btn.onclick = (function(prod) {
        return function() {
          seleccionarProducto(prod);
          document.getElementById("txt_buscar").value = "";
          cont.innerHTML = "";
        };
      })(p);
      cont.appendChild(btn);
    }
  });
}

function seleccionarProducto(prod) {
  var stockDisp = parseFloat(prod.stock || 0);
  if (stockDisp <= 0) {
    setMsg("Sin stock disponible para " + prod.nombre, "#c2410c");
    return;
  }
  var esKilo = (prod.tipo_venta === "por kilo");
  var entrada = prompt(
    esKilo ? ("Kilos para: " + prod.nombre + " (ej. 0.750)") : ("Cantidad para: " + prod.nombre),
    esKilo ? "1.0" : "1"
  );
  if (entrada === null) return;
  var cant = parseFloat(String(entrada).replace(",", "."));
  if (isNaN(cant) || cant <= 0) {
    setMsg("Cantidad o peso inválido.", "#b91c1c");
    return;
  }

  for (var i = 0; i < carrito.length; i++) {
    if (String(carrito[i].codigo) === String(prod.codigo)) {
      carrito[i].cantidad = parseFloat(carrito[i].cantidad) + cant;
      renderCarrito();
      return;
    }
  }
  carrito.push({
    codigo: prod.codigo,
    nombre: prod.nombre,
    precio: parseFloat(prod.precio),
    cantidad: cant,
    tipo_venta: prod.tipo_venta || "por unidad"
  });
  setMsg("", "");
  renderCarrito();
}

function quitarItem(idx) {
  carrito.splice(idx, 1);
  renderCarrito();
}

function renderCarrito() {
  var tbody = document.getElementById("carrito_body");
  tbody.innerHTML = "";
  var subTotal = 0;
  for (var i = 0; i < carrito.length; i++) {
    var it = carrito[i];
    var sub = parseFloat(it.precio) * parseFloat(it.cantidad);
    subTotal += sub;
    var cantTxt = (it.tipo_venta === "por kilo")
      ? (Number(it.cantidad).toFixed(3) + " kg")
      : String(it.cantidad);
    tbody.innerHTML += "<tr>" +
      "<td>" + it.codigo + "</td>" +
      "<td>" + it.nombre + "</td>" +
      "<td>" + cantTxt + "</td>" +
      "<td>$" + Number(it.precio).toFixed(2) + "</td>" +
      "<td>$" + sub.toFixed(2) + "</td>" +
      "<td><button class='gray' onclick='quitarItem(" + i + ")'>X</button></td>" +
      "</tr>";
  }
  var impPct = parseFloat(document.getElementById("impuesto").value || 0);
  if (isNaN(impPct)) impPct = 0;
  var impMonto = subTotal * (impPct / 100.0);
  var total = subTotal + impMonto;

  document.getElementById("lbl_sub").textContent = "$" + subTotal.toFixed(2);
  document.getElementById("lbl_imp").textContent = "$" + impMonto.toFixed(2);
  document.getElementById("lbl_tot").textContent = "$" + total.toFixed(2);
}

function procesarVenta() {
  if (carrito.length === 0) {
    setMsg("El carrito está vacío.", "#c2410c");
    return;
  }
  var payload = {
    id_usuario: parseInt(document.getElementById("usuario_id").value, 10),
    metodo_pago_id: parseInt(document.getElementById("metodo_pago").value, 10),
    id_cliente: clienteId,
    impuesto: parseFloat(document.getElementById("impuesto").value || 0),
    items: carrito
  };
  xhrJson("POST", "/api/venta", payload, function(status, data) {
    if (status === 200 && data && data.ok) {
      setMsg("Venta procesada con éxito (Folio #" + data.id_venta + ").", "#15803d");
      carrito = [];
      clienteId = null;
      document.getElementById("txt_cliente").value = "";
      document.getElementById("cliente_elegido").textContent = "";
      renderCarrito();
    } else {
      setMsg((data && data.error) ? data.error : "Error al procesar la venta.", "#b91c1c");
    }
  });
}

cargarInicial();
</script>
</body>
</html>
"""


class POSHandler(BaseHTTPRequestHandler):
    db = Database()

    def _send_html(self, html_str):
        raw = html_str.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_json(self, status_code, obj):
        raw = json.dumps(obj, default=str).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path in ("/", "/ipad"):
            self._send_html(HTML_PAGE)
            return

        if parsed.path == "/api/init":
            usuarios = self.db.obtener_resultados("SELECT id_usuario, nombre, rol FROM usuarios")
            metodos = self.db.obtener_resultados("SELECT id_metodo, metodo FROM metodos_pago")
            self._send_json(200, {"usuarios": usuarios, "metodos_pago": metodos})
            return

        if parsed.path == "/api/productos":
            q = (qs.get("q", [""])[0] or "").strip()
            if not q:
                self._send_json(200, {"productos": []})
                return
            rows = self.db.obtener_resultados(
                "SELECT codigo, nombre, precio, stock, tipo_venta FROM productos "
                "WHERE codigo = %s OR nombre LIKE %s LIMIT 8",
                (q, f"%{q}%"),
            )
            self._send_json(200, {"productos": rows})
            return

        if parsed.path == "/api/clientes":
            q = (qs.get("q", [""])[0] or "").strip()
            if not q:
                self._send_json(200, {"clientes": []})
                return
            rows = self.db.obtener_resultados(
                "SELECT id_cliente, nombre, telefono FROM clientes "
                "WHERE nombre LIKE %s OR telefono LIKE %s LIMIT 6",
                (f"%{q}%", f"%{q}%"),
            )
            self._send_json(200, {"clientes": rows})
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/venta":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        data = json.loads(raw or "{}")

        items = data.get("items") or []
        id_usuario = data.get("id_usuario")
        metodo_id = data.get("metodo_pago_id")
        id_cliente = data.get("id_cliente")
        imp_pct = float(data.get("impuesto") or 0.0)

        if not items:
            self._send_json(400, {"ok": False, "error": "El carrito está vacío."})
            return

        caja_activa = self.db.obtener_resultados(
            "SELECT id_caja FROM caja WHERE id_usuario = %s AND estado = 'ABIERTA' LIMIT 1",
            (id_usuario,),
        )
        if not caja_activa:
            self._send_json(400, {"ok": False, "error": "Debe abrir caja antes de realizar una venta."})
            return

        metodos = self.db.obtener_resultados(
            "SELECT metodo FROM metodos_pago WHERE id_metodo = %s LIMIT 1",
            (metodo_id,),
        )
        metodo_texto = (metodos[0]["metodo"].lower() if metodos else "")
        es_fiado = ("fiado" in metodo_texto) or ("crédito" in metodo_texto) or ("credito" in metodo_texto)

        if es_fiado and not id_cliente:
            self._send_json(400, {"ok": False, "error": "Selecciona un cliente válido para el fiado."})
            return

        subtotal = sum(float(i["precio"]) * float(i["cantidad"]) for i in items)
        total = subtotal + (subtotal * (imp_pct / 100.0))

        id_venta = self.db.ejecutar_query(
            "INSERT INTO ventas (id_usuario, metodo_pago_id, impuesto, total_venta) VALUES (%s, %s, %s, %s)",
            (id_usuario, metodo_id, imp_pct, total),
        )
        if not id_venta:
            self._send_json(500, {"ok": False, "error": "Error al guardar la venta."})
            return

        if es_fiado:
            self.db.ejecutar_query(
                "INSERT INTO creditos (id_cliente, id_venta, total_fiado, abono, estado) "
                "VALUES (%s, %s, %s, 0.00, 'Pendiente')",
                (id_cliente, id_venta, total),
            )

        for it in items:
            cant = float(it["cantidad"])
            precio = float(it["precio"])
            sub_item = precio * cant
            self.db.ejecutar_query(
                "INSERT INTO ventas_detalle (id_venta, codigo_producto, cantidad, precio_unitario, subtotal) "
                "VALUES (%s, %s, %s, %s, %s)",
                (id_venta, it["codigo"], cant, precio, sub_item),
            )
            self.db.ejecutar_query(
                "UPDATE productos SET stock = stock - %s WHERE codigo = %s",
                (cant, it["codigo"]),
            )

        self._send_json(200, {"ok": True, "id_venta": id_venta})

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    server = ThreadingHTTPServer(("0.0.0.0", port), POSHandler)
    print(f"Servidor iPad listo en http://0.0.0.0:{port}")
    server.serve_forever()
