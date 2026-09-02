import { useEffect, useState } from "react";

import { useBorrarPresupuesto, useGuardarPresupuesto } from "@/api/queries";
import type { Moneda, Presupuesto } from "@/api/types";
import { Modal } from "@/components/Modal";
import { usePreferencias } from "@/hooks/usePreferencias";
import { useToast } from "@/hooks/useToast";
import { fmtMon } from "@/lib/formato";
import { trd } from "./messages";
import css from "./Dashboard.module.css";

const MONEDAS: Moneda[] = ["ARS", "USD", "EUR"];

type Props = {
  abierto: boolean;
  presupuestos: Presupuesto[];
  categorias: string[];
  onCerrar: () => void;
};

export function PresupuestoModal({ abierto, presupuestos, categorias, onCerrar }: Props) {
  const { lang } = usePreferencias();
  const toast = useToast();
  const guardar = useGuardarPresupuesto();
  const borrar = useBorrarPresupuesto();

  const [cat, setCat] = useState("");
  const [monto, setMonto] = useState("");
  const [moneda, setMoneda] = useState<Moneda>("ARS");

  useEffect(() => {
    if (abierto) {
      setCat("");
      setMonto("");
      setMoneda("ARS");
    }
  }, [abierto]);

  async function alGuardar() {
    const montoNum = parseFloat(monto);
    if (!cat.trim() || !montoNum || montoNum <= 0) {
      toast(trd("completa_cat_monto", lang));
      return;
    }
    try {
      await guardar.mutateAsync({ categoria: cat.trim(), monto: montoNum, moneda });
      setCat("");
      setMonto("");
      toast(trd("presupuesto_guardado", lang));
    } catch {
      toast(trd("error_guardar", lang));
    }
  }

  async function alBorrar(id: number) {
    try {
      await borrar.mutateAsync(id);
      toast(trd("presupuesto_eliminado", lang));
    } catch {
      toast(trd("error_guardar", lang));
    }
  }

  return (
    <Modal abierto={abierto} titulo={trd("presupuestos_del_mes", lang)} onCerrar={onCerrar} grande>
      {presupuestos.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          {presupuestos.map((p) => (
            <div
              key={p.id}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "8px 0",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <div>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{p.categoria}</span>
                <span style={{ fontSize: 12, color: "var(--muted)", marginLeft: 8 }}>
                  {fmtMon(p.monto, p.moneda ?? "ARS")}
                  {trd("por_mes", lang)}
                  {p.moneda && p.moneda !== "ARS" ? ` · ${p.moneda}` : ""}
                </span>
              </div>
              <button
                onClick={() => alBorrar(p.id)}
                aria-label="Eliminar presupuesto"
                style={{ background: "none", border: "none", color: "var(--muted)", fontSize: 18, cursor: "pointer", padding: "0 4px", lineHeight: 1 }}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      <div className={css.campo}>
        <label htmlFor="presup-cat">Categoría</label>
        <input
          id="presup-cat"
          type="text"
          list="cat-suggestions-presup"
          placeholder="Ej: Supermercado"
          autoComplete="off"
          value={cat}
          onChange={(e) => setCat(e.target.value)}
        />
        <datalist id="cat-suggestions-presup">
          {categorias.map((c) => (
            <option key={c} value={c} />
          ))}
        </datalist>
      </div>
      <div className={css.campo}>
        <label>Moneda</label>
        <div className={css.monedaToggle} style={{ marginTop: 4 }}>
          {MONEDAS.map((m) => (
            <button
              key={m}
              className={`${css.monedaBtn} ${moneda === m ? css.active : ""}`}
              onClick={() => setMoneda(m)}
            >
              {m === "ARS" ? "$ ARS" : m === "EUR" ? "€ EUR" : "USD"}
            </button>
          ))}
        </div>
      </div>
      <div className={css.campo}>
        <label>Límite mensual</label>
        <input type="number" min={1} placeholder="0" value={monto} onChange={(e) => setMonto(e.target.value)} />
      </div>
      <button className={css.btnGuardar} onClick={alGuardar} disabled={guardar.isPending}>
        Guardar presupuesto
      </button>
    </Modal>
  );
}
