import os
import base64
import json
import requests
from openpyxl import Workbook, load_workbook
from io import BytesIO

# --- Variables de entorno ---
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = "AlbertoMayoralGreenSunrise/Render"
GITHUB_BRANCH = "main"
WATTWIN_API_KEY = os.environ["WATTWIN_API_KEY"]
ORDER_ID = "69134d11b9c1d30b15fabdc3"

# --- Llamar a Wattwin ---
resp = requests.get(
    "https://public.api.wattwin.com/v1/ECommerceOrderLines",
    headers={"accept": "application/json", "x-api-key": WATTWIN_API_KEY},
    params={"filter": f'{{"where":{{"orderId":"{ORDER_ID}"}}}}'}
)
products_lines = resp.json()

# --- Obtener Excel existente de GitHub ---
github_api_url = f"https://api.github.com/repos/AlbertoMayoralGreenSunrise/Render/contents/Material_ventas.xlsx"
headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

get_resp = requests.get(github_api_url, headers=headers, params={"ref": GITHUB_BRANCH})
if get_resp.status_code == 200:
    file_data = get_resp.json()
    sha = file_data["sha"]
    file_content = base64.b64decode(file_data["content"])
    wb = load_workbook(filename=BytesIO(file_content))
    ws = wb.active
else:
    # Si no existe, crear nuevo
    wb = Workbook()
    ws = wb.active
    ws.title = "Productos"
    columns = ["Numero", "Nombre", "Unidades", "Estructura", "Paneles", "Unidades4",
               "Optimizador", "Unidades2", "Inversor", "Unidades3", "Baterías",
               "Cargador VE", "Pajareras", "Fecha de venta", "LEG"]
    ws.append(columns)
    sha = None

from openpyxl import Workbook, load_workbook
from collections import defaultdict

# Suponiendo que products_lines ya es la lista de productos de un pedido
# Ejemplo de estructura de brand_to_column:
brand_to_column = {
    "Estructura": 3,
    "Panel": 4,
    "Optimizador": 6,
    "Inversor": 8,
    "Batería": 10,
    "Cargador": 11,
    "Pajareras": 12,
}

# Diccionario para agrupar por pedido
pedido_row = [""] * 15  # 15 columnas como en tu Excel

pedido_row[0] = "Pedido 1"  # Numero
pedido_row[1] = ""           # Nombre general si quieres
pedido_row[14] = "LEG"       # Fecha de venta o LEG

for line in products_lines:
    product_name = line.get("name")  # o llamando al endpoint de producto
    count = line.get("count", 0)
    brand = line.get("brand", "").lower()

    # Buscar columna según brand
    for key, col_idx in brand_to_column.items():
        if key.lower() in brand:
            if pedido_row[col_idx]:  # si ya hay algo, sumar
                pedido_row[col_idx] += f", {product_name} x{count}"
            else:
                pedido_row[col_idx] = f"{product_name} x{count}"

# Finalmente agregar la fila
ws.append(pedido_row)


# --- Guardar Excel temporalmente ---
from tempfile import NamedTemporaryFile
tmp_file = NamedTemporaryFile(delete=False, suffix=".xlsx")
wb.save(tmp_file.name)

# --- Subir actualizado a GitHub ---
with open(tmp_file.name, "rb") as f:
    content = base64.b64encode(f.read()).decode()

data = {
    "message": f"Actualizar presupuesto {ORDER_ID}",
    "content": content,
    "branch": GITHUB_BRANCH
}
if sha:
    data["sha"] = sha  # importante para reemplazar el archivo existente

put_resp = requests.put(github_api_url, headers=headers, data=json.dumps(data))
if put_resp.status_code in [200, 201]:
    print("Excel actualizado correctamente en GitHub")
else:
    print(put_resp.status_code, put_resp.text)
