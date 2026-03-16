El error se debe a que estás usando Python 3.13, una versión muy reciente en la que se eliminó por completo el módulo pkg_resources (parte de las antiguas setuptools). Muchas librerías de IA, como las dependencias de Docling, aún no se han actualizado para esta versión.
Para solucionarlo, tienes tres opciones rápidas:

1. La solución directa (Instalar setuptools)
En Python 3.13, pkg_resources ya no viene por defecto. Intenta instalarlo manualmente en tu entorno virtual antes de instalar docling:

    pip install setuptools
    pip install docling

2. Usar Python 3.12 (Recomendado)
Actualmente, la mayoría de las librerías de procesamiento de datos y tensores (como PyTorch, que Docling usa por debajo) son mucho más estables en Python 3.10, 3.11 o 3.12.
Si tienes instalada otra versión en tu Mac, te sugiero recrear el entorno virtual con ella:
    # Ejemplo si tienes python 3.12 instalado
    python3.12 -m venv .venv
    source .venv/bin/activate
    pip install docling

3. Actualizar herramientas de construcción
A veces, simplemente actualizar pip y wheel dentro del entorno virtual ayuda a que el proceso de "build" maneje mejor las dependencias:
    pip install --upgrade pip setuptools wheel
    pip install docling

Nota para Mac (Apple Silicon): Si estás en una MacBook con chip M1/M2/M3, asegúrate de tener instaladas las herramientas de línea de comandos de Xcode (xcode-select --install), ya que Docling necesita compilar algunas dependencias de C++.