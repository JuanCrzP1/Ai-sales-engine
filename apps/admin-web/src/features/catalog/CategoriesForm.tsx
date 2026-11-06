import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { TextField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { useConfig, useFieldIssue } from "../../state/useConfig";

/** Categorías del catálogo: se crean al escribirlas en un producto y aquí se renombran o se quitan si no se usan. */
export function CategoriesForm() {
  const { document, actions } = useConfig();
  const issue = useFieldIssue("offer.catalog.categories");
  const catalog = document.offer.catalog;
  if (!catalog || catalog.categories.length === 0) return null;

  return (
    <Card title="Categorías" description="Cómo se agrupan tus productos. Cambiar el nombre no afecta a los productos.">
      {catalog.categories.map((category, index) => {
        const used = catalog.items.filter((item) => item.category === category.id).length;
        return (
          <div className="category-row" key={category.id}>
            <TextField
              label={`Categoría ${index + 1}`}
              value={category.name}
              onChange={(name) => actions.renameCategory(category.id, name)}
              issue={issue}
              hint={used === 1 ? "1 producto" : `${used} productos`}
            />
            {used === 0 && (
              <ConfirmButton confirmLabel="Sí, quitar" onConfirm={() => actions.removeCategory(category.id)}>
                Quitar
              </ConfirmButton>
            )}
          </div>
        );
      })}
    </Card>
  );
}
