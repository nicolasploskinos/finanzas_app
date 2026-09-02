import { usePreferencias } from "@/hooks/usePreferencias";
import { trd } from "./messages";
import css from "./Dashboard.module.css";

export function LimiteBanner({ count, onUpgrade }: { count: number; onUpgrade: () => void }) {
  const { lang } = usePreferencias();
  if (count < 35) return null;

  if (count >= 50) {
    return (
      <div className={`${css.limiteBanner} ${css.full}`}>
        {trd("limite_alcanzado", lang)}
        <button onClick={onUpgrade}>{trd("upgrade_a_pro", lang)}</button>
        {trd("para_seguir", lang)}
      </div>
    );
  }
  if (count >= 45) {
    return (
      <div className={`${css.limiteBanner} ${css.mid}`}>
        <span dangerouslySetInnerHTML={{ __html: trd("te_quedan_tx", lang, { n: 50 - count }) }} />
        <button onClick={onUpgrade}>{trd("upgrade_flecha", lang)}</button>
      </div>
    );
  }
  return (
    <div className={`${css.limiteBanner} ${css.warn}`}>
      {trd("usaste_tx", lang, { n: count })}
      <button onClick={onUpgrade}>{trd("ver_pro_flecha", lang)}</button>
    </div>
  );
}
