import os
import base64
import json
import requests
from openpyxl import Workbook

# --- Variables de entorno ---
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = "AlbertoMayoralGreenSunrise/Render"  # e.g., "AlbertoMayoral/wattwin-excel"
GITHUB_BRANCH = "main"               # rama donde subirás el Excel
WATTWIN_API_KEY = os.environ["WATTWIN_API_KEY"]
ORDER_ID = "6915ec902c8ed10ae318fb79"

# --- Llamar a Wattwin ---
resp = requests.get(
    "https://public.api.wattwin.com/v1/ECommerceOrderLines",
    headers={"accept": "application/json", "x-api-key": WATTWIN_API_KEY},
    params={"filter": f'{{"where":{{"orderId":"{ORDER_ID}"}}}}'}
)
products = resp.json()

products_lines = resp.json()

# --- Crear Excel ---
wb = Workbook()
ws = wb.active
ws.title = "Productos"
columns = ["Numero", "Nombre", "Unidades", "Estructura", "Paneles", "Unidades4",
           "Optimizador", "Unidades2", "Inversor", "Unidades3", "Baterías",
           "Cargador VE", "Pajareras", "Fecha de venta", "LEG"]
ws.append(columns)

brand_to_column = {
    "Estructura": 3,
    "Panel": 4,
    "Optimizador": 6,
    "Inversor": 8,
    "Batería": 10,
    "Cargador": 11,
    "Pajareras": 12,
}

for line in products_lines:
    product_id = line.get("productId")
    # Llamada individual para obtener info completa del producto
    product_resp = requests.get(
        f"https://public.api.wattwin.com/v1/Products/{product_id}",
        headers={"accept": "application/json", "x-api-key": WATTWIN_API_KEY}
    )
    product = product_resp.json()

    row = [""] * len(columns)
    row[0] = line.get("index")
    row[1] = product.get("name", "")
    row[2] = line.get("count", 0)

    brand = product.get("brand", "").lower()
    for key, col_idx in brand_to_column.items():
        if key.lower() in brand:
            row[col_idx] = product.get("name", "")
    
    ws.append(row)


# Guardar temporalmente
file_path = f"/tmp/presupuesto_{ORDER_ID}.xlsx"
wb.save(file_path)

# --- Subir a GitHub ---
with open(file_path, "rb") as f:
    content = base64.b64encode(f.read()).decode()

# Obtener SHA del archivo si ya existe
github_api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/presupuesto_{ORDER_ID}.xlsx"
headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

get_resp = requests.get(github_api_url, headers=headers, params={"ref": GITHUB_BRANCH})
sha = None
if get_resp.status_code == 200:
    sha = get_resp.json()["sha"]

# Payload para crear o actualizar archivo
data = {
    "message": f"Subir presupuesto {ORDER_ID}",
    "content": content,
    "branch": GITHUB_BRANCH
}
if sha:
    data["sha"] = sha

put_resp = requests.put(github_api_url, headers=headers, data=json.dumps(data))

if put_resp.status_code in [200, 201]:
    print("Excel subido correctamente a GitHub")
else:
    print(put_resp.status_code, put_resp.text)
