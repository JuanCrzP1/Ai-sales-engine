import { describe, expect, it } from "vitest";
import { bucketOf, byBucket, dueShort, dueText, fromLocalInput, localInput, quickDueOptions, type Reminder } from "./reminders";

// Sábado 28 de noviembre de 2026, 3:00 p. m. en la hora de quien mira.
const NOW = new Date(2026, 10, 28, 15, 0, 0);
const at = (days: number, hour: number, minute = 0) => new Date(2026, 10, 28 + days, hour, minute).toISOString();

const reminder = (id: string, dueAt: string): Reminder => ({
  id, conversationId: "c1", customerName: "Laura", customerContact: "573001", title: id, dueAt, assignee: null, createdBy: null, createdAt: null, doneAt: null, doneBy: null,
});

describe("Los recordatorios", () => {
  it("saben si están vencidos, son de hoy o vienen después", () => {
    expect(bucketOf(at(0, 14), NOW)).toBe("overdue");
    expect(bucketOf(at(0, 18), NOW)).toBe("today");
    expect(bucketOf(at(1, 0, 1), NOW)).toBe("upcoming");
  });

  it("dicen cuándo tocan como una persona", () => {
    expect(dueText(at(0, 13), NOW)).toEqual({ text: "Vencido · hace 2 h", tone: "overdue" });
    expect(dueText(at(0, 14, 50), NOW).text).toBe("Vencido · hace 10 min");
    expect(dueText(at(-3, 15), NOW).text).toBe("Vencido · hace 3 días");
    expect(dueText(at(0, 18), NOW)).toEqual({ text: "Hoy 6:00 p. m.", tone: "today" });
    expect(dueText(at(1, 9), NOW)).toEqual({ text: "Mañana 9:00 a. m.", tone: "upcoming" });
    expect(dueText(at(3, 9), NOW).text).toBe("mar, 1 de dic, 9:00 a. m.");
  });

  it("en una tarjeta lo dicen corto", () => {
    expect(dueShort(at(0, 13), NOW)).toEqual({ text: "Vencido", tone: "overdue" });
    expect(dueShort(at(0, 18), NOW).text).toBe("Hoy 6:00 p. m.");
    expect(dueShort(at(1, 9), NOW).text).toBe("Mañana 9:00 a. m.");
    expect(dueShort(at(3, 9), NOW).text).toBe("1 dic");
  });

  it("propone atajos de fecha y traduce el campo de fecha y hora", () => {
    expect(quickDueOptions(NOW).map((option) => option.label)).toEqual(["En 1 hora", "Mañana 9:00 a. m.", "En 3 días", "En una semana"]);
    expect(quickDueOptions(NOW)[1]!.at).toEqual(new Date(2026, 10, 29, 9, 0));
    expect(localInput(new Date(2026, 10, 29, 9, 5))).toBe("2026-11-29T09:05");
    expect(fromLocalInput("2026-11-29T09:05")).toBe(new Date(2026, 10, 29, 9, 5).toISOString());
    expect(fromLocalInput("")).toBeNull();
  });

  it("reparte los pendientes por cuándo tocan, cada grupo por fecha", () => {
    const groups = byBucket([reminder("b", at(2, 9)), reminder("a", at(0, 13)), reminder("c", at(0, 18)), reminder("d", at(1, 9))], NOW);
    expect([groups.overdue, groups.today, groups.upcoming].map((items) => items.map((item) => item.id))).toEqual([["a"], ["c"], ["d", "b"]]);
  });
});
