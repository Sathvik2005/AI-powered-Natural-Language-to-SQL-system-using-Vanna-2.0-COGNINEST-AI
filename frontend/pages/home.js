import React, { useState } from 'react';
import axios from 'axios';
import Head from 'next/head';

const API_URL = 'http://localhost:8001';

export default function Home() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);

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
      const res = await axios.post(`${API_URL}/chat`, {
        question: question.trim(),
      });

      if (res.status === 200) {
        setResponse(res.data);
        setHistory([
          { question: question.trim(), time: new Date().toLocaleTimeString() },
          ...history.slice(0, 4),
        ]);
        setQuestion('');
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error querying API');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>NL2SQL Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div style={{ minHeight: '100vh', backgroundColor: '#0f172a', color: '#e5e7eb', padding: '20px' }}>
        {/* Header */}
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ 
            borderBottom: '1px solid rgba(59, 130, 246, 0.3)', 
            paddingBottom: '20px', 
            marginBottom: '30px' 
          }}>
            <h1 style={{ margin: 0, fontSize: '32px', fontWeight: 'bold', color: '#fff' }}>
              NL2SQL Analytics
            </h1>
            <p style={{ margin: '5px 0 0 0', color: '#9ca3af' }}>
              Ask questions about your database in plain English
            </p>
          </div>

          {/* Main Layout */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px' }}>
            {/* Sidebar */}
            <div>
              <div style={{
                backgroundColor: '#1e293b',
                border: '1px solid rgba(59, 130, 246, 0.2)',
                borderRadius: '8px',
                padding: '20px'
              }}>
                <h2 style={{ margin: '0 0 15px 0', fontSize: '16px', fontWeight: '600' }}>
                  Recent Queries
                </h2>
                {history.length === 0 ? (
                  <p style={{ color: '#6b7280', margin: 0 }}>No queries yet</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {history.map((item, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: '10px',
                          backgroundColor: 'rgba(59, 130, 246, 0.1)',
                          borderRadius: '4px',
                          fontSize: '13px',
                          color: '#cbd5e1'
                        }}
                      >
                        <div>{item.question.substring(0, 30)}...</div>
                        <div style={{ color: '#64748b', marginTop: '4px' }}>{item.time}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Main Panel */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Query Input */}
              <div style={{
                backgroundColor: '#1e293b',
                border: '1px solid rgba(59, 130, 246, 0.2)',
                borderRadius: '8px',
                padding: '25px'
              }}>
                <form onSubmit={handleSubmit}>
                  <label style={{ display: 'block', marginBottom: '10px', fontSize: '14px', fontWeight: '500' }}>
                    Ask a Question
                  </label>
                  <textarea
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="e.g., How many patients do we have? Show revenue by doctor..."
                    rows={4}
                    style={{
                      width: '100%',
                      padding: '12px',
                      backgroundColor: '#0f172a',
                      border: '1px solid rgba(59, 130, 246, 0.5)',
                      borderRadius: '4px',
                      color: '#e5e7eb',
                      fontFamily: 'inherit',
                      fontSize: '14px',
                      boxSizing: 'border-box',
                      marginBottom: '15px'
                    }}
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    style={{
                      width: '100%',
                      padding: '12px',
                      backgroundColor: loading ? '#1e40af' : '#2563eb',
                      color: '#fff',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '14px',
                      fontWeight: '500',
                      cursor: loading ? 'not-allowed' : 'pointer',
                      opacity: loading ? 0.7 : 1
                    }}
                  >
                    {loading ? 'Processing...' : 'Execute Query'}
                  </button>
                </form>
              </div>

              {/* Error Message */}
              {error && (
                <div style={{
                  backgroundColor: 'rgba(220, 38, 38, 0.2)',
                  border: '1px solid rgba(220, 38, 38, 0.5)',
                  color: '#fca5a5',
                  padding: '15px',
                  borderRadius: '4px'
                }}>
                  Error: {error}
                </div>
              )}

              {/* Results */}
              {response && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  {/* Stats Cards */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px' }}>
                    <div style={{
                      backgroundColor: 'rgba(59, 130, 246, 0.1)',
                      border: '1px solid rgba(59, 130, 246, 0.3)',
                      borderRadius: '8px',
                      padding: '15px'
                    }}>
                      <div style={{ fontSize: '12px', color: '#9ca3af' }}>Records Found</div>
                      <div style={{ fontSize: '28px', fontWeight: 'bold', marginTop: '8px' }}>
                        {response.row_count || 0}
                      </div>
                    </div>
                    <div style={{
                      backgroundColor: 'rgba(147, 51, 234, 0.1)',
                      border: '1px solid rgba(147, 51, 234, 0.3)',
                      borderRadius: '8px',
                      padding: '15px'
                    }}>
                      <div style={{ fontSize: '12px', color: '#9ca3af' }}>Columns</div>
                      <div style={{ fontSize: '28px', fontWeight: 'bold', marginTop: '8px' }}>
                        {response.columns?.length || 0}
                      </div>
                    </div>
                    <div style={{
                      backgroundColor: 'rgba(34, 197, 94, 0.1)',
                      border: '1px solid rgba(34, 197, 94, 0.3)',
                      borderRadius: '8px',
                      padding: '15px'
                    }}>
                      <div style={{ fontSize: '12px', color: '#9ca3af' }}>Status</div>
                      <div style={{ fontSize: '14px', fontWeight: 'bold', marginTop: '8px', color: '#86efac' }}>
                        Success
                      </div>
                    </div>
                  </div>

                  {/* SQL Query */}
                  {response.sql_query && (
                    <div style={{
                      backgroundColor: '#1e293b',
                      border: '1px solid rgba(59, 130, 246, 0.2)',
                      borderRadius: '8px',
                      padding: '15px'
                    }}>
                      <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: '600' }}>
                        Generated SQL
                      </h3>
                      <pre style={{
                        margin: 0,
                        backgroundColor: '#0f172a',
                        padding: '12px',
                        borderRadius: '4px',
                        overflow: 'auto',
                        color: '#60a5fa',
                        fontSize: '12px',
                        fontFamily: 'monospace'
                      }}>
                        {response.sql_query}
                      </pre>
                    </div>
                  )}

                  {/* Results Table */}
                  {response.rows && response.rows.length > 0 ? (
                    <div style={{
                      backgroundColor: '#1e293b',
                      border: '1px solid rgba(59, 130, 246, 0.2)',
                      borderRadius: '8px',
                      overflow: 'hidden'
                    }}>
                      <h3 style={{ margin: '0', padding: '15px', paddingBottom: '10px', fontSize: '14px', fontWeight: '600', borderBottom: '1px solid rgba(59, 130, 246, 0.2)' }}>
                        Results ({response.rows.length} rows)
                      </h3>
                      <div style={{ overflowX: 'auto' }}>
                        <table style={{
                          width: '100%',
                          borderCollapse: 'collapse',
                          fontSize: '13px'
                        }}>
                          <thead>
                            <tr style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)', borderBottom: '1px solid rgba(59, 130, 246, 0.2)' }}>
                              {response.columns?.map((col, idx) => (
                                <th
                                  key={idx}
                                  style={{
                                    padding: '12px 15px',
                                    textAlign: 'left',
                                    fontWeight: '600',
                                    color: '#93c5fd'
                                  }}
                                >
                                  {col}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {response.rows.slice(0, 100).map((row, rowIdx) => (
                              <tr
                                key={rowIdx}
                                style={{
                                  borderBottom: '1px solid rgba(59, 130, 246, 0.1)',
                                  backgroundColor: rowIdx % 2 === 0 ? 'transparent' : 'rgba(59, 130, 246, 0.05)'
                                }}
                              >
                                {Array.isArray(row) ? (
                                  row.map((cell, cellIdx) => (
                                    <td
                                      key={cellIdx}
                                      style={{
                                        padding: '10px 15px',
                                        color: '#cbd5e1'
                                      }}
                                    >
                                      {cell !== null && cell !== undefined ? String(cell) : 'NULL'}
                                    </td>
                                  ))
                                ) : (
                                  Object.values(row).map((cell, cellIdx) => (
                                    <td
                                      key={cellIdx}
                                      style={{
                                        padding: '10px 15px',
                                        color: '#cbd5e1'
                                      }}
                                    >
                                      {cell !== null && cell !== undefined ? String(cell) : 'NULL'}
                                    </td>
                                  ))
                                )}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      {response.rows.length > 100 && (
                        <div style={{
                          padding: '12px 15px',
                          borderTop: '1px solid rgba(59, 130, 246, 0.2)',
                          backgroundColor: 'rgba(59, 130, 246, 0.05)',
                          color: '#9ca3af',
                          fontSize: '12px'
                        }}>
                          Showing 100 of {response.rows.length} rows
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{
                      backgroundColor: 'rgba(180, 83, 9, 0.1)',
                      border: '1px solid rgba(180, 83, 9, 0.5)',
                      color: '#fcd34d',
                      padding: '15px',
                      borderRadius: '4px'
                    }}>
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
}
