import type { Moneda, Transaccion } from "@/api/types";
import { usePreferencias } from "@/hooks/usePreferencias";
import { fmtMon, formatFecha } from "@/lib/formato";
import type { Filtros } from "./logic";

export function DiaResultado({ filtrados, filtros }: { filtrados: Transaccion[]; filtros: Filtros }) {
  const { lang } = usePreferencias();
  if (!filtros.dia) return null;

  const porMoneda = new Map<Moneda, number>();
  for (const t of filtrados) {
    if (t.tipo !== "Gasto") continue;
    const m = (t.moneda ?? "ARS") as Moneda;
    porMoneda.set(m, (porMoneda.get(m) ?? 0) + Number(t.monto));
  }
  const partes = [...porMoneda.entries()].map(([m, v]) => fmtMon(v, m));

  const esUnDia = filtros.dia.desde === filtros.dia.hasta;
  const fDesde = formatFecha(filtros.dia.desde, lang);
  const fHasta = formatFecha(filtros.dia.hasta, lang);
  const fechaTxt = esUnDia
    ? lang === "en"
      ? `on ${fDesde}`
      : `el ${fDesde}`
    : lang === "en"
      ? `between ${fDesde} and ${fHasta}`
      : `entre el ${fDesde} y el ${fHasta}`;

  const texto = partes.length
    ? lang === "en"
      ? `🗓️ You spent ${fechaTxt}: ${partes.join(" + ")}`
      : `🗓️ Gastaste ${fechaTxt}: ${partes.join(" + ")}`
    : lang === "en"
      ? `🗓️ No expenses recorded ${fechaTxt}`
      : `🗓️ No hay gastos registrados ${fechaTxt}`;

  return <div style={{ padding: "0 12px 8px", color: "var(--muted)" }}>{texto}</div>;
}
