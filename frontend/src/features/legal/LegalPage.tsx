import { Link } from "react-router-dom";
import { usePreferencias } from "@/hooks/usePreferencias";
import nebula from "@/styles/nebula.module.css";
import css from "./Legal.module.css";

export type Seccion = {
  heading: { es: string; en: string };
  /** HTML (puede traer <strong>, <a>, <ul><li>...). Contenido fijo escrito
   *  por nosotros, no input de usuario, así que dangerouslySetInnerHTML es
   *  seguro acá. */
  body: { es: string; en: string };
};

type Props = {
  titulo: { es: string; en: string };
  actualizado: { es: string; en: string };
  intro: { es: string; en: string };
  secciones: Seccion[];
};

export function LegalPage({ titulo, actualizado, intro, secciones }: Props) {
  const { modo, lang, toggleModo, toggleLang } = usePreferencias();

  return (
    <div className={nebula.theme} data-tema="nebula">
    <div className={css.page}>
      <div className={css.topbar}>
        <Link to="/">{lang === "en" ? "← Back to Montor" : "← Volver a Montor"}</Link>
        <div className={css.acciones}>
          <button onClick={toggleLang} title="Switch language">
            {lang === "en" ? "ES" : "EN"}
          </button>
          <button onClick={toggleModo} title="Cambiar modo">
            {modo === "light" ? "☀️" : "🌙"}
          </button>
        </div>
      </div>
      <main className={css.main}>
        <h1 className={css.h1}>{titulo[lang]}</h1>
        <p className={css.actualizado}>{actualizado[lang]}</p>

        <div className="legal-body" dangerouslySetInnerHTML={{ __html: intro[lang] }} />

        {secciones.map((s, i) => (
          <div key={i}>
            <h2 className={css.h2}>{s.heading[lang]}</h2>
            <div className="legal-body" dangerouslySetInnerHTML={{ __html: s.body[lang] }} />
          </div>
        ))}
      </main>
    </div>
    </div>
  );
}
