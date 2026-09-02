import { useCountUp } from "@/hooks/useCountUp";
import { usePreferencias } from "@/hooks/usePreferencias";
import type { MsgKey } from "@/i18n/messages";
import { fmtARS } from "./analytics";
import type { Analisis } from "./analytics";
import css from "./Analisis.module.css";

type KpiProps = {
  variante: "ingresos" | "gastos" | "balance" | "promedio";
  label: MsgKey;
  valor: number;
  color?: string;
  formato?: (n: number) => string;
};

function Kpi({ variante, label, valor, color, formato = fmtARS }: KpiProps) {
  const { t } = usePreferencias();
  const animado = useCountUp(valor);

  return (
    <div className={`${css.kpiCard} ${css[variante]}`}>
      <div className={css.kpiLabel}>{t(label)}</div>
      <div className={css.kpiValue} style={color ? { color } : undefined}>
        {formato(animado)}
      </div>
    </div>
  );
}

const conSigno = (n: number) => (n >= 0 ? "+" : "-") + fmtARS(Math.abs(n));

export function KpiGrid({ analisis }: { analisis: Analisis }) {
  return (
    <div className={css.kpiGrid}>
      <Kpi
        variante="ingresos"
        label="ingresos_totales"
        valor={analisis.ingTotal}
        color="var(--green)"
      />
      <Kpi variante="gastos" label="gastos_totales" valor={analisis.gasTotal} color="var(--red)" />
      <Kpi
        variante="balance"
        label="balance_neto"
        valor={analisis.balanceNeto}
        color={analisis.balanceNeto >= 0 ? "var(--green)" : "var(--red)"}
        formato={conSigno}
      />
      <Kpi variante="promedio" label="promedio_mensual" valor={analisis.promedioMensual} />
    </div>
  );
}
