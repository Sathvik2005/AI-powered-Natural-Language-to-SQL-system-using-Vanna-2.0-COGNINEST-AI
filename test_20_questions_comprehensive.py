#!/usr/bin/env python
"""
Test suite for NL2SQL system - 20 comprehensive questions
Tests all major SQL operations: SELECT, aggregation, JOIN, GROUP BY, etc.
"""

import requests
import json
from datetime import datetime
import time

API_URL = "http://localhost:8000"

# Test questions with expected behaviors
TEST_QUESTIONS = [
    {
        "id": 1,
        "question": "How many patients do we have?",
        "expected": "COUNT of patients",
        "sql_pattern": "SELECT.*COUNT"
    },
    {
        "id": 2,
        "question": "List all doctors and their specializations",
        "expected": "Doctor names and specializations",
        "sql_pattern": "SELECT.*FROM.*doctors"
    },
    {
        "id": 3,
        "question": "Show me appointments for last month",
        "expected": "Appointments filtered by date",
        "sql_pattern": "SELECT.*WHERE.*appointment_date"
    },
    {
        "id": 4,
        "question": "Which doctor has the most appointments?",
        "expected": "Doctor with highest appointment count",
        "sql_pattern": "GROUP BY.*ORDER BY.*DESC"
    },
    {
        "id": 5,
        "question": "What is the total revenue?",
        "expected": "SUM of all invoice amounts",
        "sql_pattern": "SELECT.*SUM"
    },
    {
        "id": 6,
        "question": "Show revenue by doctor",
        "expected": "Revenue aggregated by doctor",
        "sql_pattern": "JOIN.*GROUP BY"
    },
    {
        "id": 7,
        "question": "How many cancelled appointments last quarter?",
        "expected": "Count of cancelled appointments",
        "sql_pattern": "WHERE.*cancelled"
    },
    {
        "id": 8,
        "question": "Top 5 patients by spending",
        "expected": "Top 5 patients ordered by spending",
        "sql_pattern": "ORDER BY.*LIMIT.*5"
    },
    {
        "id": 9,
        "question": "Average treatment cost by specialization",
        "expected": "AVG cost grouped by specialization",
        "sql_pattern": "AVG.*GROUP BY"
    },
    {
        "id": 10,
        "question": "Show monthly appointment count for the past 6 months",
        "expected": "Appointments grouped by month",
        "sql_pattern": "GROUP BY.*DATE"
    },
    {
        "id": 11,
        "question": "Which city has the most patients?",
        "expected": "City with highest patient count",
        "sql_pattern": "GROUP BY.*city"
    },
    {
        "id": 12,
        "question": "List patients who visited more than 3 times",
        "expected": "Patients with HAVING clause filtering",
        "sql_pattern": "HAVING"
    },
    {
        "id": 13,
        "question": "Show unpaid invoices",
        "expected": "Unpaid invoice list",
        "sql_pattern": "WHERE.*status"
    },
    {
        "id": 14,
        "question": "What percentage of appointments are no-shows?",
        "expected": "Percentage calculation",
        "sql_pattern": "SELECT.*.*100"
    },
    {
        "id": 15,
        "question": "Show the busiest day of the week for appointments",
        "expected": "Day with most appointments",
        "sql_pattern": "ORDER BY.*DESC.*LIMIT.*1"
    },
    {
        "id": 16,
        "question": "Revenue trend by month",
        "expected": "Monthly revenue progression",
        "sql_pattern": "DATE.*GROUP BY"
    },
    {
        "id": 17,
        "question": "Average appointment duration by doctor",
        "expected": "AVG duration per doctor",
        "sql_pattern": "AVG.*doctors"
    },
    {
        "id": 18,
        "question": "List patients with overdue invoices",
        "expected": "Overdue invoice patients",
        "sql_pattern": "JOIN.*WHERE"
    },
    {
        "id": 19,
        "question": "Compare revenue between departments",
        "expected": "Revenue by department",
        "sql_pattern": "GROUP BY.*department"
    },
    {
        "id": 20,
        "question": "Show patient registration trend by month",
        "expected": "Registration counts by month",
        "sql_pattern": "registered_date.*GROUP BY"
    }
]


