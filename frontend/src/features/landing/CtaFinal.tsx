import { Link } from "react-router-dom";
import { usePreferencias } from "@/hooks/usePreferencias";
import css from "./Landing.module.css";

export function CtaFinal() {
  const { lang } = usePreferencias();
  return (
    <section className={css.ctaFinal}>
      <h2>
        {lang === "en"
          ? "Ready to stop guessing where your money went?"
          : "¿Listo para dejar de adivinar en qué se te fue la plata?"}
      </h2>
      <p>
        {lang === "en"
          ? "No card required. Set up your first transaction in under 2 minutes."
          : "Sin tarjeta necesaria. Cargá tu primera transacción en menos de 2 minutos."}
      </p>
      <Link to="/montor/login" className={css.btnPrimary}>
        {lang === "en" ? "I want free access →" : "Quiero acceso gratis →"}
      </Link>
    </section>
  );
}
