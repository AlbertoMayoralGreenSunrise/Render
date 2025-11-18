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
from io import BytesIO
import base64
import requests

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
    wb = Workbook()
    ws = wb.active
    ws.title = "Productos"
    columns = ["Numero", "Nombre", "Unidades", "Estructura", "Paneles", "Unidades4",
               "Optimizador", "Unidades2", "Inversor", "Unidades3", "Baterías",
               "Cargador VE", "Pajareras", "Fecha de venta", "LEG"]
    ws.append(columns)
    sha = None

# --- Mapeo de brand a columna en el Excel ---
brand_to_column = {
    "estructura": 3,  # Nombre en columna 3, cantidad en columna 4
    "panel": 4,
    "optimizador": 6,
    "inversor": 8,
    "batería": 10,
    "cargador": 11,
    "pajareras": 12,
}

# --- Crear fila para un pedido ---
pedido_row = [""] * 15
pedido_row[0] = "Pedido 1"  # Numero
pedido_row[14] = "LEG"       # Fecha o LEG

# --- Recorrer productos y obtener brand desde Wattwin ---
for line in products_lines:
    product_name = line.get("name", "")
    count = line.get("count", 0)
    product_id = line.get("productId")

    # Llamada a Wattwin para obtener el producto y su brand
    if product_id:
        product_resp = requests.get(
            f"https://public.api.wattwin.com/v1/Products/{product_id}",
            headers={"accept": "application/json", "x-api-key": WATTWIN_API_KEY}
        )
        if product_resp.status_code == 200:
            product_data = product_resp.json()
            brand = product_data.get("brand", "").lower()
        else:
            brand = ""
    else:
        brand = ""

    # Colocar el producto en la columna correspondiente
    for key, col_idx in brand_to_column.items():
        if key in brand:
            pedido_row[col_idx] = product_name
            pedido_row[col_idx + 1] = count
            break

# --- Agregar fila al Excel ---
ws.append(pedido_row)


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
