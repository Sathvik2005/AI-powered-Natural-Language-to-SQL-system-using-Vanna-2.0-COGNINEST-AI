import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import gsap from 'gsap';
import Head from 'next/head';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Pie } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const Dashboard = () => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  const [selectedResult, setSelectedResult] = useState(null);

  const containerRef = useRef(null);
  const cardRef = useRef(null);
  const tableRef = useRef(null);

  // Animate on component load
  useEffect(() => {
    if (containerRef.current) {
      gsap.from(containerRef.current, {
        opacity: 0,
        y: 20,
        duration: 0.6,
        ease: 'power2.out',
      });
    }
  }, []);

  // Animate results card when data appears
  useEffect(() => {
    if (response && cardRef.current) {
      gsap.from(cardRef.current, {
        opacity: 0,
        scale: 0.95,
        duration: 0.4,
        ease: 'back.out',
      });
    }
  }, [response]);

  // Animate table rows
  useEffect(() => {
    if (tableRef.current) {
      const rows = tableRef.current.querySelectorAll('tbody tr');
      gsap.from(rows, {
        opacity: 0,
        x: -20,
        duration: 0.3,
        stagger: 0.05,
        ease: 'power2.out',
      });
    }
  }, [response?.rows]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setError('');
    setResponse(null);

    try {
      const res = await axios.post(`${apiUrl}/chat`, {
        question: question.trim(),
      }, { timeout: 30000 });

      const data = res.data;
      setResponse(data);

      setHistory([
        {
          question: question.trim(),
          timestamp: new Date().toLocaleTimeString(),
          status: data.rows && data.rows.length > 0 ? 'success' : 'no_data',
        },
        ...history.slice(0, 9),
      ]);

      setQuestion('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to process question';
      setError(errorMsg);
      console.error('API Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const renderTable = () => {
    if (!response?.rows || response.rows.length === 0) {
      return <div className="text-gray-400 text-center py-8">No data returned</div>;
    }

    const displayRows = response.rows.slice(0, 50);

    return (
      <div className="overflow-x-auto rounded-lg border border-blue-700 border-opacity-30">
        <table ref={tableRef} className="min-w-full">
          <thead>
            <tr className="bg-gradient-to-r from-blue-600 to-blue-700 border-b border-blue-600">
              {response.columns?.map((col, idx) => (
                <th
                  key={idx}
                  className="px-6 py-3 text-left text-sm font-semibold text-white"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayRows.map((row, rowIdx) => (
              <tr
                key={rowIdx}
                className="border-b border-blue-700 border-opacity-20 hover:bg-blue-900 hover:bg-opacity-30 transition-colors"
              >
                {Array.isArray(row)
                  ? row.map((cell, cellIdx) => (
                      <td key={cellIdx} className="px-6 py-3 text-sm text-gray-300">
                        {cell !== null && cell !== undefined ? String(cell) : 'NULL'}
                      </td>
                    ))
                  : Object.values(row).map((cell, cellIdx) => (
                      <td key={cellIdx} className="px-6 py-3 text-sm text-gray-300">
                        {cell !== null && cell !== undefined ? String(cell) : 'NULL'}
                      </td>
                    ))}
              </tr>
            ))}
          </tbody>
        </table>
        {response.rows.length > 50 && (
          <div className="px-6 py-3 bg-slate-800 text-gray-400 text-sm border-t border-blue-700 border-opacity-20">
            Showing 50 of {response.rows.length} rows
          </div>
        )}
      </div>
    );
  };

  const renderChart = () => {
    if (!response?.chart) return null;

    try {
      const chartData = response.chart.data || [];
      const chartType = response.chart_type || 'bar';

      if (chartType === 'bar') {
        const labels = chartData.map((d) => d.x || d.name || '');
        const values = chartData.map((d) => d.y || d.value || 0);

        const data = {
          labels,
          datasets: [
            {
              label: 'Values',
              data: values,
              backgroundColor: 'rgba(59, 130, 246, 0.8)',
              borderColor: 'rgba(59, 130, 246, 1)',
              borderWidth: 1,
              borderRadius: 4,
            },
          ],
        };

        return (
          <div className="mt-8">
            <h3 className="text-lg font-bold text-white mb-4">Chart Visualization</h3>
            <div className="bg-slate-800 rounded-lg p-4 border border-blue-700 border-opacity-30">
              <Bar
                data={data}
                options={{
                  responsive: true,
                  maintainAspectRatio: true,
                  plugins: {
                    legend: {
                      labels: { color: '#e5e7eb' },
                    },
                  },
                  scales: {
                    y: {
                      ticks: { color: '#9ca3af' },
                      grid: { color: 'rgba(59, 130, 246, 0.1)' },
                    },
                    x: {
                      ticks: { color: '#9ca3af' },
                      grid: { color: 'rgba(59, 130, 246, 0.1)' },
                    },
                  },
                }}
                height={300}
              />
            </div>
          </div>
        );
      } else if (chartType === 'pie') {
        const labels = chartData.map((d) => d.label || d.name || '');
        const values = chartData.map((d) => d.value || 0);

        const data = {
          labels,
          datasets: [
            {
              data: values,
              backgroundColor: [
                'rgba(59, 130, 246, 0.8)',
                'rgba(147, 51, 234, 0.8)',
                'rgba(236, 72, 153, 0.8)',
                'rgba(245, 158, 11, 0.8)',
                'rgba(34, 197, 94, 0.8)',
              ],
              borderColor: 'rgba(30, 41, 59, 1)',
              borderWidth: 2,
            },
          ],
        };

        return (
          <div className="mt-8">
            <h3 className="text-lg font-bold text-white mb-4">Chart Visualization</h3>
            <div className="bg-slate-800 rounded-lg p-4 border border-blue-700 border-opacity-30 flex justify-center">
              <div style={{ width: '300px', height: '300px' }}>
                <Pie
                  data={data}
                  options={{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                      legend: {
                        labels: { color: '#e5e7eb' },
                        position: 'bottom',
                      },
                    },
                  }}
                />
              </div>
            </div>
          </div>
        );
      }

      return null;
    } catch (e) {
      console.error('Chart rendering error:', e);
      return null;
    }
  };

  return (
    <>
      <Head>
        <title>NL2SQL Analytics Dashboard</title>
        <meta name="description" content="Natural Language to SQL Analytics" />
      </Head>

      <div ref={containerRef} className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
        {/* Header */}
        <header className="border-b border-blue-800 bg-black bg-opacity-40 backdrop-blur-lg sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-blue-400 to-blue-600 rounded-lg">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h1 className="text-2xl font-bold text-white">Analytics Workspace</h1>
              </div>
              <div className="text-sm text-blue-300">Powered by NL2SQL</div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Sidebar - Query History */}
            <div className="lg:col-span-1">
              <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-6 border border-blue-700 border-opacity-30">
                <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                  <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Recent Queries
                </h2>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {history.length === 0 ? (
                    <p className="text-gray-400 text-sm">No recent queries</p>
                  ) : (
                    history.map((item, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-blue-900 bg-opacity-40 rounded-lg text-sm text-gray-200 hover:bg-opacity-60 transition-all cursor-pointer border border-blue-700 border-opacity-20"
                      >
                        <div className="font-medium text-blue-300">{item.question.substring(0, 25)}...</div>
                        <div className="text-xs text-gray-400 mt-1">{item.timestamp}</div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Main Panel */}
            <div className="lg:col-span-3 space-y-6">
              {/* Query Input */}
              <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 border border-blue-700 border-opacity-30 shadow-2xl">
                <form onSubmit={handleSubmit}>
                  <label className="block text-sm font-semibold text-gray-200 mb-4">
                    Ask a Question
                  </label>
                  <textarea
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="e.g., Show revenue by doctor, Which city has the most patients?, Top 5 patients by spending..."
                    rows={3}
                    className="w-full px-4 py-3 rounded-lg bg-slate-700 border border-blue-600 border-opacity-50 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-all"
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="mt-4 w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold py-3 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        Execute Query
                      </>
                    )}
                  </button>
                </form>
              </div>

              {/* Error Message */}
              {error && (
                <div className="bg-red-900 bg-opacity-20 border border-red-600 border-opacity-50 text-red-200 px-6 py-4 rounded-lg flex items-start gap-3">
                  <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <h3 className="font-semibold">Error</h3>
                    <p className="text-sm mt-1">{error}</p>
                  </div>
                </div>
              )}

              {/* Results */}
              {response && (
                <div ref={cardRef} className="space-y-6">
                  {/* Stats */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-4 text-white">
                      <div className="text-sm font-medium opacity-90">Records Found</div>
                      <div className="text-3xl font-bold mt-2">{response.row_count || 0}</div>
                    </div>
                    <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-xl p-4 text-white">
                      <div className="text-sm font-medium opacity-90">Columns</div>
                      <div className="text-3xl font-bold mt-2">{response.columns?.length || 0}</div>
                    </div>
                    <div className="bg-gradient-to-br from-indigo-600 to-indigo-700 rounded-xl p-4 text-white">
                      <div className="text-sm font-medium opacity-90">Status</div>
                      <div className="text-sm font-bold mt-2 text-green-300">Success</div>
                    </div>
                  </div>

                  {/* SQL Query Display */}
                  {response.sql_query && (
                    <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-6 border border-blue-700 border-opacity-30">
                      <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                        <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                        </svg>
                        Generated SQL Query
                      </h3>
                      <pre className="bg-slate-900 rounded-lg p-4 text-blue-300 font-mono text-sm overflow-x-auto border border-blue-700 border-opacity-30">
                        {response.sql_query}
                      </pre>
                    </div>
                  )}

                  {/* Chart */}
                  {response.chart && (
                    <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-6 border border-blue-700 border-opacity-30">
                      {renderChart()}
                    </div>
                  )}

                  {/* Data Table */}
                  {response.rows && response.rows.length > 0 && (
                    <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-6 border border-blue-700 border-opacity-30 overflow-hidden">
                      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v12m0 0l-4-4m4 4l4-4M3 15h18" />
                        </svg>
                        Query Results
                      </h3>
                      {renderTable()}
                    </div>
                  )}

                  {!response.rows || response.rows.length === 0 && (
                    <div className="bg-yellow-900 bg-opacity-20 border border-yellow-600 border-opacity-50 text-yellow-200 px-6 py-4 rounded-lg">
                      No results found for this query
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Dashboard;
