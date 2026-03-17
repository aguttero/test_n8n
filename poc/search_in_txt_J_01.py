#config

#FILE_IN = "file_out/JAD_OUTPUT_V01.txt"
FILE_IN = "file_out/JAD_AT_OUTPUT_V01.txt"

# search dictionary for next line ocurrence:
# Key: field_name being searched
# Value: {key: "reference keyword" , number of lines where the searched text is located, counting from the reference line in the input file.txt}

dict_busqueda = {
    "gerencia_solicitante": {"keyword": "Gerencia Solicitante", "line_distance": 1},
    "rut_proveedor": {"keyword": "Rut Proveedor", "line_distance": 8},
    "razon_social_proveedor": {"keyword": "Razón Social Proveedor", "line_distance": 8},
    "monto_uf": {"keyword": "Criticidad del Servicio", "line_distance": 2},
    "cuenta_contable": {"keyword": "Orden Controlling", "line_distance": 4},
    "centro_costo": {"keyword": "Orden Controlling", "line_distance": 6},
    "orden_controlling": {"keyword": "Orden Controlling", "line_distance": 8},
    "descripcion_servicio": {"keyword": "Descripción del Servicio/Proyecto:", "line_distance": 1},
}

def extraer_datos_complejos(nombre_archivo, dict_busqueda):
    # Inicializamos el resultado con None para cada campo de la DB
    resultados = {campo: None for campo in dict_busqueda}
    
    # Lista de tareas activas: {"campo": "gerencia", "steps_left": 1}
    pendientes = []

    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            for linea in archivo:
                linea_limpia = linea.strip()

                # 1. Procesar pendientes (restar distancia)
                for tarea in pendientes[:]: # Copia [:] para poder borrar mientras iteramos
                    tarea["steps_left"] -= 1
                    
                    if tarea["steps_left"] == 0:
                        resultados[tarea["campo"]] = linea_limpia
                        pendientes.remove(tarea)

                # 2. Buscar nuevas palabras clave
                for campo, config in dict_busqueda.items():
                    if config["keyword"] in linea_limpia:
                        # Añadimos a la lista de espera para capturar en X líneas
                        pendientes.append({
                            "campo": campo, 
                            "steps_left": config["line_distance"]
                        })
                        
        return resultados

    except FileNotFoundError:
        return "Archivo no encontrado"

# TEST Uso del script
mis_datos = extraer_datos_complejos(FILE_IN, dict_busqueda)
print("mis_datos:", mis_datos)

