"""Capa de aplicación de BusinessConfig: los casos de uso y lo que necesitan de la persistencia.

Paquete propio y no dentro de `app.application` a propósito: importar aquel paquete carga el motor comercial, y esta capa no
debe depender de él. Lo comprueban `tests/test_business_config_architecture.py` y `tests/test_business_config_yaml_independence.py`.
"""
