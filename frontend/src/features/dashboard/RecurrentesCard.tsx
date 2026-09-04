import { useBorrarRecurrente, useRecurrentes } from "@/api/queries";
import { usePreferencias } from "@/hooks/usePreferencias";
import { useToast } from "@/hooks/useToast";
import { fmtMon, formatFecha } from "@/lib/formato";
import { AccBody } from "./AccBody";
import { trd } from "./messages";
import css from "./Dashboard.module.css";
import { useConfirmar } from "@/components/Confirmacion";

export function RecurrentesCard({ abierto, onToggle }: { abierto: boolean; onToggle: () => void }) {
  const { lang } = usePreferencias();
  const confirmar = useConfirmar();
  const toast = useToast();
  const recurrentes = useRecurrentes(abierto);
  const borrar = useBorrarRecurrente();
  const lista = recurrentes.data ?? [];

  async function alBorrar(id: number) {
    const ok = await confirmar({
      titulo: trd("dlg_borrar_recu_t", lang),
      mensaje: trd("dlg_borrar_recu_m", lang),
      confirmar: trd("dlg_eliminar", lang),
      cancelar: trd("dlg_cancelar", lang),
      peligro: true,
    });
    if (!ok) return;
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
        <div className={css.recurCountRow}>
          <span className={css.recurCount}>{lista.length ? `(${lista.length})` : ""}</span>
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
              style={{ animationDelay: `${Math.min(i, 10) * 50}ms` }}
            >
              <div>
                <div className={css.recurItemTop}>
                  {r.tipo === "Ingreso" ? "💚" : "🔴"} {fmtMon(r.monto, r.moneda ?? "ARS")}
                  <span className={css.recurItemFreq}>
                    {trd(r.frecuencia === "semanal" ? "frecuencia_semanal" : "frecuencia_mensual", lang)}
                  </span>
                </div>
                <div className={css.recurItemSub}>
                  {r.categoria || trd("sin_categoria", lang)}
                  {r.descripcion ? " · " + r.descripcion : ""} · {trd("proximo", lang)}: {formatFecha(r.proxima_fecha, lang)}
                </div>
              </div>
              <button onClick={() => alBorrar(r.id)} aria-label="Eliminar recurrente" className={css.recurItemBorrar}>
                ×
              </button>
            </div>
          ))
        )}
      </AccBody>
    </div>
  );
}
