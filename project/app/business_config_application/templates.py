"""El catálogo de plantillas de negocio que ofrece el panel al crear un negocio («Empezar de cero» no es una plantilla: es no elegir ninguna).

Las plantillas son archivos JSON en `project/config/business-templates/`, uno por tipo de negocio, revisados como contenido del producto.
Se leen y se validan al arrancar la API: una plantilla rota impide arrancar en lugar de crear negocios a medias.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from app.domain.business_config.templates import BusinessTemplate, TemplateNotFoundError, template_from_dict

DEFAULT_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "config" / "business-templates"


class BusinessTemplateCatalog:
    def __init__(self, templates: Iterable[BusinessTemplate]) -> None:
        ordered = sorted(templates, key=lambda template: (template.order, template.title))
        self._templates = {template.id: template for template in ordered}
        if len(self._templates) != len(ordered):
            raise ValueError("hay plantillas con el mismo identificador")

    @classmethod
    def from_directory(cls, directory: Path = DEFAULT_TEMPLATES_DIR) -> BusinessTemplateCatalog:
        """Las plantillas de la carpeta; sin carpeta, ninguna (el panel solo ofrece empezar de cero)."""
        if not directory.is_dir():
            return cls([])
        return cls(template_from_dict(json.loads(path.read_text(encoding="utf-8"))) for path in sorted(directory.glob("*.json")))

    def list(self) -> list[BusinessTemplate]:
        return list(self._templates.values())

    def get(self, template_id: str) -> BusinessTemplate:
        try:
            return self._templates[template_id]
        except KeyError:
            raise TemplateNotFoundError(template_id) from None
