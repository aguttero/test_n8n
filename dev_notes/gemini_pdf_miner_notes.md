2026 03

Extracción de Texto General
PyMuPDF (fitz): Es una de las más rápidas y completas. Permite extraer texto, imágenes y metadatos con alta precisión, manteniendo bien el diseño original.

PyPDF2: Muy popular para tareas básicas y ligeras como leer texto, dividir o combinar páginas. No es la mejor para diseños complejos o tablas.

pdfminer.six: Se enfoca en la estructura del documento y la ubicación exacta de los caracteres, ideal si necesitas saber dónde está cada palabra en la página. 

2. Extracción de Tablas (Datos Estructurados)
Extraer tablas es un reto común porque los PDFs no suelen tener etiquetas de "tabla". Estas librerías lo facilitan: 

Tabula-py: Un "wrapper" de la herramienta Java Tabula. Es excelente para detectar y extraer tablas automáticamente, convirtiéndolas directamente en DataFrames de Pandas.

Camelot: Ofrece gran control sobre la detección de tablas (usando bordes de línea o espacios en blanco) y permite exportar a múltiples formatos.

pdfplumber: Construida sobre pdfminer.six, es muy potente para extraer tanto texto como tablas complejas, ofreciendo una inspección visual de lo que está extrayendo. 

3. Soluciones Avanzadas e IA
Docling: Desarrollada por IBM, utiliza inteligencia artificial para convertir documentos complejos (PDF, DOCX) a formatos modernos como JSON o Markdown.

PDFQuery: Utiliza selectores similares a CSS (como en el desarrollo web) para extraer datos basados en su posición específica en el documento.

OCR (Tesseract): Si el PDF es una imagen (escaneado), necesitarás herramientas de reconocimiento óptico de caracteres combinadas con librerías como pdf2image