Crear venv folder
	ptyhon3 -m venv .venv # [2do venv es la subfolder]
	source .venv/bin/activate
	deactivate

    pip freeze > requirements.txt

Install requirements
	ir al folder del proyecto
	activar el .venv
	pip install -r requirements.tx

To Clean uninstall packages:
pip uninstall -r requirements.txt -y

To Clean install packages in a .venv
python3 -m pip install my_package