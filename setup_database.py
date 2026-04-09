"""
Setup SQLite Database for Clinic Management System
Creates schema and inserts realistic dummy data
"""

import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker

# Initialize Faker
fake = Faker()
random.seed(42)  # For reproducibility
Faker.seed(42)

DB_PATH = "clinic.db"

def create_schema(conn):
    """Create all tables in the database"""
    cursor = conn.cursor()
    
    # Create patients table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        date_of_birth DATE,
        gender TEXT,
        city TEXT,
        registered_date DATE
    )
    """)
    
    # Create doctors table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialization TEXT,
        department TEXT,
        phone TEXT
    )
    """)
    
    # Create appointments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        appointment_date DATETIME,
        status TEXT,
        notes TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    )
    """)
    
    # Create treatments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS treatments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER NOT NULL,
        treatment_name TEXT,
        cost REAL,
        duration_minutes INTEGER,
        FOREIGN KEY (appointment_id) REFERENCES appointments(id)
    )
    """)
    
    # Create invoices table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        invoice_date DATE,
        total_amount REAL,
        paid_amount REAL,
        status TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )
    """)
    
    conn.commit()
    print("✅ Schema created successfully")


def insert_doctors(conn):
    """Insert 15 doctors across 5 specializations"""
    cursor = conn.cursor()
    
    specializations = [
        ("Dermatology", "Skin & Dermatology"),
        ("Cardiology", "Heart & Cardiovascular"),
        ("Orthopedics", "Bones & Joints"),
        ("General Medicine", "General"),
        ("Pediatrics", "Children")
    ]
    
    doctors = []
    doctor_id = 1
    
    for _ in range(3):  # 3 doctors per specialization = 15 total
        for spec, dept in specializations:
            doctor_name = fake.name()
            phone = fake.phone_number()[:10]
            
            cursor.execute("""
                INSERT INTO doctors (name, specialization, department, phone)
                VALUES (?, ?, ?, ?)
            """, (doctor_name, spec, dept, phone))
            
            doctors.append((doctor_id, doctor_name, spec))
            doctor_id += 1
    
    conn.commit()
    print(f"✅ Inserted {doctor_id - 1} doctors")
    return doctors


def insert_patients(conn):
    """Insert 200 patients from 8-10 cities"""
    cursor = conn.cursor()
    
    cities = ["Chennai", "Bangalore", "Mumbai", "Delhi", "Hyderabad", 
              "Pune", "Kolkata", "Ahmedabad"]
    
    patients = []
    start_date = datetime.now() - timedelta(days=365)
    
    for i in range(200):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = fake.email() if random.random() > 0.3 else None
        phone = fake.phone_number()[:10] if random.random() > 0.2 else None
        date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=80)
        gender = random.choice(['M', 'F'])
        city = random.choice(cities)
        registered_date = start_date + timedelta(days=random.randint(0, 365))
        
        cursor.execute("""
            INSERT INTO patients (first_name, last_name, email, phone, 
                                 date_of_birth, gender, city, registered_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, email, phone, date_of_birth, gender, city, registered_date))
        
        patients.append((i + 1, first_name, last_name, city))
    
    conn.commit()
    print(f"✅ Inserted {len(patients)} patients")
    return patients


def insert_appointments(conn, num_patients, num_doctors):
    """Insert 500 appointments with varied statuses"""
    cursor = conn.cursor()
    
    statuses = ["Scheduled", "Completed", "Cancelled", "No-Show"]
    appointments = []
    start_date = datetime.now() - timedelta(days=365)
    
    for i in range(500):
        patient_id = random.randint(1, num_patients)
        doctor_id = random.randint(1, num_doctors)
        
        # Spread appointments across 12 months
        appointment_date = start_date + timedelta(
            days=random.randint(0, 365),
            hours=random.randint(8, 17)
        )
        
        status = random.choice(statuses)
        notes = fake.sentence() if random.random() > 0.5 else None
        
        cursor.execute("""
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (patient_id, doctor_id, appointment_date, status, notes))
        
        appointments.append((i + 1, patient_id, doctor_id, status))
    
    conn.commit()
    print(f"✅ Inserted {len(appointments)} appointments")
    return appointments


def insert_treatments(conn, num_appointments):
    """Insert 350 treatments linked to completed appointments"""
    cursor = conn.cursor()
    
    treatments_data = [
        "Consultation", "Medication", "Surgery", "Physical Therapy",
        "Injection", "Prescription", "Follow-up", "Lab Test",
        "Vaccination", "Wound Care"
    ]
    
    # Get completed appointments
    cursor.execute("SELECT id FROM appointments WHERE status='Completed' LIMIT 350")
    completed_appointments = [row[0] for row in cursor.fetchall()]
    
    treatments = []
    
    for i, appointment_id in enumerate(completed_appointments):
        treatment_name = random.choice(treatments_data)
        cost = round(random.uniform(50, 5000), 2)
        duration_minutes = random.randint(15, 120)
        
        cursor.execute("""
            INSERT INTO treatments (appointment_id, treatment_name, cost, duration_minutes)
            VALUES (?, ?, ?, ?)
        """, (appointment_id, treatment_name, cost, duration_minutes))
        
        treatments.append((i + 1, appointment_id, treatment_name, cost))
    
    conn.commit()
    print(f"✅ Inserted {len(treatments)} treatments")
    return treatments


def insert_invoices(conn, num_patients):
    """Insert 300 invoices with mixed statuses"""
    cursor = conn.cursor()
    
    statuses = ["Paid", "Pending", "Overdue"]
    invoices = []
    start_date = datetime.now() - timedelta(days=365)
    
    for i in range(300):
        patient_id = random.randint(1, num_patients)
        invoice_date = start_date + timedelta(days=random.randint(0, 365))
        total_amount = round(random.uniform(500, 10000), 2)
        
        # Some invoices partially paid
        if random.random() > 0.3:
            paid_amount = round(random.uniform(0, total_amount), 2)
        else:
            paid_amount = total_amount if random.random() > 0.5 else 0
        
        status = random.choice(statuses)
        
        cursor.execute("""
            INSERT INTO invoices (patient_id, invoice_date, total_amount, paid_amount, status)
            VALUES (?, ?, ?, ?, ?)
        """, (patient_id, invoice_date, total_amount, paid_amount, status))
        
        invoices.append((i + 1, patient_id, total_amount, status))
    
    conn.commit()
    print(f"✅ Inserted {len(invoices)} invoices")
    return invoices


def main():
    """Main function to setup database"""
    print("🚀 Starting database setup...\n")
    
    # Create or connect to database
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Create schema
        create_schema(conn)
        
        # Insert data
        doctors = insert_doctors(conn)
        patients = insert_patients(conn)
        appointments = insert_appointments(conn, len(patients), len(doctors))
        treatments = insert_treatments(conn, len(appointments))
        invoices = insert_invoices(conn, len(patients))
        
        # Print summary
        print("\n" + "="*50)
        print("📊 DATABASE SETUP COMPLETE")
        print("="*50)
        print(f"✅ Created {len(patients)} patients")
        print(f"✅ Created {len(doctors)} doctors")
        print(f"✅ Created {len(appointments)} appointments")
        print(f"✅ Created {len(treatments)} treatments")
        print(f"✅ Created {len(invoices)} invoices")
        print(f"✅ Database: {DB_PATH}")
        print("="*50 + "\n")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
