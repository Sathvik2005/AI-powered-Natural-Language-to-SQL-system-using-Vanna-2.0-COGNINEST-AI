import React, { useState, useEffect } from 'react';
import styles from '../styles/stats.module.css';

const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function StatsPanel() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch(`${apiUrl}/cache-stats`);
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (err) {
        console.log('Could not fetch cache stats (not critical)');
      } finally {
        setLoading(false);
      }
    };

    // Fetch stats immediately
    fetchStats();

    // Refresh stats every 10 seconds
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  if (!stats) {
    return null;
  }

  return (
    <div className={styles.statsPanel}>
      <h3>⚡ System Stats</h3>
      <div className={styles.statsGrid}>
        <div className={styles.statItem}>
          <small>Cache Size</small>
          <strong>{stats.size}/{stats.max_size}</strong>
        </div>
        <div className={styles.statItem}>
          <small>Cache Hits</small>
          <strong>{stats.hits}</strong>
        </div>
        <div className={styles.statItem}>
          <small>Cache Misses</small>
          <strong>{stats.misses}</strong>
        </div>
        <div className={styles.statItem}>
          <small>Hit Rate</small>
          <strong>{stats.hit_rate}</strong>
        </div>
      </div>
    </div>
  );
}
