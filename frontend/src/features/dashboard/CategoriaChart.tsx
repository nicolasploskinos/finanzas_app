import { ArcElement, Chart as ChartJS, Legend, Tooltip } from "chart.js";
import { Doughnut } from "react-chartjs-2";

import type { StatsCategoria } from "@/api/types";
import { useColoresTema } from "@/hooks/useColoresTema";

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

export function CategoriaChart({ categorias }: { categorias: StatsCategoria[] }) {
  const c = useColoresTema();

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
                const total = (ctx.dataset.data as number[]).reduce((a, b) => a + b, 0);
                const v = ctx.raw as number;
                return ` $${Math.round(v).toLocaleString("es-AR")} (${Math.round((v / total) * 100)}%)`;
              },
            },
          },
        },
      }}
    />
  );
}
