import { usePreferencias } from "@/hooks/usePreferencias";
import { trd } from "./messages";
import css from "./Dashboard.module.css";

export function TrialBanner({ dias, onSuscribirme }: { dias: number; onSuscribirme: () => void }) {
  const { lang } = usePreferencias();
  const dia = lang === "en" ? "day" : "día";
  const plural = dias === 1 ? "" : lang === "en" ? "s" : "s";
  const verbo = lang === "en" ? "you have" : dias === 1 ? "te queda" : "te quedan";

  return (
    <div className={css.trialBanner}>
      <span>
        {lang === "en" ? (
          <>
            🎉 <strong>Pro trial</strong> active — {verbo} <strong>{dias} {dia}{plural}</strong> left
          </>
        ) : (
          <>
            🎉 <strong>Prueba Pro</strong> activa — {verbo} <strong>{dias} {dia}{plural}</strong>
          </>
        )}
      </span>
      <a
        href="#"
        onClick={(e) => {
          e.preventDefault();
          onSuscribirme();
        }}
      >
        {trd("suscribirme", lang)}
      </a>
    </div>
  );
}
