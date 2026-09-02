import type { Lang } from "@/i18n/messages";
import type { Moneda } from "@/api/types";

const SIMBOLO: Record<Moneda, string> = { ARS: "$", USD: "USD ", EUR: "€" };

/** Monto con símbolo y dos decimales, siempre en valor absoluto: el signo lo
 *  pone quien llama según sea gasto o ingreso. */
export function fmtMon(n: number, moneda: Moneda | null = "ARS"): string {
  return (
    SIMBOLO[moneda ?? "ARS"] +
    Math.abs(n).toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  );
}

/** "15 ago 2026". La fecha llega como YYYY-MM-DD; el sufijo evita que se lea
 *  como UTC y termine mostrando el día anterior. */
export function formatFecha(iso: string, lang: Lang): string {
  return new Date(iso + "T00:00:00").toLocaleDateString(lang === "en" ? "en-US" : "es-AR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}
