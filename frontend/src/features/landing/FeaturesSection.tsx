import { usePreferencias } from "@/hooks/usePreferencias";
import { FEATURES, HERO_TILES } from "./content";
import { HeroTile } from "./HeroTile";
import { MiniConverter } from "./MiniConverter";
import { Reveal } from "./Reveal";
import css from "./Landing.module.css";

export function FeaturesSection({ contenedor }: { contenedor: HTMLElement | null }) {
  const { lang } = usePreferencias();

  return (
    <section className={css.section} id="features">
      <div className={css.sectionLabel}>
        <span className={css.num}>02</span> — <span>{lang === "en" ? "Why Montor" : "Por qué Montor"}</span>
      </div>
      <h2 className={css.h2}>
        {lang === "en" ? "Everything you need, nothing you don't" : "Todo lo que necesitás, nada que no"}
      </h2>
      <p className={css.sectionSub}>
        {lang === "en"
          ? "Built for people juggling more than one currency who don't want to overcomplicate it."
          : "Diseñado para argentinos que manejan más de una moneda y no quieren complicarse."}
      </p>

      <div className={css.heroTiles}>
        {HERO_TILES.map((tile, i) => (
          <HeroTile key={tile.icon} tile={tile} index={i} contenedor={contenedor} />
        ))}
      </div>
      <div className={css.gridMiniLabel}>{lang === "en" ? "And there's more:" : "Y además:"}</div>

      <div className={css.featuresGrid}>
        {FEATURES.map((f, i) => (
          <Reveal key={f.icon + f.title.es} contenedor={contenedor} index={i} className={css.featCard}>
            <div className={css.featIcon}>{f.icon}</div>
            <h3>{f.title[lang]}</h3>
            <p>{f.body[lang]}</p>
            {f.slot === "converter" && <MiniConverter />}
          </Reveal>
        ))}
      </div>
    </section>
  );
}
