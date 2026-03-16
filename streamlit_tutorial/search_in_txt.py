
# search dictionary for next line ocurrence:
# Key: field_name being searched
# Value: {key: "reference keyword" , number of lines where the searched text is located, counting from the reference line in the input file.txt}

dict_busqueda = {
    "gerencia_solicitante": {"keyword": "Gerencia Solictante", "line_distance": 1},
    "rut_proveedor": {"keyword": "SI/NO", "line_distance": 1},
    "razon_social_proveedor": {"keyword": "SI/NO", "line_distance": 3},
    "monto_uf": {"keyword": "Criticidad del Servicio", "line_distance": 2},
    "cuenta_contable": {"keyword": "Orden Controlling", "line_distance": 4},
    "centro_costo": {"keyword": "Orden Controlling", "line_distance": 6},
    "orden_controlling": {"keyword": "Orden Controlling", "line_distance": 6},
    "descripcion_servicio": {"keyword": "Descripción del Servicio/Proyecto:", "line_distance": 1},
}

def extraer_multiples_valores(nombre_archivo, lista_busqueda):
    # Creamos un diccionario para guardar los resultados {termino: valor_siguiente}
    resultados = {termino: None for termino in lista_busqueda}
    pendientes = {} # Para rastrear qué valor debemos capturar en la siguiente línea

    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            for linea in archivo:
                linea_limpia = linea.strip()
                
                # 1. Si teníamos un pendiente de la línea anterior, guardamos el valor
                for termino in list(pendientes.keys()):
                    resultados[termino] = linea_limpia
                    del pendientes[termino] # Ya no es pendiente
                
                # 2. Buscamos si la línea actual coincide con alguno de nuestros términos
                for termino in lista_busqueda:
                    if termino in linea_limpia:
                        pendientes[termino] = True
                        
        return resultados
    except FileNotFoundError:
        return "Archivo no encontrado"

def test(lista_busqueda):
    # Creamos un diccionario para guardar los resultados {termino: valor_siguiente}
    resultados = {termino: None for termino in lista_busqueda}
    print ("resultados: ", resultados)

busqueda = ["Gerencia Solicitante", "Monto Total", "Fecha de Emisión"]
test(busqueda)

# Uso del script
busqueda = ["Gerencia Solicitante", "Monto Total", "Fecha de Emisión"]
# datos_extraidos = extraer_multiples_valores("file.txt", busqueda)

# print(datos_extraidos)
# Salida: {'Gerencia Solicitante': 'Finanzas', 'Monto Total': '1500.50', ...}
