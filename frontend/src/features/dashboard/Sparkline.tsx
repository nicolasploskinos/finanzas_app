import {
  Chart as ChartJS,
  Filler,
  LineElement,
  LinearScale,
  PointElement,
  CategoryScale,
} from "chart.js";
import { Line } from "react-chartjs-2";

import { useColoresTema } from "@/hooks/useColoresTema";

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, Filler);

export function Sparkline({ puntos }: { puntos: number[] }) {
  const c = useColoresTema();
  const ultimos = puntos.slice(-30);

  return (
    <Line
      data={{
        labels: ultimos.map((_, i) => i),
        datasets: [
          {
            data: ultimos,
            borderColor: c.blue,
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.35,
            fill: true,
            backgroundColor: c.blue + "22",
          },
        ],
      }}
      options={{
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        scales: { x: { display: false }, y: { display: false } },
      }}
    />
  );
}
