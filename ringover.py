




# -----------------------------
# Funciones auxiliares
# -----------------------------
def get_call(call_id, base_summary):
    res = requests.get(f"{RINGOVER_BASE}/calls/{call_id}", headers={"Authorization": RINGOVER_API_KEY})
    if res.status_code != 200:
        return {
            "from_number": None,
            "to_number": None,
            "summary_completed": f"⚠️ Error al obtener llamada {call_id}. Código HTTP: {res.status_code}"
        }

    json_data = res.json()
    data_list = json_data.get("data") or json_data.get("list", [])
    call_data = data_list[0] if data_list else {}

    from_number = call_data.get("from_number", "Desconocido")
    to_number = call_data.get("to_number", "Desconocido")
    fecha = call_data.get("start_time", "Sin fecha")
    duracion = f"{call_data.get('total_duration', 'Sin duración')} seg"

    summary_completed = f"""
📞 *Resumen de llamada*
────────────────────
🧩 Call ID: {call_id}
📆 Fecha: {fecha}
⏱️ Duración: {duracion}
📤 De: {from_number}
📥 A: {to_number}

📝 Detalles Ringover:
{base_summary}
"""
    return {"from_number": from_number, "to_number": to_number, "summary_completed": summary_completed}

def search_number(num):
    payload = {"query": {"match_phrase_prefix": {"phoneNumber": num}}}
    res = requests.post(f"{WATTWIN_BASE}/Companies/search",
                        headers={"x-api-key": WATTWIN_API_KEY, "Content-Type": "application/json"},
                        json=payload)
    if res.status_code != 200:
        return None
    companies = res.json().get("data", {}).get("companies", [])
    if companies:
        return companies[0].get("id")
    return None

def get_client(phone_number):
    if not phone_number:
        return None
    phone_number = phone_number.replace(" ", "").strip()
    client_id = None

    if phone_number.startswith("+34"):
        client_id = search_number(phone_number[3:])
        if client_id: return client_id
    if phone_number.startswith("34"):
        client_id = search_number(phone_number[2:])
        if client_id: return client_id

    client_id = search_number(phone_number)
    if client_id: return client_id

    if not phone_number.startswith(("+34", "34")):
        client_id = search_number("+34"+phone_number) or search_number("34"+phone_number)
    return client_id

def get_process_instance(client_id):
    payload = {"query": {"term": {"customer.companyId": client_id}}, "limit": 1}
    res = requests.post(f"{WATTWIN_BASE}/ProcessInstances/search",
                        headers={"x-api-key": WATTWIN_API_KEY, "Content-Type": "application/json"},
                        json=payload)
    instances = res.json().get("data", {}).get("processInstances", [])
    if instances:
        return instances[0].get("id")
    return None

def post_note(process_instance_id, text):
    payload = {
        "processInstanceId": process_instance_id,
        "text": text,
        "allVisible": True,
        "domainId": "65953a9279d3700671585995"
    }
    requests.post(f"{WATTWIN_BASE}/Notes",
                  headers={"x-api-key": WATTWIN_API_KEY, "Content-Type": "application/json"},
                  json=payload)
