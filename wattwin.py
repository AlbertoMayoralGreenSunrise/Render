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
print(f"[LOG] Número de líneas de pedido obtenidas: {len(products_lines)}")

# --- Obtener Excel existente de GitHub ---
github_api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/Material_ventas.xlsx"
headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

get_resp = requests.get(github_api_url, headers=headers, params={"ref": GITHUB_BRANCH})
if get_resp.status_code == 200:
    file_data = get_resp.json()
    sha = file_data["sha"]
    file_content = base64.b64decode(file_data["content"])
    wb = load_workbook(filename=BytesIO(file_content))
    ws = wb.active
    print("[LOG] Excel existente cargado desde GitHub")
else:
    wb = Workbook()
    ws = wb.active
    ws.title = "Productos"
    columns = ["Numero", "Nombre", "Unidades", "Estructura", "Paneles", "Unidades4",
               "Optimizador", "Unidades2", "Inversor", "Unidades3", "Baterías",
               "Cargador VE", "Pajareras", "Fecha de venta", "LEG"]
    ws.append(columns)
    sha = None
    print("[LOG] Nuevo Excel creado")

# --- Mapeo de categoryId a columna en el Excel ---
category_to_column = {
    "641070821fff5b625088e567": 3,   # Bomba de calor → Estructura
    "6328b2a5efa9419a5938b922": 4,   # Estaciones de recarga → Paneles
    "6328b2a5efa9419a5938b921": 8,   # Inversor → Inversor
    "6328b2a5efa9419a5938b927": 10,  # Baterías → Baterías
}

# --- Crear fila para un pedido ---
pedido_row = [""] * 15
pedido_row[0] = "Pedido 1"  # Numero
pedido_row[14] = "LEG"       # Fecha o LEG

# --- Recorrer productos y colocarlos según categoryId ---
for idx, line in enumerate(products_lines, start=1):
    product_name = line.get("name", "")
    count = line.get("count", 0)
    product_id = line.get("productId")
    print(f"[LOG] Procesando línea {idx}: {product_name} (ID: {product_id}, Cantidad: {count})")

    category_id = ""
    if product_id:
        product_resp = requests.get(
            f"https://public.api.wattwin.com/v1/Products/{product_id}",
            headers={"accept": "application/json", "x-api-key": WATTWIN_API_KEY}
        )
        if product_resp.status_code == 200:
            product_data = product_resp.json()
            category_id = product_data.get("categoryId", "")
            print(f"[LOG] categoryId obtenido: {category_id}")
        else:
            print(f"[ERROR] No se pudo obtener producto {product_id} (status {product_resp.status_code})")

    # Colocar el producto en la columna correspondiente según categoryId
    if category_id in category_to_column:
        col_idx = category_to_column[category_id]

        if pedido_row[col_idx]:
            pedido_row[col_idx] += f", {product_name}"
            pedido_row[col_idx + 1] += f" + {count}"
        else:
            pedido_row[col_idx] = product_name
            pedido_row[col_idx + 1] = str(count)
        print(f"[LOG] Producto colocado en columna {col_idx}")
    else:
        print(f"[WARN] categoryId {category_id} no mapeado, producto no añadido")

# --- Agregar fila al Excel ---
ws.append(pedido_row)
print("[LOG] Fila agregada al Excel:", pedido_row)

# --- Guardar Excel en memoria y subir a GitHub ---
output = BytesIO()
wb.save(output)
content = base64.b64encode(output.getvalue()).decode()

data = {
    "message": f"Actualizar presupuesto {ORDER_ID}",
    "content": content,
    "branch": GITHUB_BRANCH
}
if sha:
    data["sha"] = sha  # reemplazar archivo existente

put_resp = requests.put(github_api_url, headers=headers, data=json.dumps(data))
if put_resp.status_code in [200, 201]:
    print("Excel actualizado correctamente en GitHub")
else:
    print("[ERROR] GitHub PUT falló:", put_resp.status_code, put_resp.text)
