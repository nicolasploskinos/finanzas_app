import { useEffect, useState } from "react";

import modalCss from "@/components/Modal.module.css";
import { usePreferencias } from "@/hooks/usePreferencias";
import { trd } from "./messages";
import css from "./Dashboard.module.css";

type Ciclo = "mensual" | "anual";

const BENEFICIOS: Array<{ icono: string; titulo: { es: string; en: string }; cuerpo: { es: string; en: string } }> = [
  {
    icono: "♾️",
    titulo: { es: "Transacciones ilimitadas", en: "Unlimited transactions" },
    cuerpo: {
      es: "La cuenta gratis tiene un límite de 50 transacciones por mes. Con Pro podés registrar todo sin límite.",
      en: "The free plan has a limit of 50 transactions per month. With Pro you can log everything with no limit.",
    },
  },
  {
    icono: "📅",
    titulo: { es: "Historial completo", en: "Full history" },
    cuerpo: {
      es: "La cuenta gratis muestra solo los últimos 3 meses. Con Pro accedés a todo tu historial.",
      en: "The free plan only shows the last 3 months. With Pro you get access to your whole history.",
    },
  },
  {
    icono: "🔄",
    titulo: { es: "Gastos recurrentes", en: "Recurring expenses" },
    cuerpo: {
      es: "Configurá el alquiler, suscripciones y otros gastos fijos para que se agreguen solos cada semana o mes.",
      en: "Set up rent, subscriptions, and other fixed expenses so they get added by themselves every week or month.",
    },
  },
  {
    icono: "📊",
    titulo: { es: "Exportar a Excel / CSV", en: "Export to Excel / CSV" },
    cuerpo: {
      es: "Descargá todas tus transacciones para analizarlas en Excel o Google Sheets.",
      en: "Download all your transactions to analyze them in Excel or Google Sheets.",
    },
  },
];

export function ProModal({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const { lang } = usePreferencias();
  const [ciclo, setCiclo] = useState<Ciclo>("mensual");

  useEffect(() => {
    if (abierto) setCiclo("mensual");
  }, [abierto]);

  useEffect(() => {
    if (!abierto) return;
    const alTeclear = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCerrar();
    };
    document.addEventListener("keydown", alTeclear);
    return () => document.removeEventListener("keydown", alTeclear);
  }, [abierto, onCerrar]);

  function pagar() {
    window.location.href = `/api/montor/suscribir?ciclo=${ciclo}`;
  }

  return (
    <div
      className={`${css.proOverlay} ${abierto ? modalCss.open : ""}`}
      onClick={(e) => {
        if (e.target === e.currentTarget) onCerrar();
      }}
      role="dialog"
      aria-modal="true"
      aria-hidden={!abierto}
    >
      <div className={css.proModal}>
        <div className={css.proModalHandle} />
        <div className={css.proTitulo}>⭐ Montor Pro</div>
        <p className={css.proPrecio}>{lang === "en" ? "Choose your plan" : "Elegí tu plan"}</p>

        <div className={css.proCiclos}>
          <button className={`${css.proCicloBtn} ${ciclo === "mensual" ? css.active : ""}`} onClick={() => setCiclo("mensual")}>
            <div className={css.proCicloNombre}>{lang === "en" ? "Monthly" : "Mensual"}</div>
            <div className={css.proCicloPrecio}>
              $6.000<span>{lang === "en" ? "/mo" : "/mes"}</span>
            </div>
          </button>
          <button className={`${css.proCicloBtn} ${ciclo === "anual" ? css.active : ""}`} onClick={() => setCiclo("anual")}>
            <div className={css.proCicloBadge}>{lang === "en" ? "2 months free" : "2 meses gratis"}</div>
            <div className={css.proCicloNombre}>{lang === "en" ? "Yearly" : "Anual"}</div>
            <div className={css.proCicloPrecio}>
              $60.000<span>{lang === "en" ? "/yr" : "/año"}</span>
            </div>
          </button>
        </div>

        <div className={css.proBeneficios}>
          {BENEFICIOS.map((b) => (
            <div key={b.icono} className={css.proFila}>
              <div className={css.proFilaIcono}>{b.icono}</div>
              <div className={css.proFilaTexto}>
                <h4>{b.titulo[lang]}</h4>
                <p>{b.cuerpo[lang]}</p>
              </div>
            </div>
          ))}
        </div>

        <button className={css.btnProPagar} onClick={pagar}>
          {ciclo === "anual" ? trd("suscribirme_anual", lang) : trd("suscribirme_mensual", lang)}
        </button>
        <button className={css.btnProCancel} onClick={onCerrar}>
          {lang === "en" ? "Not now" : "Ahora no"}
        </button>
      </div>
    </div>
  );
}
