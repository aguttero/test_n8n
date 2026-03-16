# import streamlit as st
import pymupdf

# Config section
FOLDER_IN = "./file_in"
FOLDER_TEMP = "./file_tmp"
FOLDER_OUT = "./file_out" 

# Test config section
file_name_in = "response no audit trail_v01.pdf"
file_name_out = "JAD_OUTPUT_V01.txt"


# Load JAD and Contract PDF
# Convert JAD and Contract PDF to text

def convert_pdf_2_text (file_name_in:str, file_name_out:str):
    """Converts a PDF file to text with PyMuPdf"""

    doc = pymupdf.open(f"{FOLDER_IN}/{file_name_in}") # open a document
    out = open(f"{FOLDER_OUT}/{file_name_out}", "wb") # create a text output
    for page in doc: # iterate the document pages
        text = page.get_text().encode("utf8") # get plain text (is in UTF-8)
        out.write(text) # write text of page
        out.write(bytes((12,))) # write page delimiter (form feed 0x0C)
    out.close()
    # Call to logger function. Log file names and transaction



# TODO Extract JAD fields
# - Gerencia solicitante -> Next Line
# - RUT -> Buscar por formato, primer hit después de "RUT Proveedor" o Next Line de "SI/NO"
# - Razón Social del proveedor -> primer hit desdpues de <nro RUT> y después de "SI/NO" 
# - Monto en UF
# - Cuenta contable
# - Centro de costo
# - Orden Controlling
# - Descripción del servicio

def search_next_line(file_name:str, search_text:str) -> str:
    """Returns the next line after the searched text in the <file_name> text file"""
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            found = False
            contador = 0
            for line in file:
                print("Contador de linea: ", contador) # test control
                contador += 1
                # Si en la vuelta anterior encontramos el texto, 
                # esta vuelta es la "línea siguiente"
                if found:
                    return line.strip() # .strip() quita espacios y saltos de línea (\n)
                
                # Buscamos la coincidencia (puedes usar in para mayor flexibilidad)
                if search_text in line:
                    found = True
                    
        return "Texto no encontrado o no hay línea siguiente."
    
    except FileNotFoundError:
        return "El file no existe."

# Test Uso del script
resultado = search_next_line(f"{FOLDER_OUT}/{file_name_out}", "Gerencia Solicitante")
print(f"La gerencia es: {resultado}")


# TODO Save To CSV
# TODO Load Contract
# TODO Extract Contracct fields
# TODO Append To CSV
# TODO Log data transactions
# TODO Purge temp data


# TODO Display JAD and Contract Dashboard

# Show the page title and description.
# st.set_page_config(page_title="Dashboard Contratos", page_icon="📓")
# st.title("📓 Dashboard JAD y Contratos")
# st.write(
#     """
#     Esta app extrae data de JADs y contratos gestionados por Adobe Sign en departamento de compras de empresa XXX.
#     click on the widgets below to explore!
#     """
# )

# Load the data from a CSV. We're caching this so it doesn't reload every time the app
# reruns (e.g. if the user interacts with the widgets).
# @st.cache_data
# def load_data():
#     df = pd.read_csv("data/movies_genres_summary.csv")
#     return df

# df = load_data()

# Show a multiselect widget with the genres using `st.multiselect`.
# genres = st.multiselect(
#     "Genres",
#     df.genre.unique(),
#     ["Action", "Adventure", "Biography", "Comedy", "Drama", "Horror"],
# )