import React, { useState } from 'react';
import Chart from './Chart';
import styles from '../styles/results.module.css';

export default function ResultsPanel({ responses }) {
  const [expandedIdx, setExpandedIdx] = useState(0);

  if (responses.length === 0) {
    return (
      <div className={styles.empty}>
        <h2>👋 No queries yet</h2>
        <p>Ask a question to see results here</p>
      </div>
    );
  }

  return (
    <div className={styles.resultsContainer}>
      <h2>📊 Results</h2>
      
      {responses.map((item, idx) => (
        <div key={idx} className={styles.resultCard}>
          <div 
            className={styles.header}
            onClick={() => setExpandedIdx(expandedIdx === idx ? -1 : idx)}
          >
            <div className={styles.question}>
              <strong>Q:</strong> {item.question}
            </div>
            <span className={styles.toggle}>
              {expandedIdx === idx ? '▼' : '▶'}
            </span>
          </div>

          {expandedIdx === idx && (
            <div className={styles.content}>
              {item.response.error ? (
                <div className={styles.error}>
                  <p><strong>❌ Error:</strong> {item.response.error}</p>
                </div>
              ) : (
                <>
                  <div className={styles.message}>
                    <strong>📌 Summary:</strong> {item.response.message}
                  </div>

                  {item.response.sql_query && (
                    <div className={styles.sqlBox}>
                      <strong>SQL Generated:</strong>
                      <pre>{item.response.sql_query}</pre>
                    </div>
                  )}

                  {item.response.chart && (
                    <div className={styles.chartContainer}>
                      <strong>📈 Visualization:</strong>
                      <Chart chartData={item.response.chart} />
                    </div>
                  )}

                  {item.response.rows && item.response.rows.length > 0 && (
                    <div className={styles.table}>
                      <strong>📋 Data:</strong>
                      <div className={styles.tableWrapper}>
                        <table className={styles.dataTable}>
                          <thead className={styles.tableHead}>
                            <tr>
                              {item.response.columns?.map((col) => (
                                <th key={col} className={styles.tableHeader}>{col}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {item.response.rows.map((row, rIdx) => (
                              <tr key={rIdx} className={styles.tableRow}>
                                {row.map((cell, cIdx) => (
                                  <td key={cIdx} className={styles.tableCell}>
                                    {typeof cell === 'object' 
                                      ? JSON.stringify(cell) 
                                      : String(cell)}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  <div className={styles.meta}>
                    <small>
                      Rows: {item.response.row_count || 0} | 
                      Time: {item.timestamp.toLocaleTimeString()}
                    </small>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
