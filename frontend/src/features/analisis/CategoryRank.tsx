import { useEffect, useState } from "react";

import { usePreferencias } from "@/hooks/usePreferencias";
import { fmtARS } from "./analytics";
import type { Analisis } from "./analytics";
import css from "./Analisis.module.css";

const COLORES = [
  "#4f8cf7",
  "#f0576a",
  "#34d399",
  "#f5b95c",
  "#9d7bf5",
  "#2dd4bf",
  "#fb923c",
  "#f472b6",
];

export function CategoryRank({ categorias }: { categorias: Analisis["categorias"] }) {
  const { t } = usePreferencias();
  // Las barras se pintan en 0% y recién en el frame siguiente toman su ancho
  // real, para que la transición de CSS tenga de dónde animar.
  const [reveladas, setReveladas] = useState(false);

  useEffect(() => {
    setReveladas(false);
    const raf = requestAnimationFrame(() => setReveladas(true));
    return () => cancelAnimationFrame(raf);
  }, [categorias]);

  if (!categorias.length) return <div className={css.empty}>{t("sin_gastos")}</div>;

  const max = categorias[0].total;

  return (
    <div className={css.catRank}>
      {categorias.map((c, i) => (
        <div
          key={c.nombre}
          className={`${css.catRow} stagger-in`}
          style={{ animationDelay: `${i * 60}ms` }}
        >
          <div className={css.catName}>{c.nombre}</div>
          <div className={css.catTrack}>
            <div
              className={css.catFill}
              style={{
                width: reveladas ? `${((c.total / max) * 100).toFixed(1)}%` : "0%",
                background: COLORES[i % COLORES.length],
              }}
            />
          </div>
          <div className={css.catVal}>{fmtARS(c.total)}</div>
        </div>
      ))}
    </div>
  );
}
