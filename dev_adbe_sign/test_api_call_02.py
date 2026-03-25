import requests, json, requests
from dotenv import dotenv_values

# Configuration
config = dotenv_values(".env")
CLIENT_ID = config.get("CLIENT_ID")
CLIENT_SECRET = config.get("CLIENT_SECRET")
REFRESH_TOKEN = config.get("REFRESH_TOKEN")
ACCESS_TOKEN = config.get("ACCESS_TOKEN")
SHARD = "na1"
BASE_URL = f"https://api.{SHARD}.echosign.com"
SECRETS_FOLDER = "./client_secret/"
URI_FILENAME = f"{SECRETS_FOLDER}adbe_sign_uri.json"
TOKEN_FILENAME = f"{SECRETS_FOLDER}adbe_dev_token.txt"
# USERS_ENDPOINT = f"{BASE_URL}/users"

# TEST Get URI endpoint

# API request configuration
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def refresh_token (client_id, client_secret, refresh_token):
    endpoint = f"{BASE_URL}/oauth/v2/refresh"
    current_url = endpoint
    print(f"Consultando: {current_url}")

    payload = {
            'grant_type': 'refresh_token',
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token
        }

    headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

    try:
        api_response = requests.post(endpoint, data=payload, headers=headers)
        api_response.raise_for_status()
        
        tokens = api_response.json()
        new_access_token = tokens.get("access_token")
        print("Token renovado exitosamente.")
        return new_access_token
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error al refrescar: {e.response.status_code} - {e.response.text}")
        return None



# TEST CODE

refreshed_tkn = refresh_token(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)

# write token to file
with open (TOKEN_FILENAME, "w", encoding="utf-8") as file:
    file.write(refreshed_tkn)



def get_uris (headers):
    endpoint = f"https://api.{SHARD}.adobesign.com/api/rest/v6/baseUris"
    current_url = endpoint
    
    print(f"Consultando: {current_url}")
    try:
        api_response = requests.get(url=current_url, headers=headers)
        api_response.raise_for_status()
        print("api_response:", api_response)
        json_data = api_response.json()
        print ("json:\n", json_data)
        with open(URI_FILENAME, "w", encoding="utf-8") as file:
            # indent=4 hace que el archivo sea legible para humanos
            json.dump(json_data, file, ensure_ascii=False, indent=4)
            print(f"File saved in {URI_FILENAME}")
    except requests.exceptions.HTTPError as err:
        print(f"Error: {err}")
        print(f"Server message: {api_response.text}")

# TEST CODE

# get_uris(headers)

####

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
# usuarios = get_all_users(endpoint, headers)

# print(f"Total de usuarios recuperados: {len(usuarios)}")

# nombre_archivo = f"{SECRETS_FOLDER}userlist_01.json"

# TEST CODE
# print (CLIENT_ID)