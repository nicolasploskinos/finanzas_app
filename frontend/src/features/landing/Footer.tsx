import { usePreferencias } from "@/hooks/usePreferencias";
import { FOOTER_CUENTA, FOOTER_LEGAL, FOOTER_PRODUCT } from "./content";
import css from "./Landing.module.css";
import { LogoMontor } from "@/components/LogoMontor";

export function Footer() {
  const { lang } = usePreferencias();

  return (
    <footer className={css.footer}>
      <div className={css.footerInner}>
        <div>
          <div className={css.footerBrand}>
            <LogoMontor size={24} />
            <span>Montor</span>
          </div>
          <p className={css.footerTagline}>
            {lang === "en"
              ? "Control your expenses and income in pesos, dollars, and euros. Built for Argentina."
              : "Controlá tus gastos e ingresos en pesos, dólares y euros. Hecha para la economía argentina."}
          </p>
        </div>

        <div className={css.footerCol}>
          <div className={css.footerColTitle}>{lang === "en" ? "Product" : "Producto"}</div>
          {FOOTER_PRODUCT.map((l) => (
            <a key={l.href} href={l.href}>
              {l.label[lang]}
            </a>
          ))}
        </div>

        <div className={css.footerCol}>
          <div className={css.footerColTitle}>Legal</div>
          {FOOTER_LEGAL.map((l) => (
            <a key={l.href} href={l.href}>
              {l.label[lang]}
            </a>
          ))}
        </div>

        <div className={css.footerCol}>
          <div className={css.footerColTitle}>{lang === "en" ? "Account" : "Cuenta"}</div>
          {FOOTER_CUENTA.map((l) => (
            <a key={l.href} href={l.href}>
              {l.label[lang]}
            </a>
          ))}
        </div>
      </div>
      <div className={css.footerBottom}>
        <span>{lang === "en" ? "© 2026 Montor. All rights reserved." : "© 2026 Montor. Todos los derechos reservados."}</span>
        <span>{lang === "en" ? "Made in Argentina 🇦🇷" : "Hecho en Argentina 🇦🇷"}</span>
      </div>
    </footer>
  );
}
