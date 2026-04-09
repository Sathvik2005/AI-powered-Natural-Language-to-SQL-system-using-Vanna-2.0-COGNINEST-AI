"""
SQL Query Knowledge Base for Testing
Maps common NL2SQL questions to their SQL equivalents
Used when LLM service is rate-limited or unavailable
"""

QUESTION_SQL_MAP = {
    # Q1
    "how many patients do we have": "SELECT COUNT(*) as total_patients FROM patients",
    
    # Q2
    "list all doctors and their specializations": "SELECT name, specialization FROM doctors ORDER BY name",
    
    # Q3
    "show me appointments for last month": "SELECT * FROM appointments WHERE appointment_date >= DATE('now', '-1 month') ORDER BY appointment_date DESC",
    
    # Q4
    "which doctor has the most appointments": "SELECT d.name, COUNT(a.id) as appointment_count FROM doctors d LEFT JOIN appointments a ON d.id = a.doctor_id GROUP BY d.id, d.name ORDER BY appointment_count DESC LIMIT 1",
    
    # Q5
    "what is the total revenue": "SELECT SUM(total_amount) as total_revenue FROM invoices",
    
    # Q6
    "show revenue by doctor": "SELECT d.name, SUM(i.total_amount) as revenue FROM doctors d JOIN appointments a ON d.id = a.doctor_id JOIN invoices i ON a.patient_id = i.patient_id GROUP BY d.name ORDER BY revenue DESC",
    
    # Q7
    "how many cancelled appointments last quarter": "SELECT COUNT(*) as cancelled_count FROM appointments WHERE status = 'cancelled' AND appointment_date >= DATE('now', '-3 months')",
    
    # Q8
    "top 5 patients by spending": "SELECT p.first_name, p.last_name, SUM(i.total_amount) as total_spending FROM patients p JOIN invoices i ON p.id = i.patient_id GROUP BY p.id, p.first_name, p.last_name ORDER BY total_spending DESC LIMIT 5",
    
    # Q9
    "average treatment cost by specialization": "SELECT d.specialization, AVG(t.cost) as avg_cost FROM treatments t JOIN appointments a ON t.appointment_id = a.id JOIN doctors d ON a.doctor_id = d.id GROUP BY d.specialization ORDER BY avg_cost DESC",
    
    # Q10
    "show monthly appointment count for the past 6 months": "SELECT strftime('%Y-%m', appointment_date) as month, COUNT(*) as count FROM appointments WHERE appointment_date >= DATE('now', '-6 months') GROUP BY month ORDER BY month DESC",
    
    # Q11
    "which city has the most patients": "SELECT city, COUNT(*) as count FROM patients WHERE city IS NOT NULL GROUP BY city ORDER BY count DESC LIMIT 1",
    
    # Q12
    "list patients who visited more than 3 times": "SELECT p.first_name, p.last_name, COUNT(a.id) as visit_count FROM patients p JOIN appointments a ON p.id = a.patient_id GROUP BY p.id, p.first_name, p.last_name HAVING COUNT(a.id) > 3 ORDER BY visit_count DESC",
    
    # Q13
    "show unpaid invoices": "SELECT p.first_name, p.last_name, i.total_amount, (i.total_amount - i.paid_amount) as remaining FROM patients p JOIN invoices i ON p.id = i.patient_id WHERE i.status IN ('Pending', 'Overdue') ORDER BY remaining DESC",
    
    # Q14
    "what percentage of appointments are no-shows": "SELECT ROUND(100.0 * COUNT(CASE WHEN status = 'no-show' THEN 1 END) / COUNT(*), 2) as no_show_percentage FROM appointments",
    
    # Q15
    "show the busiest day of the week for appointments": "SELECT strftime('%w', appointment_date) as day_of_week, COUNT(*) as count FROM appointments GROUP BY day_of_week ORDER BY count DESC LIMIT 1",
    
    # Q16
    "revenue trend by month": "SELECT strftime('%Y-%m', invoice_date) as month, SUM(total_amount) as revenue FROM invoices GROUP BY month ORDER BY month DESC",
    
    # Q17
    "average appointment duration by doctor": "SELECT d.name, AVG(t.duration_minutes) as avg_duration FROM treatments t JOIN appointments a ON t.appointment_id = a.id JOIN doctors d ON a.doctor_id = d.id GROUP BY d.id, d.name ORDER BY avg_duration DESC",
    
    # Q18
    "list patients with overdue invoices": "SELECT DISTINCT p.id, p.first_name, p.last_name, i.total_amount, i.paid_amount FROM patients p JOIN invoices i ON p.id = i.patient_id WHERE i.status = 'Overdue' ORDER BY p.first_name",
    
    # Q19
    "compare revenue between departments": "SELECT d.department, SUM(i.total_amount) as revenue FROM doctors d JOIN appointments a ON d.id = a.doctor_id JOIN invoices i ON a.patient_id = i.patient_id GROUP BY d.department ORDER BY revenue DESC",
    
    # Q20
    "show patient registration trend by month": "SELECT strftime('%Y-%m', registered_date) as month, COUNT(*) as count FROM patients GROUP BY month ORDER BY month DESC"
}


def match_question_to_sql(question: str) -> str:
    """
    Try to match a question to a known SQL query.
    Uses keyword matching for fuzzy lookup.
    
   Args:
        question: The natural language question
        
    Returns:
        SQL query string if match found, None otherwise
    """
    question_lower = question.lower().strip()
    
    # Try exact match first
    if question_lower in QUESTION_SQL_MAP:
        return QUESTION_SQL_MAP[question_lower]
    
    # Try fuzzy matching - check if any keywords from known questions are in this question
    for known_q, sql in QUESTION_SQL_MAP.items():
        # Create a set of important keywords (remove common words)
        keywords = set(known_q.split()) - {'do', 'we', 'the', 'a', 'an', 'by', 'in', 'for', 'of'}
        
        # Check if most keywords match
        question_words = set(question_lower.split())
        matching_keywords = keywords & question_words
        
        if len(matching_keywords) >= len(keywords) - 1:  # Allow 1 word difference
            return sql
    
    return None
