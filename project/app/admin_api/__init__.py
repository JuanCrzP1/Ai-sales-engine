"""API local del panel de administración: conecta `apps/admin-web` con BusinessConfig v1.

Es independiente de la aplicación del motor (`app.main`): no carga el pipeline, no lee `.env` ni los YAML, salvo la
importación puntual de negocios, que los lee una vez. Sin autenticación: se limita a `127.0.0.1` hasta que la fase de
nube incorpore la autenticación definitiva (ver `docs/operations.md`).
"""
