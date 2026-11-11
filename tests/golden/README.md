# Referencias congeladas del motor

Cada `<negocio>.json` es lo que el motor recibía de los YAML de ese negocio de ejemplo (`business`, `sales`, `pricing`,
`inventory` y `config`) el día que los YAML se retiraron (11 de noviembre de 2026). Los ejemplos ahora viven en
`project/config/tenants/<negocio>/business-config.json`, y las pruebas comprueban que lo publicado compila exactamente a esta
referencia: así el retiro de los YAML no cambió nada de lo que recibe el motor.

Las claves están en el orden de los YAML: el contenido se compara sin importar el orden, pero el del cierre
(`sales.closing`) sí importa, porque el motor lo lleva tal cual en sus metadatos.

Si se cambia a propósito un negocio de ejemplo, se regenera su referencia con `python tests/golden/regenerate.py <negocio>`.
