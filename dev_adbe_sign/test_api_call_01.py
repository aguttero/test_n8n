import requests, json
from dotenv import dotenv_values
import requests

# Configuration
config = dotenv_values(".env")
CLIENT_ID = config.get("CLIENT_ID")
CLIENT_SECRET = config.get("CLIENT_SECRET")
REFRESH_TOKEN = config.get("REFRESH_TOKEN")
ACCESS_TOKEN = config.get("ACCESS_TOKEN")
BASE_URL = "https://api.na1.echosign.com"
USERS_ENDPOINT = f"{BASE_URL}/users"

# API request configuration
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}





# Configuración inicial
# ACCESS_TOKEN = "TU_TOKEN_AQUÍ"
#BASE_URL = "https://api.na1.adobesign.com" # Ajusta según tu región
endpoint = f"{BASE_URL}/users"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def get_all_users(url, headers):
    all_users = []
    current_url = url
    #test_list = []
    
    while current_url:
        print(f"Consultando: {current_url}")
        response = requests.get(current_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # TEST CODE
            print ("json data: ", data)
            print ("---")
            # Añadir usuarios de la página actual a la lista global
            all_users.extend(data.get('userInfoList', []))
            
            # Verificar si hay una siguiente página (nextCursor)
            page_info = data.get('page', {})
            next_cursor = page_info.get('nextCursor')
            #TEST CODE
            #test_list.append(next_cursor)
            #print("next_cursor: ", test_list)
            #print("***")


            if next_cursor:
                # Construir la URL para la siguiente página
                current_url = f"{url}?cursor={next_cursor}"
            else:
                current_url = None # No hay más páginas
        else:
            print(f"Error {response.status_code}: {response.text}")
            break
            
    return all_users

# Ejecución
usuarios = get_all_users(endpoint, headers)

print(f"Total de usuarios recuperados: {len(usuarios)}")

nombre_archivo = "userlist_01.json"

try:
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        # indent=4 hace que el archivo sea legible para humanos
        json.dump(usuarios, f, ensure_ascii=False, indent=4)
    print(f"✅ Lista de usuarios guardada exitosamente en {nombre_archivo}")
except Exception as e:
    print(f"❌ Error al guardar el archivo: {e}")

# TEST CODE
# print (CLIENT_ID)