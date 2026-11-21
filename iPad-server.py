import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from database import Database

HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Easy Sale - iPad</title>
<style>
  body { font-family: -apple-system, sans-serif; margin: 0; background: #f4f6f9; color: #111; }
  header { background: #0d47a1; color: #fff; padding: 14px 18px; font-size: 18px; font-weight: bold; }
  .wrap { max-width: 900px; margin: 16px auto; padding: 0 14px; }
  .card { background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
  input, button { font-size: 16px; padding: 10px 12px; border-radius: 6px; border: 1px solid #ccc; }
  button { background: #0d47a1; color: #fff; border: none; font-weight: bold; cursor: pointer; }
  button.secondary { background: #455a64; }
  table { width: 100%; border-collapse: collapse; margin-top: 10px; }
  th, td { border-bottom: 1px solid #e0e0e0; padding: 8px; text-align: left; font-size: 15px; }
  .row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
</style>
</head>
<body>
<header>Easy Sale — Acceso iPad</header>
<div class="wrap">
  <div class="card">
    <h3>Buscar / Agregar producto</h3>
    <div class="row">
      <input id="buscar" type="text" placeholder="Código o nombre..." style="flex:1; min-width:180px;">
      <input id="cant" type="number" step="any" value="1" style="width:90px;">
      <button onclick="buscarProducto()">Buscar</button>
    </div>
    <div id="resultados"></div>
  </div>

  <div class="card">
    <h3>Carrito actual</h3>
    <table>
      <thead><tr><th>Producto</th><th>Cant.</th><th>Precio</th><th>Subtotal</th><th></th></tr></thead>
      <tbody id="carrito"></tbody>
    </table>
    <p style="font-size:18px; font-weight:bold;">Total: $<span id="total">0.00</span></p>
    <div class="row">
      <button onclick="cobrar()">Registrar Venta</button>
      <button class="secondary" onclick="limpiarCarrito()">Limpiar</button>
    </div>
    <p id="msg"></p>
  </div>
</div>

<script>
var carrito = [];

function renderCarrito() {
  var tbody = document.getElementById("carrito");
  var total = 0;
  tbody.innerHTML = "";
  for (var i = 0; i < carrito.length; i++) {
    var item = carrito[i];
    var sub = item.precio * item.cantidad;
    total += sub;
    tbody.innerHTML += "<tr>" +
      "<td>" + item.nombre + "</td>" +
      "<td>" + item.cantidad + "</td>" +
      "<td>$" + item.precio.toFixed(2) + "</td>" +
      "<td>$" + sub.toFixed(2) + "</td>" +
      "<td><button class='secondary' onclick='quitar(" + i + ")'>X</button></td>" +
      "</tr>";
  }
  document.getElementById("total").textContent = total.toFixed(2);
}

function quitar(idx) {
  carrito.splice(idx, 1);
  renderCarrito();
}

function limpiarCarrito() {
  carrito = [];
  renderCarrito();
}

function buscarProducto() {
  var q = encodeURIComponent(document.getElementById("buscar").value.trim());
  var xhr = new XMLHttpRequest();
  xhr.open("GET", "/api/productos?q=" + q, true);
  xhr.onreadystatechange = function() {
    if (xhr.readyState === 4 && xhr.status === 200) {
      var data = JSON.parse(xhr.responseText);
      var cont = document.getElementById("resultados");
      cont.innerHTML = "";
      if (!data.productos || data.productos.length === 0) {
        cont.innerHTML = "<p>Sin coincidencias.</p>";
        return;
      }
      for (var i = 0; i < data.productos.length; i++) {
        var p = data.productos[i];
        var btn = document.createElement("button");
        btn.style.margin = "6px 6px 0 0";
        btn.textContent = p.nombre + " ($" + Number(p.precio).toFixed(2) + ")";
        btn.onclick = (function(prod) {
          return function() {
            var c = parseFloat(document.getElementById("cant").value) || 1;
            carrito.push({
              id: prod.id,
              nombre: prod.nombre,
              precio: parseFloat(prod.precio),
              cantidad: c
            });
            renderCarrito();
          };
        })(p);
        cont.appendChild(btn);
      }
    }
  };
  xhr.send();
}

function cobrar() {
  if (carrito.length === 0) return;
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/api/venta", true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.onreadystatechange = function() {
    if (xhr.readyState === 4) {
      var msg = document.getElementById("msg");
      if (xhr.status === 200) {
        msg.textContent = "Venta registrada correctamente.";
        limpiarCarrito();
      } else {
        msg.textContent = "Error al registrar la venta.";
      }
    }
  };
  xhr.send(JSON.stringify({ items: carrito }));
}
</script>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    db = Database()

    def _send_json(self, code, payload):
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            body = HTML_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path == "/api/productos":
            # Ajusta nombres de columnas/tabla según tu clase Database
            self._send_json(200, {"productos": []})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/venta":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            _ = json.loads(raw)
            # Conecta aquí el guardado de venta con tu Database()
            self._send_json(200, {"ok": True})
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    port = int(os.environ.get("IPAD_PORT", 8080))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Servidor iPad corriendo en http://0.0.0.0:{port}")
    server.serve_forever()
