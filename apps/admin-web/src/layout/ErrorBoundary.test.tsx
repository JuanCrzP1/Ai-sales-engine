import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ErrorBoundary } from "./ErrorBoundary";

function Boom({ explode }: { explode: { current: boolean } }) {
  if (explode.current) throw new Error("fallo de prueba");
  return <p>Contenido visible</p>;
}

describe("ErrorBoundary", () => {
  beforeEach(() => {
    // React y el propio límite registran el error en consola; aquí se espera que ocurra.
    vi.spyOn(console, "error").mockImplementation(() => undefined);
  });
  afterEach(() => vi.restoreAllMocks());

  it("muestra una pantalla de error en vez de dejarla en blanco", () => {
    render(
      <ErrorBoundary>
        <Boom explode={{ current: true }} />
      </ErrorBoundary>,
    );
    expect(screen.getByRole("heading", { name: "Algo salió mal" })).toBeInTheDocument();
    expect(screen.getByText(/Tus datos guardados no se han perdido/)).toBeInTheDocument();
  });

  it("en una sección permite reintentar sin recargar la aplicación", async () => {
    const explode = { current: true };
    render(
      <ErrorBoundary variant="section">
        <Boom explode={explode} />
      </ErrorBoundary>,
    );
    expect(screen.getByRole("heading", { name: "Esta sección no se pudo mostrar" })).toBeInTheDocument();
    explode.current = false;
    await userEvent.setup().click(screen.getByRole("button", { name: "Reintentar" }));
    expect(screen.getByText("Contenido visible")).toBeInTheDocument();
  });

  it("se recupera al cambiar de ruta", () => {
    const explode = { current: true };
    const { rerender } = render(
      <ErrorBoundary variant="section" resetKey="/a">
        <Boom explode={explode} />
      </ErrorBoundary>,
    );
    explode.current = false;
    rerender(
      <ErrorBoundary variant="section" resetKey="/b">
        <Boom explode={explode} />
      </ErrorBoundary>,
    );
    expect(screen.getByText("Contenido visible")).toBeInTheDocument();
  });
});
