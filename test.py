
import os
import base64
import json
import requests
from openpyxl import Workbook

# --- TEST VARIABLES ---
PROCESS_INSTANCE_ID = "69134d11b9c1d30b15fabdbf"

# --- ENVIRONMENT ---
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = "AlbertoMayoral/wattwin-excel"
GITHUB_BRANCH = "main"
WATTWIN_API_KEY = os.environ["WATTWIN_API_KEY"]

# ---------------------------------------------------------
# 1) Obtener orderId desde el processInstance
# ---------------------------------------------------------
def get_order_id_from_process(process_id: str, api_key: str):
    payload = {
        "query": { "term": { "processInstanceId": process_id }},
        "limit": 1
    }

    resp = requests.post(
        "https://public.api.wattwin.com/v1/ProcessInstances/search",
        headers={"Content-Type": "application/json", "x-api-key": api_key},
        data=json.dumps(payload)
    )

    data = resp.json()

    if not isinstance(data, list) or len(data) == 0:
        raise Exception("ProcessInstance no encontrado")

    process = data[0]
    order_id = process.get("ecommerceOrderId")

    if not order_id:
        raise Exception("ProcessInstance no tiene ecommerceOrderId")

    return order_id

# ---------------------------------------------------------
# 2) Obtener líneas del pedido
# ---------------------------------------------------------
def get_order_lines(order_id: str, api_key: str):
    resp = requests.get(
        "https://public.api.wattwin.com/v1/ECommerceOrderLines",
        headers={"accept": "application/json", "x-api-key": api_key},
        params={"filter": json.dumps({"where": {"orderId": order_id}})}
    )
    if resp.status_code != 200:
        raise Exception("Error ECommerceOrderLines: " + resp.text)

    return resp.json()

# ---------------------------------------------------------
# 3) Crear Excel
# ---------------------------------------------------------
def generate_excel(order_id, products):
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

    file_path = f"/tmp/presupuesto_{order_id}.xlsx"
    wb.save(file_path)
    return file_path

# ---------------------------------------------------------
# 4) Subir archivo a GitHub
# ---------------------------------------------------------
def upload_to_github(order_id, file_path):
    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/presupuesto_{order_id}.xlsx"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

    # Check if exists
    sha = None
    check = requests.get(url, headers=headers)
    if check.status_code == 200:
        sha = check.json()["sha"]

    payload = {"message": f"Subir presupuesto {order_id}", "content": content, "branch": GITHUB_BRANCH}
    if sha:
        payload["sha"] = sha

    put = requests.put(url, headers=headers, data=json.dumps(payload))
    if put.status_code not in [200, 201]:
        raise Exception("Error subiendo a GitHub: " + put.text)

# ---------------------------------------------------------
# MAIN TEST
# ---------------------------------------------------------
order_id = get_order_id_from_process(PROCESS_INSTANCE_ID, WATTWIN_API_KEY)
products = get_order_lines(order_id, WATTWIN_API_KEY)
path = generate_excel(order_id, products)
upload_to_github(order_id, path)

print("✓ Test completado: Excel subido a GitHub")
