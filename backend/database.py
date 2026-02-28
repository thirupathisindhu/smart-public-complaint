"""
Database initialization, schema creation, and seed data.
"""
import sqlite3
import os
from auth import hash_password

DB_PATH = os.path.join(os.path.dirname(__file__), "complaints.db")


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize the database schema and seed demo data."""
    conn = get_db()
    cursor = conn.cursor()

    # ── Users Table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('citizen', 'staff', 'admin')),
            department TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Complaints Table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_number TEXT UNIQUE NOT NULL,
            citizen_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            department TEXT NOT NULL,
            location TEXT,
            priority TEXT DEFAULT 'Medium' CHECK(priority IN ('Low', 'Medium', 'High', 'Critical')),
            status TEXT DEFAULT 'Submitted' CHECK(status IN ('Submitted', 'Acknowledged', 'In Progress', 'Resolved', 'Closed', 'Rejected')),
            assigned_to INTEGER,
            resolution_notes TEXT,
            attachment_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (citizen_id) REFERENCES users(id),
            FOREIGN KEY (assigned_to) REFERENCES users(id)
        )
    """)

    # ── Complaint Timeline Table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaint_timeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            updated_by INTEGER NOT NULL,
            action TEXT NOT NULL,
            old_status TEXT,
            new_status TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
            FOREIGN KEY (updated_by) REFERENCES users(id)
        )
    """)

    # ── Notifications Table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            complaint_id INTEGER,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE
        )
    """)

    # ── Feedback Table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            citizen_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
            FOREIGN KEY (citizen_id) REFERENCES users(id)
        )
    """)

    conn.commit()

    # ── Seed Demo Data ──
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        seed_data(conn)

    conn.close()


def seed_data(conn):
    """Insert demo users and sample complaints."""
    cursor = conn.cursor()

    # Demo Users
    demo_users = [
        ("Admin User", "admin@smartgov.in", "9000000001", hash_password("Admin@123"), "admin", "System Admin"),
        ("Rajesh Kumar", "citizen@demo.in", "9000000002", hash_password("Citizen@123"), "citizen", None),
        ("Priya Sharma", "priya@demo.in", "9000000003", hash_password("Citizen@123"), "citizen", None),
        ("Electric Staff", "electric@smartgov.in", "9000000004", hash_password("Staff@123"), "staff", "Electricity"),
        ("Water Staff", "water@smartgov.in", "9000000005", hash_password("Staff@123"), "staff", "Water Supply"),
        ("Sanitation Staff", "sanitation@smartgov.in", "9000000006", hash_password("Staff@123"), "staff", "Sanitation"),
        ("Infra Staff", "infra@smartgov.in", "9000000007", hash_password("Staff@123"), "staff", "Infrastructure"),
    ]
    cursor.executemany(
        "INSERT INTO users (full_name, email, phone, password_hash, role, department) VALUES (?, ?, ?, ?, ?, ?)",
        demo_users
    )

    # Sample Complaints
    sample_complaints = [
        ("CMP-2024-0001", 2, "No water supply for 3 days", "Our area has not received water supply for the past 3 days. Multiple families are affected.", "Water", "Water Supply", "MG Road, Sector 5, Hyderabad", "High", "Acknowledged", 5, None),
        ("CMP-2024-0002", 2, "Street light not working", "The street light near the park entrance has been off for a week. Very unsafe at night.", "Electricity", "Electricity", "Park Avenue, Sector 12, Hyderabad", "Medium", "Submitted", None, None),
        ("CMP-2024-0003", 3, "Garbage not collected", "Garbage has not been collected from our colony for 5 days. Causing health hazard.", "Sanitation", "Sanitation", "Green Colony, Sector 8, Hyderabad", "High", "In Progress", 6, None),
        ("CMP-2024-0004", 2, "Pothole on main road", "Large pothole has developed on the main road causing accidents. Needs immediate repair.", "Infrastructure", "Infrastructure", "NH-65, Near Toll Plaza, Hyderabad", "Critical", "Resolved", 7, "Pothole has been filled and road has been resurfaced."),
        ("CMP-2024-0005", 3, "Electricity bill dispute", "Received abnormally high electricity bill this month despite normal usage.", "Electricity", "Electricity", "Flat 302, Sunrise Apartments, Hyderabad", "Low", "Submitted", None, None),
        ("CMP-2024-0006", 2, "Drainage overflow", "Drainage system overflowing near the school causing sewage on the road.", "Sanitation", "Sanitation", "School Street, Sector 3, Hyderabad", "Critical", "Acknowledged", 6, None),
        ("CMP-2024-0007", 3, "Broken footpath", "The footpath tiles are broken and uneven, posing risks for pedestrians.", "Infrastructure", "Infrastructure", "Central Market Road, Hyderabad", "Medium", "Submitted", None, None),
        ("CMP-2024-0008", 2, "Water pipeline leak", "Major water leak from the underground pipeline wasting thousands of liters daily.", "Water", "Water Supply", "Industrial Area, Phase 2, Hyderabad", "High", "In Progress", 5, None),
    ]
    cursor.executemany(
        """INSERT INTO complaints (complaint_number, citizen_id, title, description, category, department,
           location, priority, status, assigned_to, resolution_notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        sample_complaints
    )

    # Sample Timeline Entries
    timeline_entries = [
        (1, 2, "Complaint Filed", None, "Submitted", "Water supply issue reported by citizen."),
        (1, 5, "Status Updated", "Submitted", "Acknowledged", "We have received your complaint. Our team will inspect the area."),
        (3, 3, "Complaint Filed", None, "Submitted", "Garbage collection issue reported."),
        (3, 6, "Status Updated", "Submitted", "Acknowledged", "Complaint acknowledged by sanitation department."),
        (3, 6, "Status Updated", "Acknowledged", "In Progress", "Sanitation team dispatched to the area."),
        (4, 2, "Complaint Filed", None, "Submitted", "Pothole complaint registered."),
        (4, 7, "Status Updated", "Submitted", "Acknowledged", "Infrastructure team will inspect."),
        (4, 7, "Status Updated", "Acknowledged", "In Progress", "Road repair crew deployed."),
        (4, 7, "Status Updated", "In Progress", "Resolved", "Pothole has been filled and road resurfaced."),
    ]
    cursor.executemany(
        """INSERT INTO complaint_timeline (complaint_id, updated_by, action, old_status, new_status, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        timeline_entries
    )

    # Sample Notifications
    notifications = [
        (2, 1, "Your complaint CMP-2024-0001 has been acknowledged by Water Supply department."),
        (2, 4, "Your complaint CMP-2024-0004 has been resolved. Please rate the service."),
        (3, 3, "Your complaint CMP-2024-0003 is now In Progress."),
        (5, 1, "New complaint CMP-2024-0001 assigned to you."),
        (6, 3, "New complaint CMP-2024-0003 assigned to you."),
    ]
    cursor.executemany(
        "INSERT INTO notifications (user_id, complaint_id, message) VALUES (?, ?, ?)",
        notifications
    )

    # Sample Feedback
    cursor.execute(
        "INSERT INTO feedback (complaint_id, citizen_id, rating, comment) VALUES (?, ?, ?, ?)",
        (4, 2, 4, "Good job fixing the pothole. Could have been faster though.")
    )

    conn.commit()
    print("✅ Database seeded with demo data successfully!")


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
