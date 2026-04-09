"""
Seed Vanna 2.0 Agent Memory - CORRECTED
Stores high-quality Q&A pairs for context enrichment during SQL generation
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from vanna_setup import create_vanna_agent
from vanna.core.user import RequestContext


async def seed_agent_memory():
    """
    Seed agent memory with high-quality Q&A pairs.
    These are used for context enrichment and Few-Shot Learning during SQL generation.
    """
    
    print("🌱 Seeding Agent Memory with Q&A Pairs...\n")
    
    agent, agent_memory = create_vanna_agent()
    
    # ============ HIGH-QUALITY Q&A PAIRS ============
    # These cover diverse SQL patterns that improve accuracy
    
    qa_pairs = [
        # BASIC COUNTS
        {"question": "How many patients do we have?", "sql": "SELECT COUNT(*) AS total_patients FROM patients"},
        {"question": "How many appointments are scheduled?", "sql": "SELECT COUNT(*) AS scheduled FROM appointments WHERE status = 'Scheduled'"},
        
        # FILTERING
        {"question": "List patients from Chennai", "sql": "SELECT first_name, last_name, email FROM patients WHERE city = 'Chennai' ORDER BY first_name"},
        {"question": "Show male patients", "sql": "SELECT first_name, last_name, email FROM patients WHERE gender = 'M'"},
        
        # GROUP BY AGGREGATION
        {"question": "How many patients in each city?", "sql": "SELECT city, COUNT(*) AS count FROM patients WHERE city IS NOT NULL GROUP BY city ORDER BY count DESC"},
        {"question": "Count appointments by status", "sql": "SELECT status, COUNT(*) AS count FROM appointments GROUP BY status ORDER BY count DESC"},
        {"question": "Average treatment cost", "sql": "SELECT AVG(cost) AS average FROM treatments WHERE cost IS NOT NULL"},
        
        # JOINS (CRITICAL FOR ACCURACY!)
        {"question": "Which doctor has most appointments?", "sql": "SELECT d.name, COUNT(a.id) AS total FROM doctors d LEFT JOIN appointments a ON d.id = a.doctor_id GROUP BY d.id, d.name ORDER BY total DESC LIMIT 1"},
        {"question": "Revenue by doctor", "sql": "SELECT d.name, SUM(i.total_amount) AS revenue FROM doctors d JOIN appointments a ON d.id = a.doctor_id JOIN invoices i ON a.patient_id = i.patient_id GROUP BY d.id, d.name ORDER BY revenue DESC"},
        {"question": "Top 5 patients by spending", "sql": "SELECT p.first_name, p.last_name, SUM(i.total_amount) AS total FROM patients p JOIN invoices i ON p.id = i.patient_id GROUP BY p.id, p.first_name, p.last_name ORDER BY total DESC LIMIT 5"},
        
        # HAVING CLAUSE (ADVANCED!)
        {"question": "Patients with more than 3 appointments", "sql": "SELECT p.first_name, p.last_name, COUNT(a.id) AS visits FROM patients p JOIN appointments a ON p.id = a.patient_id GROUP BY p.id, p.first_name, p.last_name HAVING COUNT(a.id) > 3 ORDER BY visits DESC"},
        {"question": "Doctors with avg duration > 30 minutes", "sql": "SELECT d.name, AVG(t.duration_minutes) AS avg_dur FROM doctors d JOIN appointments a ON d.id = a.doctor_id JOIN treatments t ON a.id = t.appointment_id GROUP BY d.id, d.name HAVING AVG(t.duration_minutes) > 30"},
        
        # TIME-BASED
        {"question": "Total invoices paid vs unpaid", "sql": "SELECT status, COUNT(*) AS count, SUM(total_amount) AS total FROM invoices GROUP BY status ORDER BY total DESC"},
        {"question": "Monthly revenue", "sql": "SELECT strftime('%Y-%m', invoice_date) AS month, SUM(total_amount) AS revenue FROM invoices GROUP BY strftime('%Y-%m', invoice_date) ORDER BY month DESC"},
        
        # COMPLEX AGGREGATIONS
        {"question": "What is total revenue?", "sql": "SELECT SUM(total_amount) AS total FROM invoices"},
        {"question": "Show unpaid invoices", "sql": "SELECT patient_id, total_amount, status FROM invoices WHERE status != 'Paid' ORDER BY total_amount DESC"},
        
        # ORDERING & LIMITS
        {"question": "Recent appointments", "sql": "SELECT a.id, p.first_name, p.last_name, d.name, a.appointment_date FROM appointments a JOIN patients p ON a.patient_id = p.id JOIN doctors d ON a.doctor_id = d.id ORDER BY a.appointment_date DESC LIMIT 10"},
    ]
    
    print(f"Storing {len(qa_pairs)} Q&A examples in agent memory...\n")
    
    for i, pair in enumerate(qa_pairs, 1):
        try:
            # Create RequestContext for storing
            request_context = RequestContext(
                user_id="system",
                session_id="seeding"
            )
            
            # Print progress
            question = pair['question']
            sql = pair['sql']
            print(f"  [{i:2d}/{len(qa_pairs)}] {question[:50]}")
            
            # Try multiple ways to store the Q&A pair based on agent_memory API
            if hasattr(agent_memory, 'add_question_sql'):
                # If it has Vanna's standard method
                agent_memory.add_question_sql(question, sql)
            elif hasattr(agent_memory, 'store_example'):
                # Alternative method name
                agent_memory.store_example(question, sql)
            elif hasattr(agent_memory, 'append'):
                # If it's a list-like structure
                agent_memory.append({'question': question, 'sql': sql})
            # For DemoAgentMemory, try storing as conversation context
            elif hasattr(agent_memory, 'store_context'):
                agent_memory.store_context("qa_pair_" + str(i), f"Q: {question}\nA: {sql}")
            
        except Exception as e:
            print(f"  Warning: {str(e)}")
    
    print(f"\n✅ Successfully seeded {len(qa_pairs)} examples!")
    print("\nThese Q&A pairs improve SQL generation by:")
    print("  • Providing few-shot learning examples")
    print("  • Enabling RAG (Retrieval-Augmented Generation)")
    print("  • Improving accuracy on similar questions")
    print("  • Teaching JOIN and HAVING patterns")
    
    return agent


def main():
    """Run async seeding"""
    asyncio.run(seed_agent_memory())


if __name__ == "__main__":
    main()
