import { useEffect, useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Chart.js global defaults for our dark theme
ChartJS.defaults.color = '#94a3b8';
ChartJS.defaults.borderColor = 'rgba(255, 255, 255, 0.06)';
ChartJS.defaults.font.family = "'Inter', sans-serif";

/**
 * Reusable chart wrapper for line and bar charts.
 */
export default function TelemetryChart({
  type = 'line',
  labels = [],
  datasets = [],
  title = '',
  yAxisLabel = '',
  height = 300,
  annotation = null,  // { value, label, color } for threshold line
}) {
  const chartData = {
    labels,
    datasets: datasets.map((ds, i) => ({
      label: ds.label || `Series ${i + 1}`,
      data: ds.data || [],
      borderColor: ds.color || '#3b82f6',
      backgroundColor: ds.fill
        ? `${ds.color || '#3b82f6'}20`
        : 'transparent',
      fill: ds.fill || false,
      tension: 0.4,
      pointRadius: ds.pointRadius ?? 0,
      pointHoverRadius: 4,
      borderWidth: 2,
      ...ds.overrides,
    })),
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        display: datasets.length > 1,
        position: 'top',
        labels: {
          boxWidth: 12,
          padding: 16,
          usePointStyle: true,
        },
      },
      title: {
        display: !!title,
        text: title,
        font: { size: 14, weight: 600 },
        padding: { bottom: 16 },
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#f1f5f9',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 12,
        cornerRadius: 8,
        displayColors: true,
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { maxTicksLimit: 12, maxRotation: 0 },
      },
      y: {
        title: {
          display: !!yAxisLabel,
          text: yAxisLabel,
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.04)',
        },
        beginAtZero: true,
      },
    },
  };

  const ChartComponent = type === 'bar' ? Bar : Line;

  return (
    <div style={{ height }}>
      <ChartComponent data={chartData} options={options} />
    </div>
  );
}
