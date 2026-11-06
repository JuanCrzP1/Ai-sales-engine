"""Almacén de BusinessConfig sobre SQLAlchemy (SQLite en local, PostgreSQL más adelante).

Paquete aparte de `app.infrastructure.config` a propósito: importar aquel paquete carga los lectores de
YAML del motor. Este no debe importar nada del motor ni de los YAML; lo comprueba
`tests/test_business_config_yaml_independence.py`.
"""
