# CompuLabAdmin

Núcleo del sistema de laboratorios de cómputo del TEC. Requiere Python 3.12.
```
python -m venv .venv
.venv\Scripts\activate         # en Linux o macOS: source .venv/bin/activate
pip install -e ".[dev]"
pytest                         # corre las pruebas
lint-imports                   # revisa la regla de capas
```
