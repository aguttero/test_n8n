from docling.document_converter import DocumentConverter

FILE_IN_FOLDER = "./file_in"

#open pdf file normal en python
# with open (f"{FILE_IN_FOLDER}/Brokerage Statement_2025-12-31_552.PDF", "r") as file:
#    source = file.read()

# 1. Indicamos la fuente (puede ser una URL o una ruta local)
# source = "https://arxiv.org"  # Ejemplo de un paper científico en TXT

# source = f"{FILE_IN_FOLDER}/Brokerage Statement_2025-12-31_552.PDF"

# # 2. Inicializamos el convertidor
# converter = DocumentConverter()

# # 3. Realizamos la conversión
# result = converter.convert(source)

# # 4. Exportamos a Markdown (ideal para LLMs)
# markdown_output = result.document.export_to_markdown()

# with open(f"{FILE_IN_FOLDER}/output_01.md","w", encoding="utf-8") as file:
#     file.write(markdown_output)

# print("OK markdown_output 01")



# 2. Inicializamos el convertidor
try:
    source_2 = f"{FILE_IN_FOLDER}/response no audit trail_v01.pdf"
    converter = DocumentConverter()
    result = converter.convert(source_2)
except Exception as e:
    print(f"Error converter: {e}")

else:
    # 4. Exportamos a Markdown (ideal para LLMs)
    markdown_output = result.document.export_to_markdown()
    with open(f"{FILE_IN_FOLDER}/output_02.md","w", encoding="utf-8") as file:
        file.write(markdown_output)
    print("OK markdown_output 02")

finally:
    print("OK codebase exit")