def test_question(q):
    """Test a single question"""
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{API_URL}/chat",
            json={"question": q["question"]},
            timeout=30
        )
        
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for success
            has_error = bool(data.get("error"))
            has_sql = bool(data.get("sql_query"))
            has_rows = bool(data.get("rows"))
            row_count = data.get("row_count", 0)
            
            status = "✓ PASS" if (has_sql and not has_error) else "✗ FAIL"
            
            return {
                "id": q["id"],
                "question": q["question"],
                "status": status,
                "sql_query": data.get("sql_query", ""),
                "error": data.get("error"),
                "row_count": row_count,
                "message": data.get("message", ""),
                "response_time": f"{elapsed_time:.2f}s"
            }
        else:
            return {
                "id": q["id"],
                "question": q["question"],
                "status": "✗ FAIL",
                "error": f"HTTP {response.status_code}",
                "response_time": f"{elapsed_time:.2f}s"
            }
    except Exception as e:
        return {
            "id": q["id"],
            "question": q["question"],
            "status": "✗ ERROR",
            "error": str(e)
        }


def check_health():
    """Check if backend is healthy"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Backend is healthy")
            print(f"  Status: {data['status']}")
            print(f"  Database: {data['database']}")
            print(f"  Agent Ready: {data['agent_ready']}")
            print()
            return True
        else:
            print(f"✗ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to backend: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("=" * 80)
    print("NL2SQL SYSTEM - COMPREHENSIVE TEST SUITE (20 Questions)")
    print("=" * 80)
    print()
    
    # Check backend
    if not check_health():
        print("Backend is not responding. Start the server with:")
        print("  uvicorn main:app --port 8001")
        return
    
    print("Starting tests...")
    print()
    
    results = []
    passed = 0
    failed = 0
    
    # Run all tests
    for i, q in enumerate(TEST_QUESTIONS, 1):
        print(f"[{i}/20] Testing Q{q['id']}: {q['question'][:50]}...", end=" ", flush=True)
        
        result = test_question(q)
        results.append(result)
        
        if "PASS" in result["status"]:
            passed += 1
            print(f"✓ {result['response_time']}")
        else:
            failed += 1
            print(f"✗ {result['status']}")
        
        time.sleep(0.5)  # Rate limiting: don't hammer the server
    
    print()
    print("=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    print()
    
    # Print summary
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed} ({passed*100//len(results)}%)")
    print(f"Failed: {failed} ({failed*100//len(results)}%)")
    print()
    
    # Print detailed results
    print("=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)
    print()
    
    for result in results:
        print(f"Q{result['id']}: {result['status']}")
        print(f"  Question: {result['question']}")
        
        if result['status'] == '✓ PASS':
            print(f"  SQL Generated: {result['sql_query'][:100]}")
            print(f"  Rows Returned: {result['row_count']}")
            print(f"  Message: {result['message']}")
            print(f"  Response Time: {result['response_time']}")
        else:
            print(f"  Error: {result.get('error', 'Unknown error')}")
            if result.get('response_time'):
                print(f"  Response Time: {result['response_time']}")
        
        print()
    
    # Save results to file
    save_results(results, passed, failed)


def save_results(results, passed, failed):
    """Save test results to file"""
    output = []
    output.append("=" * 80)
    output.append("NL2SQL SYSTEM - TEST RESULTS")
    output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("=" * 80)
    output.append("")
    
    output.append("SUMMARY")
    output.append("-" * 80)
    output.append(f"Total Tests: {len(results)}")
    output.append(f"Passed: {passed} ({passed*100//len(results)}%)")
    output.append(f"Failed: {failed} ({failed*100//len(results)}%)")
    output.append("")
    
    output.append("DETAILED RESULTS")
    output.append("-" * 80)
    output.append("")
    
    for result in results:
        output.append(f"Q{result['id']}: {result['status']}")
        output.append(f"  Question: {result['question']}")
        
        if result['status'] == '✓ PASS':
            output.append(f"  SQL: {result['sql_query']}")
            output.append(f"  Rows: {result['row_count']}")
            output.append(f"  Message: {result['message']}")
            output.append(f"  Time: {result['response_time']}")
        else:
            output.append(f"  Error: {result.get('error', 'Unknown')}")
        
        output.append("")
    
    # Write to file
    with open("TEST_RESULTS_20_QUESTIONS.txt", "w") as f:
        f.write("\n".join(output))
    
    print(f"✓ Results saved to TEST_RESULTS_20_QUESTIONS.txt")


if __name__ == "__main__":
    main()
