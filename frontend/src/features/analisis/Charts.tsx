import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from "chart.js";
import { Bar, Line } from "react-chartjs-2";

import { useColoresTema } from "@/hooks/useColoresTema";
import { usePreferencias } from "@/hooks/usePreferencias";
import type { Analisis } from "./analytics";
import css from "./Analisis.module.css";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Filler,
  Legend,
  Tooltip,
);

/** Ejes y grilla, iguales en los dos gráficos. */
function escalas(muted: string, border: string) {
  return {
    x: { ticks: { color: muted }, grid: { display: false } },
    y: { ticks: { color: muted }, grid: { color: border } },
  };
}

export function MonthlyChart({ meses }: { meses: Analisis["meses"] }) {
  const { t } = usePreferencias();
  const c = useColoresTema();

  return (
    <div className={css.chartWrap}>
      <Bar
        data={{
          labels: meses.map((m) => m.label),
          datasets: [
            {
              label: t("ingresos_totales"),
              data: meses.map((m) => m.ing),
              backgroundColor: c.green,
              borderRadius: 4,
            },
            {
              label: t("gastos_totales"),
              data: meses.map((m) => m.gas),
              backgroundColor: c.red,
              borderRadius: 4,
            },
          ],
        }}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: "bottom", labels: { color: c.muted } } },
          scales: escalas(c.muted, c.border),
        }}
      />
    </div>
  );
}

export function TrendChart({ meses }: { meses: Analisis["meses"] }) {
  const c = useColoresTema();

  let acumulado = 0;
  const serie = meses.map((m) => (acumulado += m.ing - m.gas));

  return (
    <div className={css.chartWrapCorto}>
      <Line
        data={{
          labels: meses.map((m) => m.label),
          datasets: [
            {
              data: serie,
              borderColor: c.blue,
              backgroundColor: c.blue + "22",
              fill: true,
              tension: 0.3,
              pointRadius: 3,
            },
          ],
        }}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: escalas(c.muted, c.border),
        }}
      />
    </div>
  );
}
