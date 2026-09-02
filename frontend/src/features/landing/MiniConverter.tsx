import { useState } from "react";

import { usePreferencias } from "@/hooks/usePreferencias";
import css from "./Landing.module.css";

// Cotización de ejemplo fija para la demo (la app real la actualiza sola
// todos los días contra la API de BNA).
const RATE_USD = 1450;
const RATE_EUR = 1580;

export function MiniConverter() {
  const { lang } = usePreferencias();
  const [ars, setArs] = useState("");

  const monto = parseFloat(ars) || 0;
  const fmt = (n: number) => n.toLocaleString("es-AR", { maximumFractionDigits: 2 });

  return (
    <div className={css.miniConvert}>
      <div className={css.miniConvertRow}>
        <label htmlFor="mc-ars">ARS $</label>
        <input
          id="mc-ars"
          type="number"
          inputMode="decimal"
          placeholder="10000"
          value={ars}
          onChange={(e) => setArs(e.target.value)}
        />
      </div>
      <div className={css.miniConvertOut}>
        <span>≈ USD</span> <strong>{fmt(monto / RATE_USD)}</strong>
        <span>≈ EUR</span> <strong>{fmt(monto / RATE_EUR)}</strong>
      </div>
      <div className={css.miniConvertNote}>
        {lang === "en"
          ? "Example rate for the demo — the real app updates it automatically every day."
          : "Cotización de ejemplo para la demo — en la app real se actualiza sola todos los días."}
      </div>
    </div>
  );
}
