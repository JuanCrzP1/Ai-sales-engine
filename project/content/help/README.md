# Centro de ayuda: cómo escribir un artículo

Una sola fuente para tres lectores:

- **Las personas:** el Centro de ayuda del panel (menú → **Ayuda**) y la ayuda de cada pantalla (el botón **?** junto a la campana).
- **Los agentes de IA:** el servidor MCP los entrega con `search_help` y `read_help_article`.
- **Más adelante:** la ayuda pública, cuando haya dominio propio.

Viven aquí, dentro de `project/`, porque en Vercel solo se publica `project/`. Se leen al arrancar la API (`HelpService.from_directory`).

## El archivo

Cada artículo es `<tema>/<slug>.md`. El slug es el nombre del archivo: en minúsculas, sin tildes y con guiones. Empieza así:

```
---
title: Conecta tu WhatsApp con el código QR
module: canales
summary: Una frase que dice qué resuelve (máximo 200 caracteres).
order: 1
updated: 2026-11-12
keywords: qr, vincular, número
related: cuidar-tu-numero, desconectar-whatsapp
---
```

- `module`: la carpeta donde está. Los temas, en el orden del menú, están en `HELP_MODULES` (`project/app/domain/business_config/help.py`).
- `order`: su lugar dentro del tema. `related`: otros artículos (deben existir).
- Si el título lleva «:», ponlo entre comillas.

## El texto

- `##` divide el artículo en secciones (salen en «En este artículo»); `###`, subsecciones. Nunca `#`: el título va arriba.
- Listas de **un solo nivel** (`-` o `1.`). Pasos con listas numeradas.
- `> **Importante:** …` y `> **Consejo:** …` se ven como avisos.
- Tablas con `|`, **negrita** y `código`.
- Enlaces: a otro artículo `[texto](slug)`, a una pantalla del panel `[Canales](panel:canales)` (la ruta dentro del negocio) y afuera
  solo `https://`.
- Los botones y las pantallas se nombran **exactamente** como se ven en el panel. Nada de datos inventados.

## Al cambiar una pantalla

Cambia su artículo en el mismo trabajo. Las pruebas revisan que cada artículo esté bien escrito, que los enlaces entre artículos
existan (`tests/test_help_center.py`) y que cada `panel:ruta` y cada artículo que nombra el panel existan
(`apps/admin-web/src/app/Help.test.tsx`). La ayuda de cada pantalla (qué artículo sale primero) está en
`apps/admin-web/src/domain/help/help.ts`.
