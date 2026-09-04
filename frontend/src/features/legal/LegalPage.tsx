import { useLocation, useNavigate } from "react-router-dom";
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
  const navigate = useNavigate();
  const location = useLocation();

  /** Vuelve a la página desde la que se entró, no siempre a la landing.
   *
   *  A estas páginas se llega desde dos lugares distintos: el pie de la
   *  landing y el texto legal del formulario de registro. Mandar siempre a
   *  "/" dejaba a quien estaba por crearse una cuenta de nuevo en la landing,
   *  teniendo que rehacer todo el camino hasta el login.
   *
   *  `location.key` vale "default" cuando esta es la primera página de la
   *  visita (link compartido, resultado de Google): ahí no hay a dónde
   *  volver, así que va a la landing. */
  function volver() {
    if (location.key === "default") navigate("/");
    else navigate(-1);
  }

  return (
    <div className={nebula.theme} data-tema="nebula">
    <div className={css.page}>
      <div className={css.topbar}>
        <button type="button" className={css.volver} onClick={volver}>
          {lang === "en" ? "← Back" : "← Volver"}
        </button>
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
