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
ORDER_ID = "6915ec902c8ed10ae318fb79"

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

# --- Añadir nuevas líneas ---
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
    product_resp = requests.get(
        f"https://public.api.wattwin.com/v1/Products/{product_id}",
        headers={"accept": "application/json", "x-api-key": WATTWIN_API_KEY}
    )
    product = product_resp.json()

    row = [""] * ws.max_column
    row[0] = line.get("index")
    row[1] = product.get("name", "")
    row[2] = line.get("count", 0)

    brand = product.get("brand", "").lower()
    for key, col_idx in brand_to_column.items():
        if key.lower() in brand:
            row[col_idx] = product.get("name", "")

    ws.append(row)

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
