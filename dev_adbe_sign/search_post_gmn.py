import requests
from datetime import datetime, timedelta

# 1. Configuración
TOKEN = "TU_ACCESS_TOKEN"
BASE_URL = "https://api.adobesign.com" # Ajusta si tu región es eu1, na2, etc.

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# 2. Calcular fechas (Última semana)
hoy = datetime.utcnow()
hace_una_semana = hoy - timedelta(days=7)

# Formato ISO 8601 requerido por Adobe
params_busqueda = {
    "startDate": hace_una_semana.strftime('%Y-%m-%dT%H:%M:%SZ'),
    "endDate": hoy.strftime('%Y-%m-%dT%H:%M:%SZ')
}

def obtener_acuerdos_firmados():
    # PASO A: Crear el recurso de búsqueda
    search_res = requests.post(f"{BASE_URL}/search", headers=headers, json=params_busqueda)
    
    if search_res.status_code != 202:
        print(f"Error al iniciar búsqueda: {search_res.text}")
        return

    search_id = search_res.json().get("searchId")
    print(f"Búsqueda iniciada. ID: {search_id}")

    # PASO B: Recuperar los acuerdos de esa búsqueda
    # Filtramos por status=SIGNED para traer solo los completados
    agreements_url = f"{BASE_URL}/search/{search_id}/agreements?status=SIGNED"
    
    response = requests.get(agreements_url, headers=headers)
    
    if response.status_code == 200:
        acuerdos = response.json().get("userAgreementList", [])
        print(f"Se encontraron {len(acuerdos)} acuerdos firmados la última semana:")
        for a in acuerdos:
            print(f"- {a['name']} (ID: {a['id']})")
    else:
        print(f"Error al obtener resultados: {response.text}")

if __name__ == "__main__":
    obtener_acuerdos_firmados()
