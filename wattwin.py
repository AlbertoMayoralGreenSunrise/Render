# wattwin.py
import os
import base64
import json
import requests
from openpyxl import Workbook
from io import BytesIO, StringIO

def process_wattwin_order(order_id: str):
    log_stream = StringIO()

    def log(msg):
        log_stream.write(msg + "\n")

    WATTWIN_API_KEY = os.environ["WATTWIN_API_KEY"]
    GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
    GITHUB_REPO = "AlbertoMayoralGreenSunrise/Render"
    GITHUB_BRANCH = "main"

    # --- Llamar a Wattwin ---
    try:
        resp = requests.get(
            "https://public.api.wattwin.com/v1/ECommerceOrderLines",
            headers={"accept": "application/json", "x-api-key": WATTWIN_API_KEY},
            params={"filter": f'{{"where":{{"orderId":"{order_id}"}}}}'}
        )
        resp.raise_for_status()
        products_lines = resp.json()
        log(f"[LOG] Número de líneas de pedido obtenidas: {len(products_lines)}")
    except Exception as e:
        log(f"[ERROR] Error al obtener líneas de pedido: {e}")
        products_lines = []

    # --- Crear Excel nuevo ---
    columns = [
        "Numero", "Nombre",
        "Estructura", "Unidades Estructura",
        "Paneles", "Unidades Paneles",
        "Optimizador", "Unidades Optimizador",
        "Inversor", "Unidades Inversor",
        "Baterías", "Unidades Baterías",
        "Cargador VE", "Unidades Cargador VE",
        "Pajareras", "Unidades Pajareras",
        "Fecha de venta", "LEG"
    ]

    wb = Workbook()
    ws = wb.active
    ws.title = "Productos"
    ws.append(columns)

    # --- Mapeo categoryId → columna ---
    category_to_column = {
        "6328b2a5efa9419a5938b92d": 2,  # Estructura
        "6328b2a5efa9419a5938b91c": 4,  # Paneles
        "6790e34a0a5301a6d0b6e7f8": 6,  # Optimizador
        "6328b2a5efa9419a5938b921": 8,  # Inversor
        "6328b2a5efa9419a5938b927": 10,  # Batería
        "678e12f76d2390929fd91374": 12  # Cargador VE
    }


    # --- Crear fila del pedido ---
    pedido_row = [""] * len(columns)
    pedido_row[0] = "Pedido TEST"
    pedido_row[-1] = "LEG"

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
            log(f"[LOG] Producto colocado en columna {col_idx} ({columns[col_idx]})")
        else:
            log(f"[WARN] categoryId {category_id} no mapeado, producto no añadido")

    # Insertar en fila 4
    for col_idx, value in enumerate(pedido_row, start=1):
        ws.cell(row=4, column=col_idx, value=value)
    log(f"[LOG] Fila agregada al Excel en fila 4: {pedido_row}")

    # --- Guardar Excel en GitHub (con sobreescritura) ---
    output = BytesIO()
    wb.save(output)
    content_excel = base64.b64encode(output.getvalue()).decode()
    github_api_url_excel = f"https://api.github.com/repos/{GITHUB_REPO}/contents/Material_ventas_{order_id}.xlsx"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    
    # Obtener sha si el archivo existe
    sha = None
    get_resp = requests.get(github_api_url_excel, headers=headers)
    if get_resp.status_code == 200:
        sha = get_resp.json()["sha"]
    
    data_excel = {
        "message": f"Crear/Actualizar Excel para pedido {order_id}",
        "content": content_excel,
        "branch": GITHUB_BRANCH,
    }
    if sha:
        data_excel["sha"] = sha  # necesario para sobreescribir
    
    try:
        put_resp = requests.put(github_api_url_excel, headers=headers, data=json.dumps(data_excel))
        put_resp.raise_for_status()
        log("[LOG] Excel subido correctamente a GitHub (creado o sobreescrito)")
    except Exception as e:
        log(f"[ERROR] GitHub PUT falló: {e}")


    # --- SUBIR LOGS A GITHUB (con sobreescritura) ---
    logs_content = log_stream.getvalue()
    log_file_path = f"logs/log_{order_id}.txt"
    github_api_url_logs = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{log_file_path}"
    
    # Obtener sha si existe
    sha_logs = None
    get_resp_logs = requests.get(github_api_url_logs, headers=headers)
    if get_resp_logs.status_code == 200:
        sha_logs = get_resp_logs.json()["sha"]
    
    put_data_logs = {
        "message": f"Guardar logs pedido {order_id}",
        "content": base64.b64encode(logs_content.encode()).decode(),
        "branch": GITHUB_BRANCH,
    }
    if sha_logs:
        put_data_logs["sha"] = sha_logs  # necesario para sobreescribir
    
    try:
        put_resp_logs = requests.put(github_api_url_logs, headers=headers, data=json.dumps(put_data_logs))
        put_resp_logs.raise_for_status()
        log("[LOG] Logs subidos correctamente a GitHub (creados o sobreescritos)")
    except Exception as e:
        log(f"[ERROR] No se pudieron subir los logs: {e}")


    # Retornar logs para debug
    log_stream.seek(0)
    return log_stream.read()

    
