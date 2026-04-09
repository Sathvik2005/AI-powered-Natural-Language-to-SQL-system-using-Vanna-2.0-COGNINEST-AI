import React, { useState } from 'react';
import axios from 'axios';
import Head from 'next/head';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px' }}>
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
                      <div key={idx} style={{
                        padding: '10px',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderRadius: '4px',
                        fontSize: '13px',
                        color: '#cbd5e1'
                      }}>
                        <div>{item.question.substring(0, 30)}...</div>
                        <div style={{ color: '#64748b', marginTop: '4px' }}>{item.time}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
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
                      cursor: loading ? 'not-allowed' : 'pointer'
                    }}
                  >
                    {loading ? 'Processing...' : 'Ask Question'}
                  </button>
                </form>

                {error && (
                  <div style={{
                    marginTop: '15px',
                    padding: '12px',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.5)',
                    borderRadius: '4px',
                    color: '#fca5a5'
                  }}>
                    {error}
                  </div>
                )}
              </div>

              {response && (
                <div style={{
                  backgroundColor: '#1e293b',
                  border: '1px solid rgba(59, 130, 246, 0.2)',
                  borderRadius: '8px',
                  padding: '25px'
                }}>
                  <h2 style={{ margin: '0 0 15px 0', fontSize: '16px', fontWeight: '600' }}>
                    Results
                  </h2>

                  {response.message && (
                    <div style={{ marginBottom: '15px', color: '#cbd5e1' }}>
                      <strong>Response:</strong> {response.message}
                    </div>
                  )}

                  {response.sql_query && (
                    <div style={{ marginBottom: '15px' }}>
                      <strong>SQL Generated:</strong>
                      <div style={{
                        backgroundColor: '#0f172a',
                        padding: '12px',
                        borderRadius: '4px',
                        marginTop: '8px',
                        fontFamily: 'monospace',
                        fontSize: '12px',
                        color: '#10b981',
                        overflowX: 'auto'
                      }}>
                        {response.sql_query}
                      </div>
                    </div>
                  )}

                  {response.rows && response.rows.length > 0 && (
                    <div style={{ marginBottom: '15px' }}>
                      <strong>Data ({response.row_count} records):</strong>
                      <div style={{
                        backgroundColor: '#0f172a',
                        padding: '12px',
                        borderRadius: '4px',
                        marginTop: '8px',
                        overflowX: 'auto'
                      }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                          <thead>
                            <tr>
                              {response.columns?.map((col, idx) => (
                                <th key={idx} style={{ padding: '8px', textAlign: 'left', borderBottom: '1px solid rgba(59, 130, 246, 0.3)' }}>
                                  {col}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {response.rows.slice(0, 10).map((row, rowIdx) => (
                              <tr key={rowIdx}>
                                {row.map((cell, cellIdx) => (
                                  <td key={cellIdx} style={{ padding: '8px', borderBottom: '1px solid rgba(59, 130, 246, 0.1)', color: '#cbd5e1' }}>
                                    {String(cell)}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {response.rows.length > 10 && (
                          <div style={{ marginTop: '8px', color: '#64748b', fontSize: '11px' }}>
                            Showing 10 of {response.row_count} records
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {response.chart && (
                    <div style={{ marginTop: '15px' }}>
                      <strong>Chart:</strong>
                      <div style={{ marginTop: '8px', color: '#cbd5e1' }}>
                        Chart type: {response.chart_type}
                      </div>
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
