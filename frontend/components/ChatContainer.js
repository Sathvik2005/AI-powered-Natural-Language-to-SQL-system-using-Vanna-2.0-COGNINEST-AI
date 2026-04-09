import React, { useState } from 'react';
import styles from '../styles/chat.module.css';

export default function ChatContainer({ onSubmit }) {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!question.trim()) return;

    setLoading(true);
    try {
      await onSubmit(question);
      setQuestion('');
    } finally {
      setLoading(false);
    }
  };

  const exampleQuestions = [
    'How many patients do we have?',
    'Top 5 patients by spending',
    'Revenue by doctor',
    'Appointments last month',
    'Which doctor has the most appointments?',
  ];

  return (
    <div className={styles.chatContainer}>
      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.inputGroup}>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask your database a question..."
            disabled={loading}
            className={styles.input}
            maxLength={500}
          />
          <button 
            type="submit" 
            disabled={loading || !question.trim()} 
            className={styles.submitBtn}
          >
            {loading ? '⏳ Querying...' : '🔍 Search'}
          </button>
        </div>
      </form>

      <div className={styles.examples}>
        <p>📝 Try these questions:</p>
        <div className={styles.exampleList}>
          {exampleQuestions.map((q, idx) => (
            <button
              key={idx}
              onClick={() => setQuestion(q)}
              className={styles.exampleBtn}
              disabled={loading}
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
