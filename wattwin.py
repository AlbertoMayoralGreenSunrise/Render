import os
import base64
import json
import requests
from openpyxl import Workbook, load_workbook
from io import BytesIO, StringIO

# --- Capturar "logs" en memoria ---
log_stream = StringIO()

def log(msg):
    """Guardar mensaje en log_stream"""
    log_stream.write(msg + "\n")

# --- Variables de entorno ---
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = "AlbertoMayoralGreenSunrise/Render"
GITHUB_BRANCH = "main"
WATTWIN_API_KEY = os.environ["WATTWIN_API_KEY"]
ORDER_ID = "69134d11b9c1d30b15fabdc3"

# --- Llamar a Wattwin ---
try:
    resp = requests.get(
        "https://public.api.wattwin.com/v1/ECommerceOrderLines",
        headers={"accept": "application/json", "x-api-key": WATTWIN_API_KEY},
        params={"filter": f'{{"where":{{"orderId":"{ORDER_ID}"}}}}'}
    )
    resp.raise_for_status()
    products_lines = resp.json()
    log(f"[LOG] Número de líneas de pedido obtenidas: {len(products_lines)}")
except Exception as e:
    log(f"[ERROR] Error al obtener líneas de pedido: {e}")
    products_lines = []

# --- Obtener Excel existente de GitHub ---
github_api_url_excel = f"https://api.github.com/repos/{GITHUB_REPO}/contents/Material_ventas.xlsx"
headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

try:
    get_resp = requests.get(github_api_url_excel, headers=headers, params={"ref": GITHUB_BRANCH})
    get_resp.raise_for_status()
    file_data = get_resp.json()
    sha_excel = file_data["sha"]
    file_content = base64.b64decode(file_data["content"])
    wb = load_workbook(filename=BytesIO(file_content))
    ws = wb.active
    log("[LOG] Excel existente cargado desde GitHub")
except Exception:
    wb = Workbook()
    ws = wb.active
    ws.title = "Productos"
    columns = ["Numero", "Nombre", "Unidades", "Estructura", "Paneles", "Unidades4",
               "Optimizador", "Unidades2", "Inversor", "Unidades3", "Baterías",
               "Cargador VE", "Pajareras", "Fecha de venta", "LEG"]
    ws.append(columns)
    sha_excel = None
    log("[LOG] Nuevo Excel creado")

# --- Mapeo de categoryId a columna en el Excel ---
category_to_column = {
    "641070821fff5b625088e567": 3,   # Bomba de calor → Estructura
    "6328b2a5efa9419a5938b922": 4,   # Estaciones de recarga → Paneles
    "6328b2a5efa9419a5938b921": 8,   # Inversor → Inversor
    "6328b2a5efa9419a5938b927": 10,  # Baterías → Baterías
}

# --- Crear fila para un pedido ---
pedido_row = [""] * 15
pedido_row[0] = "Pedido 1"
pedido_row[14] = "LEG"

# --- Recorrer productos ---
for idx, line in enumerate(products_lines, start=1):
    product_name = line.get("name", "")
    count = line.get("count", 0)
    product_id = line.get("productId")
    log(f"[LOG] Procesando línea {idx}: {product_name} (ID: {product_id}, Cantidad: {count})")

    category_id = ""
    if product_id:
        try:
            product_resp = requests.get(
                f"https://public.api.wattwin.com/v1/Products/{product_id}",
                headers={"accept": "application/json", "x-api-key": WATTWIN_API_KEY}
            )
            product_resp.raise_for_status()
            product_data = product_resp.json()
            category_id = product_data.get("categoryId", "")
            log(f"[LOG] categoryId obtenido: {category_id}")
        except Exception as e:
            log(f"[ERROR] No se pudo obtener producto {product_id}: {e}")

    if category_id in category_to_column:
        col_idx = category_to_column[category_id]
        if pedido_row[col_idx]:
            pedido_row[col_idx] += f", {product_name}"
            pedido_row[col_idx + 1] += f" + {count}"
        else:
            pedido_row[col_idx] = product_name
            pedido_row[col_idx + 1] = str(count)
        log(f"[LOG] Producto colocado en columna {col_idx}")
    else:
        log(f"[WARN] categoryId {category_id} no mapeado, producto no añadido")

ws.append(pedido_row)
log(f"[LOG] Fila agregada al Excel: {pedido_row}")

# --- Guardar Excel en GitHub ---
output = BytesIO()
wb.save(output)
content_excel = base64.b64encode(output.getvalue()).decode()

data_excel = {
    "message": f"Actualizar presupuesto {ORDER_ID}",
    "content": content_excel,
    "branch": GITHUB_BRANCH
}
if sha_excel:
    data_excel["sha"] = sha_excel

try:
    put_resp = requests.put(github_api_url_excel, headers=headers, data=json.dumps(data_excel))
    put_resp.raise_for_status()
    log("[LOG] Excel actualizado correctamente en GitHub")
except Exception as e:
    log(f"[ERROR] GitHub PUT falló: {e}")

# --- Subir logs como archivo de texto a GitHub ---
log_stream.seek(0)
logs_content = log_stream.read()
log_file_path = f"logs/log_{ORDER_ID}.txt"
github_api_url_logs = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{log_file_path}"

try:
    get_resp_logs = requests.get(github_api_url_logs, headers=headers, params={"ref": GITHUB_BRANCH})
    if get_resp_logs.status_code == 200:
        sha_logs = get_resp_logs.json()["sha"]
    else:
        sha_logs = None

    put_data_logs = {
        "message": f"Guardar logs pedido {ORDER_ID}",
        "content": base64.b64encode(logs_content.encode()).decode(),
        "branch": GITHUB_BRANCH
    }
    if sha_logs:
        put_data_logs["sha"] = sha_logs

    put_resp_logs = requests.put(github_api_url_logs, headers=headers, data=json.dumps(put_data_logs))
    put_resp_logs.raise_for_status()
    log("[LOG] Logs subidos correctamente a GitHub")
except Exception as e:
    log(f"[ERROR] No se pudieron subir los logs: {e}")
