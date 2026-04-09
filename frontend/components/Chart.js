import React from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
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
  ArcElement
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

export default function Chart({ chartData }) {
  if (!chartData) return null;

  const { type = 'bar', labels, datasets, title } = chartData;
  
  const options = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      title: {
        display: !!title,
        text: title,
        font: { size: 14, weight: 'bold' }
      },
      legend: {
        display: true,
        position: 'top'
      }
    },
    scales: {
      y: {
        beginAtZero: true
      }
    }
  };

  const data = { labels, datasets };

  const ChartComponent = 
    type === 'line' ? Line :
    type === 'doughnut' ? Doughnut :
    Bar;

  return (
    <div style={{
      width: '100%',
      height: '400px',
      margin: '20px 0',
      padding: '10px',
      backgroundColor: '#f9fafb',
      borderRadius: '8px'
    }}>
      <ChartComponent data={data} options={options} />
    </div>
  );
}
