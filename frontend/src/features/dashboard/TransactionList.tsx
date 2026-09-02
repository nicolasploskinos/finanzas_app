import { Fragment, useState } from "react";

import type { Transaccion } from "@/api/types";
import { usePreferencias } from "@/hooks/usePreferencias";
import { MESES_ES, MESES_EN } from "./meses";
import { trd } from "./messages";
import { TxRow } from "./TxRow";
import css from "./Dashboard.module.css";

const TOPE_MOBILE = 5;

type Props = {
  lista: Transaccion[];
  onEditar: (id: number) => void;
  onBorrar: (id: number) => Promise<boolean>;
};

export function TransactionList({ lista, onEditar, onBorrar }: Props) {
  const { lang } = usePreferencias();
  // No se resetea al cambiar de filtro a propósito: una vez que decidiste
  // ver todo, se queda así (igual que el original).
  const [verTodas, setVerTodas] = useState(false);

  if (!lista.length) return <div className={css.empty}>{trd("sin_movimientos", lang)}</div>;

  // En mobile la lista completa empuja todo lo demás fuera de la pantalla:
  // se muestran los últimos 5 movimientos y el resto queda detrás de "Ver
  // más". En escritorio hay una columna entera para la lista.
  const esMobile = typeof window !== "undefined" && window.matchMedia("(max-width: 899px)").matches;
  const recortar = esMobile && !verTodas && lista.length > TOPE_MOBILE;
  const visibles = recortar ? lista.slice(0, TOPE_MOBILE) : lista;

  const meses = lang === "en" ? MESES_EN : MESES_ES;
  const grupos = new Map<string, Transaccion[]>();
  for (const t of visibles) {
    const f = new Date(t.fecha + "T00:00:00");
    const k = `${meses[f.getMonth()]} ${f.getFullYear()}`;
    if (!grupos.has(k)) grupos.set(k, []);
    grupos.get(k)!.push(t);
  }

  // El mes-header y cada TxRow van como hermanos DIRECTOS de `.lista` (sin
  // un div contenedor por grupo) a propósito: en pantallas muy anchas
  // `.lista` pasa a ser un grid de 2 columnas y `.mesHeader` necesita ser un
  // hijo directo para que `grid-column: 1 / -1` lo estire en toda la fila.
  let i = 0;
  return (
    <div className={css.lista}>
      {[...grupos.entries()].map(([mes, txs]) => (
        <Fragment key={mes}>
          <div className={css.mesHeader}>{mes}</div>
          {txs.map((t) => (
            <TxRow key={t.id} t={t} index={i++} onEditar={onEditar} onBorrar={onBorrar} />
          ))}
        </Fragment>
      ))}
      {recortar && (
        <button className={css.verMasBtn} onClick={() => setVerTodas(true)}>
          {trd("ver_mas_tx", lang, { n: lista.length - TOPE_MOBILE })}
        </button>
      )}
    </div>
  );
}
