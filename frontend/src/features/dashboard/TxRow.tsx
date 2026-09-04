import { useRef } from "react";

import type { Transaccion } from "@/api/types";
import { usePreferencias } from "@/hooks/usePreferencias";
import { fmtMon, formatFecha } from "@/lib/formato";
import { trd } from "./messages";
import css from "./Dashboard.module.css";
import { useConfirmar } from "@/components/Confirmacion";

const SWIPE_DELETE_PX = 80;

type Props = {
  t: Transaccion;
  index: number;
  onEditar: (id: number) => void;
  onBorrar: (id: number) => Promise<boolean>;
};

/**
 * Fila de transacción con deslizar-para-borrar en touch. El seguimiento del
 * dedo (transform en cada touchmove) va directo al DOM vía ref, no a un
 * estado de React: son eventos de altísima frecuencia y puramente visuales
 * mientras se arrastra.
 */
export function TxRow({ t, index, onEditar, onBorrar }: Props) {
  const { lang } = usePreferencias();
  const confirmar = useConfirmar();
  const elRef = useRef<HTMLDivElement | null>(null);
  const estado = useRef({ startX: 0, startY: 0, dx: 0, scrolling: false, activo: false });

  function alTocar(e: React.TouchEvent) {
    estado.current = { startX: e.touches[0].clientX, startY: e.touches[0].clientY, dx: 0, scrolling: false, activo: true };
    elRef.current?.classList.add(css.swiping);
  }

  function alMover(e: React.TouchEvent) {
    const s = estado.current;
    if (!s.activo || !elRef.current) return;
    const dx = e.touches[0].clientX - s.startX;
    const dy = e.touches[0].clientY - s.startY;
    if (!s.scrolling && Math.abs(dy) > Math.abs(dx) + 5) s.scrolling = true;
    if (s.scrolling || dx < 0) {
      elRef.current.classList.remove(css.swiping);
      s.activo = false;
      return;
    }
    // El CSS ya pone touch-action:pan-y en .tx (el scroll vertical lo
    // maneja el navegador nativamente); este preventDefault es una red
    // extra para que un swipe horizontal no dispare gestos del navegador.
    if (e.cancelable) e.preventDefault();
    s.dx = dx;
    elRef.current.style.transform = `translateX(${Math.min(dx, 120)}px)`;
  }

  async function alSoltar() {
    const s = estado.current;
    const el = elRef.current;
    if (!s.activo || !el) return;
    s.activo = false;
    el.classList.remove(css.swiping);

    if (s.dx <= SWIPE_DELETE_PX) {
      el.style.transition = "transform .2s";
      el.style.transform = "translateX(0)";
      return;
    }
    const ok = await confirmar({
      titulo: trd("dlg_borrar_tx_t", lang),
      mensaje: trd("dlg_borrar_tx_m", lang),
      confirmar: trd("dlg_eliminar", lang),
      cancelar: trd("dlg_cancelar", lang),
      peligro: true,
    });
    if (!ok) {
      el.style.transition = "transform .2s";
      el.style.transform = "translateX(0)";
      return;
    }
    el.style.transition = "transform .2s, opacity .15s";
    el.style.transform = "translateX(110%)";
    el.style.opacity = "0";
    setTimeout(async () => {
      const ok = await onBorrar(t.id);
      if (!ok && el) {
        el.style.transition = "transform .2s, opacity .15s";
        el.style.transform = "translateX(0)";
        el.style.opacity = "1";
      }
    }, 180);
  }

  const mon = t.moneda ?? "ARS";
  const tipoClase = t.tipo === "Ingreso" ? css.ingreso : css.gasto;
  const delay = Math.min(index, 12) * 30;

  return (
    <div className={`${css.txWrap} ${css.staggerIn}`} style={{ animationDelay: `${delay}ms` }}>
      <div className={css.txSwipeBg}>🗑</div>
      <div
        ref={elRef}
        // El ejemplo se distingue por un tinte y no por una etiqueta de texto:
        // a .txInfo le quedan menos de 100px en escritorio angosto, y cualquier
        // texto extra ahí se come la categoría (la dejaba en "S…").
        className={`${css.tx} ${tipoClase} ${t.es_ejemplo ? css.txEjemplo : ""}`}
        onTouchStart={alTocar}
        onTouchMove={alMover}
        onTouchEnd={alSoltar}
      >
        <div className={`${css.txIcon} ${tipoClase}`}>{t.tipo === "Ingreso" ? "↑" : "↓"}</div>
        <div className={css.txInfo}>
          <div className={css.txCat}>{t.categoria || trd("sin_categoria", lang)}</div>
          {t.descripcion && <div className={css.txDesc}>{t.descripcion}</div>}
          <div className={css.txFecha}>{formatFecha(t.fecha, lang)}</div>
        </div>
        <div className={css.txRight}>
          <div className={`${css.txMonto} ${tipoClase}`}>
            {t.tipo === "Ingreso" ? "+" : "-"}
            {fmtMon(t.monto, mon)}
          </div>
          {mon !== "ARS" && <div className={css.badgeMon}>{mon}</div>}
        </div>
        <button className={css.txEdit} onClick={() => onEditar(t.id)} aria-label="Editar transacción">
          ✏️
        </button>
      </div>
    </div>
  );
}
