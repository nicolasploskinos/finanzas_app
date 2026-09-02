import { ArcElement, Chart as ChartJS, Legend, Tooltip } from "chart.js";
import { Doughnut } from "react-chartjs-2";

import { useColoresTema } from "@/hooks/useColoresTema";
import { fmtMon } from "@/lib/formato";

ChartJS.register(ArcElement, Legend, Tooltip);

const COLORES = [
  "#60a5fa",
  "#f87171",
  "#4ade80",
  "#fbbf24",
  "#a78bfa",
  "#fb923c",
  "#34d399",
  "#f472b6",
  "#38bdf8",
  "#facc15",
];

type Props = { categorias: Array<{ nombre: string; total: number }> };

export function CategoriaDonut({ categorias }: Props) {
  const c = useColoresTema();
  const total = categorias.reduce((a, x) => a + x.total, 0);

  return (
    <Doughnut
      data={{
        labels: categorias.map((x) => x.nombre),
        datasets: [
          {
            data: categorias.map((x) => x.total),
            backgroundColor: categorias.map((_, i) => COLORES[i % COLORES.length]),
            borderWidth: 0,
            hoverOffset: 4,
          },
        ],
      }}
      options={{
        responsive: true,
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: c.muted, font: { size: 11 }, padding: 8, boxWidth: 12 },
          },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const v = ctx.raw as number;
                return ` ${fmtMon(v, "USD")} (${Math.round((v / total) * 100)}%)`;
              },
            },
          },
        },
      }}
    />
  );
}
