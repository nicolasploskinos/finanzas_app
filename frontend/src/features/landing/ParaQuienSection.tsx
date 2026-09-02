import { usePreferencias } from "@/hooks/usePreferencias";
import { CHECKLIST } from "./content";
import css from "./Landing.module.css";

export function ParaQuienSection() {
  const { lang } = usePreferencias();

  return (
    <div className={css.paraQuien} id="para-quien">
      <div className={css.section}>
        <div className={css.twoCol}>
          <div>
            <div className={css.sectionLabel}>
              <span className={css.num}>03</span> —{" "}
              <span>{lang === "en" ? "Who it's for" : "Para quién es"}</span>
            </div>
            <h2 className={`${css.h2} ${css.h2Left}`}>
              {lang === "en" ? "Is this for you?" : "¿Esto es para vos?"}
            </h2>
            <p className={css.paraQuienSub}>
              {lang === "en" ? "If any of these sound familiar, yes." : "Si alguno de estos te suena familiar, sí."}
            </p>
            <ul className={css.checkList}>
              {CHECKLIST.map((item) => (
                <li key={item.es}>{item[lang]}</li>
              ))}
            </ul>
          </div>
          <div className={css.bigEmojiWrap}>
            <div className={css.bigEmoji}>💸</div>
          </div>
        </div>
      </div>
    </div>
  );
}
