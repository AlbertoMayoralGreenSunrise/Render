import os
import base64
import json
import requests
from openpyxl import Workbook

# --- Variables de entorno ---
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = "usuario/repositorio"  # e.g., "AlbertoMayoral/wattwin-excel"
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

# --- Crear Excel ---
wb = Workbook()
ws = wb.active
ws.title = "Productos"
columns = ["Numero", "Nombre", "Unidades", "Estructura", "Paneles", "Unidades4",
           "Optimizador", "Unidades2", "Inversor", "Unidades3", "Baterías",
           "Cargador VE", "Pajareras", "Fecha de venta", "LEG"]
ws.append(columns)

for p in products:
    ws.append([
        p.get("index"),
        p.get("name"),
        p.get("count"),
        "", "", "", "", "", "", "", "", "", "", "", ""
    ])

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
