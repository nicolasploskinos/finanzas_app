import { ArcElement, Chart as ChartJS, Legend, Tooltip } from "chart.js";
import { Doughnut } from "react-chartjs-2";

import { useColoresTema } from "@/hooks/useColoresTema";
import { fmtMon } from "@/lib/formato";

ChartJS.register(ArcElement, Legend, Tooltip);

const COLORES = [
  "#7c5cff",
  "#ff4d75",
  "#00e0a4",
  "#ffb93d",
  "#c084fc",
  "#2fe6c7",
  "#5b8def",
  "#ff8fab",
  "#f5a623",
  "#4dd4e8",
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
