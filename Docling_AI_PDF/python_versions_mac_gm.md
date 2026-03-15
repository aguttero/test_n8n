2. Listar todas las versiones instaladas en el sistema
Dado que Python puede estar en diferentes carpetas, usa estos comandos para buscar los ejecutables:
Rutas comunes del sistema:
    ls -l /usr/local/bin/python* (Para versiones instaladas desde Python.org)
    ls -l /usr/bin/python* (Para la versión que viene con macOS)
Si usas Homebrew:
ls -l /opt/homebrew/bin/python*
O simplemente: brew list --versions python 

3. Identificar la ubicación de una versión específica
Si quieres saber exactamente de dónde viene el comando que estás usando:
which python3 

Resumen de rutas típicas en Mac:
/usr/bin/python3: Es el Python del sistema manejado por Apple.
/usr/local/bin/: Aquí suelen estar las versiones instaladas manualmente desde el sitio oficial.
/opt/homebrew/bin/: Ubicación estándar para instalaciones mediante Homebrew en Macs con chip Apple Silicon (M1/M2/M3