import { useBorrarRecurrente, useRecurrentes } from "@/api/queries";
import { usePreferencias } from "@/hooks/usePreferencias";
import { useToast } from "@/hooks/useToast";
import { fmtMon, formatFecha } from "@/lib/formato";
import { AccBody } from "./AccBody";
import { trd } from "./messages";
import css from "./Dashboard.module.css";

export function RecurrentesCard({ abierto, onToggle }: { abierto: boolean; onToggle: () => void }) {
  const { lang } = usePreferencias();
  const toast = useToast();
  const recurrentes = useRecurrentes(abierto);
  const borrar = useBorrarRecurrente();
  const lista = recurrentes.data ?? [];

  async function alBorrar(id: number) {
    if (!confirm(trd("confirm_borrar_recurrente", lang))) return;
    try {
      await borrar.mutateAsync(id);
      toast(trd("recurrente_eliminado", lang));
    } catch {
      toast(trd("error_guardar", lang));
    }
  }

  return (
    <div className={`${css.cotWrap} ${css.cotWrapRecur}`}>
      <div className={css.cotHeader} onClick={onToggle}>
        <span>{trd("recurrentes_activos", lang)}</span>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ fontSize: 11, color: "var(--muted)" }}>{lista.length ? `(${lista.length})` : ""}</span>
          <span className={css.chev}>{abierto ? "▲" : "▼"}</span>
        </div>
      </div>
      <AccBody open={abierto}>
        {!lista.length ? (
          <div className={css.presupEmpty}>{trd("no_recurrentes_activos", lang)}</div>
        ) : (
          lista.map((r, i) => (
            <div
              key={r.id}
              className={`${css.recurItem} ${css.staggerIn}`}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "10px 0",
                borderBottom: "1px solid var(--border)",
                animationDelay: `${Math.min(i, 10) * 50}ms`,
              }}
            >
              <div>
                <div className={css.recurItemTop} style={{ fontSize: 13, fontWeight: 700 }}>
                  {r.tipo === "Ingreso" ? "💚" : "🔴"} {fmtMon(r.monto, r.moneda ?? "ARS")}
                  <span style={{ fontSize: 11, color: "var(--muted)", fontWeight: 500, marginLeft: 4 }}>
                    {trd(r.frecuencia === "semanal" ? "frecuencia_semanal" : "frecuencia_mensual", lang)}
                  </span>
                </div>
                <div className={css.recurItemSub} style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>
                  {r.categoria || trd("sin_categoria", lang)}
                  {r.descripcion ? " · " + r.descripcion : ""} · {trd("proximo", lang)}: {formatFecha(r.proxima_fecha, lang)}
                </div>
              </div>
              <button
                onClick={() => alBorrar(r.id)}
                aria-label="Eliminar recurrente"
                style={{ background: "none", border: "none", color: "var(--muted)", fontSize: 20, cursor: "pointer", padding: "4px 8px", flexShrink: 0 }}
              >
                ×
              </button>
            </div>
          ))
        )}
      </AccBody>
    </div>
  );
}
