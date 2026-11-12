import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { anchorOf, helpLink } from "../../domain/help/help";
import { helpArticlePath } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";

/**
 * El Markdown de los artículos, como elementos de React (nunca HTML crudo): secciones `##` (con ancla) y `###`, párrafos, listas
 * de un nivel, tablas, avisos (`> **Importante:** …`, `> **Consejo:** …`), bloques de código y, en línea, **negrita**, `código` y
 * enlaces: a otro artículo (`slug`), a una pantalla del panel (`panel:ruta`) o afuera (`https://`, en otra pestaña).
 */
export function Markdown({ source }: { source: string }) {
  const pathTo = useWorkspacePath();

  const inline = (text: string, key: string): ReactNode[] => {
    const parts: ReactNode[] = [];
    const pattern = /\*\*([^*]+)\*\*|`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\)/g;
    let last = 0;
    for (let match = pattern.exec(text); match; match = pattern.exec(text)) {
      if (match.index > last) parts.push(text.slice(last, match.index));
      const id = `${key}-${match.index}`;
      if (match[1] !== undefined) parts.push(<strong key={id}>{match[1]}</strong>);
      else if (match[2] !== undefined) parts.push(<code key={id}>{match[2]}</code>);
      else {
        const label = match[3]!;
        const link = helpLink(match[4]!);
        if (link.kind === "external") {
          parts.push(
            <a key={id} href={link.href} target="_blank" rel="noreferrer">
              {label}
            </a>,
          );
        } else if (link.kind === "article") {
          parts.push(
            <Link key={id} to={pathTo(helpArticlePath(link.slug))}>
              {label}
            </Link>,
          );
        } else if (link.kind === "screen") {
          parts.push(
            <Link key={id} to={pathTo(link.path)} className="help-markdown__screen">
              {label}
            </Link>,
          );
        } else parts.push(label);
      }
      last = match.index + match[0].length;
    }
    if (last < text.length) parts.push(text.slice(last));
    return parts;
  };

  const lines = source.split(/\r?\n/);
  const blocks: ReactNode[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i]!;
    const key = `b${i}`;
    if (!line.trim()) {
      i += 1;
      continue;
    }
    const heading = /^(#{2,3}) +(.+)$/.exec(line);
    if (heading) {
      const title = heading[2]!.trim();
      blocks.push(
        heading[1] === "##" ? (
          <h2 key={key} id={anchorOf(title)}>
            {title}
          </h2>
        ) : (
          <h3 key={key}>{title}</h3>
        ),
      );
      i += 1;
      continue;
    }
    if (line.startsWith(">")) {
      const quote: string[] = [];
      while (i < lines.length && lines[i]!.startsWith(">")) quote.push(lines[i++]!.replace(/^>\s?/, ""));
      const text = quote.join(" ");
      const label = /^\*\*([^*:]+):\*\*\s*/.exec(text);
      const tone = label && /importante|cuidado/i.test(label[1]!) ? "warning" : label && /consejo/i.test(label[1]!) ? "tip" : "note";
      blocks.push(
        <aside key={key} className={`help-callout help-callout--${tone}`}>
          {label && <strong className="help-callout__label">{label[1]}</strong>}
          {label && ": "}
          {inline(label ? text.slice(label[0].length) : text, key)}
        </aside>,
      );
      continue;
    }
    if (line.startsWith("|")) {
      const rows: string[][] = [];
      while (i < lines.length && lines[i]!.startsWith("|")) {
        const cells = lines[i++]!.split("|").slice(1, -1).map((cell) => cell.trim());
        if (!cells.every((cell) => /^:?-+:?$/.test(cell))) rows.push(cells);
      }
      const [head, ...body] = rows;
      blocks.push(
        <div key={key} className="help-table">
          <table>
            <thead>
              <tr>
                {head?.map((cell, n) => (
                  <th key={n} scope="col">
                    {inline(cell, `${key}h${n}`)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {body.map((row, r) => (
                <tr key={r}>
                  {row.map((cell, n) => (
                    <td key={n}>{inline(cell, `${key}r${r}c${n}`)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }
    if (/^(\d+\.|-) /.test(line)) {
      const ordered = /^\d+\./.test(line);
      const items: string[] = [];
      while (i < lines.length && /^(\d+\.|-) /.test(lines[i]!)) items.push(lines[i++]!.replace(/^(\d+\.|-) /, ""));
      const children = items.map((item, n) => <li key={n}>{inline(item, `${key}l${n}`)}</li>);
      blocks.push(
        ordered ? (
          <ol key={key} className="help-steps">
            {children}
          </ol>
        ) : (
          <ul key={key}>{children}</ul>
        ),
      );
      continue;
    }
    if (line.startsWith("```")) {
      const code: string[] = [];
      i += 1;
      while (i < lines.length && !lines[i]!.startsWith("```")) code.push(lines[i++]!);
      i += 1;
      blocks.push(
        <pre key={key}>
          <code>{code.join("\n")}</code>
        </pre>,
      );
      continue;
    }
    const paragraph: string[] = [];
    while (i < lines.length && lines[i]!.trim() && !/^(#{2,3} |>|\||\d+\. |- |```)/.test(lines[i]!)) paragraph.push(lines[i++]!);
    blocks.push(<p key={key}>{inline(paragraph.join(" "), key)}</p>);
  }
  return <div className="help-markdown">{blocks}</div>;
}
