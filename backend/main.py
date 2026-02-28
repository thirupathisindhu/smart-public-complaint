"""
SmartGov — FastAPI Backend
All REST API routes for the Smart Public Complaint & Grievance Redressal System.
"""
import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import init_db, get_db
from auth import hash_password, verify_password, create_access_token, decode_access_token

# ── Initialize App ──
app = FastAPI(title="SmartGov API", version="1.0.0", docs_url="/api/docs", redoc_url="/api/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Ensure uploads directory exists ──
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── Static files — serve frontend ──
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
app.mount("/citizen", StaticFiles(directory=os.path.join(FRONTEND_DIR, "citizen"), html=True), name="citizen")
app.mount("/staff", StaticFiles(directory=os.path.join(FRONTEND_DIR, "staff"), html=True), name="staff")
app.mount("/admin", StaticFiles(directory=os.path.join(FRONTEND_DIR, "admin"), html=True), name="admin")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# ══════════════════════════════════════
# ── Pydantic Models ──
# ══════════════════════════════════════

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5)
    phone: Optional[str] = None
    password: str = Field(..., min_length=6)
    role: str = Field(default="citizen")
    department: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ComplaintCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    category: str
    department: str
    location: Optional[str] = None
    priority: str = Field(default="Medium")


class StatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None
    assigned_to: Optional[int] = None


class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


# ══════════════════════════════════════
# ── Auth Dependency ──
# ══════════════════════════════════════

async def get_current_user(request: Request):
    """Extract and validate current user from JWT token."""
    authorization = request.headers.get("authorization") or request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (int(payload["sub"]),)).fetchone()
    db.close()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return dict(user)


# ══════════════════════════════════════
# ── Frontend HTML Routes ──
# ══════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def serve_landing():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/login.html", response_class=HTMLResponse)
async def serve_login():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))


@app.get("/login", response_class=HTMLResponse)
async def serve_login_alt():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))


@app.get("/register.html", response_class=HTMLResponse)
async def serve_register():
    return FileResponse(os.path.join(FRONTEND_DIR, "register.html"))


@app.get("/register", response_class=HTMLResponse)
async def serve_register_alt():
    return FileResponse(os.path.join(FRONTEND_DIR, "register.html"))


# ══════════════════════════════════════
# ── AUTH ENDPOINTS ──
# ══════════════════════════════════════

@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    """Register a new user."""
    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email = ?", (req.email,)).fetchone()
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    cursor = db.execute(
        """INSERT INTO users (full_name, email, phone, password_hash, role, department)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (req.full_name, req.email, req.phone, hash_password(req.password), req.role, req.department)
    )
    user_id = cursor.lastrowid
    db.commit()
    db.close()

    token = create_access_token({"sub": str(user_id), "role": req.role, "email": req.email})
    return {
        "message": "Registration successful",
        "token": token,
        "user": {
            "id": user_id,
            "full_name": req.full_name,
            "email": req.email,
            "role": req.role,
            "department": req.department
        }
    }


@app.post("/api/auth/login")
async def login(req: LoginRequest):
    """Login and receive JWT token."""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (req.email,)).fetchone()
    db.close()

    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token({"sub": str(user["id"]), "role": user["role"], "email": user["email"]})
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
            "department": user["department"],
            "phone": user["phone"]
        }
    }


@app.get("/api/auth/me")
async def get_me(user=Depends(get_current_user)):
    """Get current user's profile."""
    return {
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "phone": user["phone"],
        "role": user["role"],
        "department": user["department"],
        "created_at": user["created_at"]
    }


# ══════════════════════════════════════
# ── COMPLAINT ENDPOINTS ──
# ══════════════════════════════════════

def generate_complaint_number():
    """Generate a unique complaint number."""
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    db.close()
    return f"CMP-{datetime.now().year}-{str(count + 1).zfill(4)}"


@app.get("/api/complaints")
async def list_complaints(
    status: Optional[str] = None,
    category: Optional[str] = None,
    department: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user=Depends(get_current_user)
):
    """List complaints — filtered by role."""
    db = get_db()
    query = """
        SELECT c.*, u.full_name as citizen_name, s.full_name as assigned_staff_name
        FROM complaints c
        LEFT JOIN users u ON c.citizen_id = u.id
        LEFT JOIN users s ON c.assigned_to = s.id
        WHERE 1=1
    """
    params = []

    # Role-based filtering
    if user["role"] == "citizen":
        query += " AND c.citizen_id = ?"
        params.append(user["id"])
    elif user["role"] == "staff":
        query += " AND c.department = ?"
        params.append(user["department"])

    # Optional filters
    if status:
        query += " AND c.status = ?"
        params.append(status)
    if category:
        query += " AND c.category = ?"
        params.append(category)
    if department and user["role"] != "staff":
        query += " AND c.department = ?"
        params.append(department)
    if priority:
        query += " AND c.priority = ?"
        params.append(priority)
    if search:
        query += " AND (c.title LIKE ? OR c.description LIKE ? OR c.complaint_number LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])

    # Count total
    count_query = query.replace(
        "SELECT c.*, u.full_name as citizen_name, s.full_name as assigned_staff_name",
        "SELECT COUNT(*)"
    )
    total = db.execute(count_query, params).fetchone()[0]

    # Pagination
    query += " ORDER BY c.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, (page - 1) * limit])

    complaints = [dict(row) for row in db.execute(query, params).fetchall()]
    db.close()

    return {"complaints": complaints, "total": total, "page": page, "limit": limit}


@app.post("/api/complaints")
async def create_complaint(complaint: ComplaintCreate, user=Depends(get_current_user)):
    """Submit a new complaint (Citizens only)."""
    if user["role"] != "citizen":
        raise HTTPException(status_code=403, detail="Only citizens can submit complaints")

    comp_number = generate_complaint_number()
    db = get_db()
    cursor = db.execute(
        """INSERT INTO complaints (complaint_number, citizen_id, title, description, category, department, location, priority)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (comp_number, user["id"], complaint.title, complaint.description, complaint.category,
         complaint.department, complaint.location, complaint.priority)
    )
    complaint_id = cursor.lastrowid

    # Add timeline entry
    db.execute(
        """INSERT INTO complaint_timeline (complaint_id, updated_by, action, new_status, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (complaint_id, user["id"], "Complaint Filed", "Submitted", f"Complaint filed by {user['full_name']}")
    )

    # Notify admins
    admins = db.execute("SELECT id FROM users WHERE role = 'admin'").fetchall()
    for admin in admins:
        db.execute(
            "INSERT INTO notifications (user_id, complaint_id, message) VALUES (?, ?, ?)",
            (admin["id"], complaint_id, f"New complaint {comp_number}: {complaint.title}")
        )

    # Notify department staff
    staff = db.execute(
        "SELECT id FROM users WHERE role = 'staff' AND department = ?", (complaint.department,)
    ).fetchall()
    for s in staff:
        db.execute(
            "INSERT INTO notifications (user_id, complaint_id, message) VALUES (?, ?, ?)",
            (s["id"], complaint_id, f"New complaint {comp_number} for {complaint.department}: {complaint.title}")
        )

    db.commit()
    db.close()

    return {
        "message": "Complaint submitted successfully",
        "complaint_number": comp_number,
        "complaint_id": complaint_id
    }


@app.get("/api/complaints/{complaint_id}")
async def get_complaint(complaint_id: int, user=Depends(get_current_user)):
    """Get full complaint detail with timeline."""
    db = get_db()
    complaint = db.execute(
        """SELECT c.*, u.full_name as citizen_name, u.email as citizen_email,
                  s.full_name as assigned_staff_name
           FROM complaints c
           LEFT JOIN users u ON c.citizen_id = u.id
           LEFT JOIN users s ON c.assigned_to = s.id
           WHERE c.id = ?""",
        (complaint_id,)
    ).fetchone()

    if not complaint:
        db.close()
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint = dict(complaint)

    # Access control
    if user["role"] == "citizen" and complaint["citizen_id"] != user["id"]:
        db.close()
        raise HTTPException(status_code=403, detail="Access denied")
    if user["role"] == "staff" and complaint["department"] != user["department"]:
        db.close()
        raise HTTPException(status_code=403, detail="Access denied")

    # Get timeline
    timeline = [dict(row) for row in db.execute(
        """SELECT ct.*, u.full_name as updated_by_name
           FROM complaint_timeline ct
           LEFT JOIN users u ON ct.updated_by = u.id
           WHERE ct.complaint_id = ?
           ORDER BY ct.created_at ASC""",
        (complaint_id,)
    ).fetchall()]

    # Get feedback
    feedback = db.execute(
        "SELECT * FROM feedback WHERE complaint_id = ?", (complaint_id,)
    ).fetchone()

    db.close()

    complaint["timeline"] = timeline
    complaint["feedback"] = dict(feedback) if feedback else None

    return complaint


@app.put("/api/complaints/{complaint_id}/status")
async def update_complaint_status(complaint_id: int, update: StatusUpdate, user=Depends(get_current_user)):
    """Update complaint status (Staff/Admin only)."""
    if user["role"] == "citizen":
        # Citizens can only close resolved complaints
        if update.status != "Closed":
            raise HTTPException(status_code=403, detail="Citizens can only close resolved complaints")

    db = get_db()
    complaint = db.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
    if not complaint:
        db.close()
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint = dict(complaint)

    # Staff can only see their department
    if user["role"] == "staff" and complaint["department"] != user["department"]:
        db.close()
        raise HTTPException(status_code=403, detail="Access denied")

    old_status = complaint["status"]

    # Build update query
    update_fields = ["status = ?"]
    update_params = [update.status]

    if update.notes:
        update_fields.append("resolution_notes = ?")
        update_params.append(update.notes)

    if update.assigned_to:
        update_fields.append("assigned_to = ?")
        update_params.append(update.assigned_to)

    if update.status == "Resolved":
        update_fields.append("resolved_at = ?")
        update_params.append(datetime.now().isoformat())

    update_params.append(complaint_id)

    db.execute(f"UPDATE complaints SET {', '.join(update_fields)} WHERE id = ?", update_params)

    # Add timeline entry
    action = "Status Updated"
    if update.assigned_to:
        action = "Assigned to Staff"
    db.execute(
        """INSERT INTO complaint_timeline (complaint_id, updated_by, action, old_status, new_status, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (complaint_id, user["id"], action, old_status, update.status, update.notes or "")
    )

    # Notify citizen
    db.execute(
        "INSERT INTO notifications (user_id, complaint_id, message) VALUES (?, ?, ?)",
        (complaint["citizen_id"], complaint_id,
         f"Your complaint {complaint['complaint_number']} status changed to {update.status}.")
    )

    # If assigned, notify the staff
    if update.assigned_to:
        db.execute(
            "INSERT INTO notifications (user_id, complaint_id, message) VALUES (?, ?, ?)",
            (update.assigned_to, complaint_id,
             f"Complaint {complaint['complaint_number']} has been assigned to you.")
        )

    db.commit()
    db.close()

    return {"message": f"Status updated to {update.status}"}


@app.delete("/api/complaints/{complaint_id}")
async def delete_complaint(complaint_id: int, user=Depends(get_current_user)):
    """Delete a complaint (role-based permissions)."""
    db = get_db()
    complaint = db.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,)).fetchone()

    if not complaint:
        db.close()
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint = dict(complaint)

    # Permission check
    if user["role"] == "citizen":
        if complaint["citizen_id"] != user["id"]:
            db.close()
            raise HTTPException(status_code=403, detail="You can only delete your own complaints")
        if complaint["status"] not in ("Submitted", "Rejected"):
            db.close()
            raise HTTPException(status_code=403, detail="You can only delete pending or rejected complaints")
    elif user["role"] == "staff":
        if complaint["department"] != user["department"]:
            db.close()
            raise HTTPException(status_code=403, detail="You can only delete complaints from your department")

    # Cascade delete related records
    db.execute("DELETE FROM complaint_timeline WHERE complaint_id = ?", (complaint_id,))
    db.execute("DELETE FROM notifications WHERE complaint_id = ?", (complaint_id,))
    db.execute("DELETE FROM feedback WHERE complaint_id = ?", (complaint_id,))
    db.execute("DELETE FROM complaints WHERE id = ?", (complaint_id,))
    db.commit()
    db.close()

    return {"message": "Complaint deleted successfully"}


# ══════════════════════════════════════
# ── FEEDBACK ENDPOINT ──
# ══════════════════════════════════════

@app.post("/api/complaints/{complaint_id}/feedback")
async def submit_feedback(complaint_id: int, fb: FeedbackCreate, user=Depends(get_current_user)):
    """Rate a resolved complaint (Citizens only)."""
    if user["role"] != "citizen":
        raise HTTPException(status_code=403, detail="Only citizens can submit feedback")

    db = get_db()
    complaint = db.execute("SELECT * FROM complaints WHERE id = ? AND citizen_id = ?",
                           (complaint_id, user["id"])).fetchone()
    if not complaint:
        db.close()
        raise HTTPException(status_code=404, detail="Complaint not found")

    if complaint["status"] not in ("Resolved", "Closed"):
        db.close()
        raise HTTPException(status_code=400, detail="Can only rate resolved or closed complaints")

    # Check if already rated
    existing = db.execute("SELECT id FROM feedback WHERE complaint_id = ? AND citizen_id = ?",
                          (complaint_id, user["id"])).fetchone()
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="You have already rated this complaint")

    db.execute(
        "INSERT INTO feedback (complaint_id, citizen_id, rating, comment) VALUES (?, ?, ?, ?)",
        (complaint_id, user["id"], fb.rating, fb.comment)
    )
    db.commit()
    db.close()

    return {"message": "Feedback submitted successfully"}


# ══════════════════════════════════════
# ── FILE UPLOAD ENDPOINT ──
# ══════════════════════════════════════

@app.post("/api/complaints/{complaint_id}/upload")
async def upload_attachment(complaint_id: int, file: UploadFile = File(...), user=Depends(get_current_user)):
    """Upload file attachment for a complaint."""
    db = get_db()
    complaint = db.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
    if not complaint:
        db.close()
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Save file
    ext = os.path.splitext(file.filename)[1]
    filename = f"{complaint_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    db.execute("UPDATE complaints SET attachment_path = ? WHERE id = ?", (filename, complaint_id))
    db.commit()
    db.close()

    return {"message": "File uploaded successfully", "filename": filename}


# ══════════════════════════════════════
# ── NOTIFICATION ENDPOINTS ──
# ══════════════════════════════════════

@app.get("/api/notifications")
async def get_notifications(user=Depends(get_current_user)):
    """Get user's notifications."""
    db = get_db()
    notifications = [dict(row) for row in db.execute(
        """SELECT n.*, c.complaint_number
           FROM notifications n
           LEFT JOIN complaints c ON n.complaint_id = c.id
           WHERE n.user_id = ?
           ORDER BY n.created_at DESC
           LIMIT 50""",
        (user["id"],)
    ).fetchall()]
    unread_count = db.execute(
        "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
        (user["id"],)
    ).fetchone()[0]
    db.close()

    return {"notifications": notifications, "unread_count": unread_count}


@app.put("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int, user=Depends(get_current_user)):
    """Mark a notification as read."""
    db = get_db()
    db.execute(
        "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
        (notification_id, user["id"])
    )
    db.commit()
    db.close()
    return {"message": "Notification marked as read"}


@app.put("/api/notifications/read-all")
async def mark_all_notifications_read(user=Depends(get_current_user)):
    """Mark all notifications as read."""
    db = get_db()
    db.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user["id"],))
    db.commit()
    db.close()
    return {"message": "All notifications marked as read"}


# ══════════════════════════════════════
# ── ANALYTICS ENDPOINT (Admin) ──
# ══════════════════════════════════════

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics(user=Depends(get_current_user)):
    """System-wide analytics for admin dashboard."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    db = get_db()

    # KPI cards
    total = db.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('Submitted', 'Acknowledged')").fetchone()[0]
    in_progress = db.execute("SELECT COUNT(*) FROM complaints WHERE status = 'In Progress'").fetchone()[0]
    resolved = db.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('Resolved', 'Closed')").fetchone()[0]
    rejected = db.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Rejected'").fetchone()[0]
    total_citizens = db.execute("SELECT COUNT(*) FROM users WHERE role = 'citizen'").fetchone()[0]
    total_staff = db.execute("SELECT COUNT(*) FROM users WHERE role = 'staff'").fetchone()[0]

    # Average rating
    avg_rating = db.execute("SELECT AVG(rating) FROM feedback").fetchone()[0]
    avg_rating = round(avg_rating, 1) if avg_rating else 0

    # By category
    by_category = [dict(row) for row in db.execute(
        "SELECT category, COUNT(*) as count FROM complaints GROUP BY category ORDER BY count DESC"
    ).fetchall()]

    # By department
    by_department = [dict(row) for row in db.execute(
        """SELECT department,
                  COUNT(*) as total,
                  SUM(CASE WHEN status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) as resolved,
                  SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                  SUM(CASE WHEN status IN ('Submitted', 'Acknowledged') THEN 1 ELSE 0 END) as pending
           FROM complaints GROUP BY department"""
    ).fetchall()]

    # By status
    by_status = [dict(row) for row in db.execute(
        "SELECT status, COUNT(*) as count FROM complaints GROUP BY status"
    ).fetchall()]

    # By priority
    by_priority = [dict(row) for row in db.execute(
        "SELECT priority, COUNT(*) as count FROM complaints GROUP BY priority"
    ).fetchall()]

    # Monthly trends (last 6 months)
    monthly_trends = [dict(row) for row in db.execute(
        """SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
           FROM complaints
           GROUP BY month ORDER BY month DESC LIMIT 6"""
    ).fetchall()]

    # Recent complaints
    recent = [dict(row) for row in db.execute(
        """SELECT c.*, u.full_name as citizen_name
           FROM complaints c LEFT JOIN users u ON c.citizen_id = u.id
           ORDER BY c.created_at DESC LIMIT 5"""
    ).fetchall()]

    db.close()

    return {
        "kpi": {
            "total_complaints": total,
            "pending": pending,
            "in_progress": in_progress,
            "resolved": resolved,
            "rejected": rejected,
            "total_citizens": total_citizens,
            "total_staff": total_staff,
            "avg_rating": avg_rating
        },
        "by_category": by_category,
        "by_department": by_department,
        "by_status": by_status,
        "by_priority": by_priority,
        "monthly_trends": monthly_trends,
        "recent_complaints": recent
    }


# ══════════════════════════════════════
# ── ADMIN USER MANAGEMENT ──
# ══════════════════════════════════════

@app.get("/api/admin/users")
async def get_all_users(role: Optional[str] = None, user=Depends(get_current_user)):
    """Get all registered users (Admin only)."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    db = get_db()
    query = "SELECT id, full_name, email, phone, role, department, is_active, created_at FROM users WHERE 1=1"
    params = []
    if role:
        query += " AND role = ?"
        params.append(role)
    query += " ORDER BY created_at DESC"

    users = [dict(row) for row in db.execute(query, params).fetchall()]
    db.close()
    return {"users": users}


@app.get("/api/admin/staff")
async def get_staff(user=Depends(get_current_user)):
    """Get all staff members (Admin only)."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    db = get_db()
    staff = [dict(row) for row in db.execute(
        """SELECT id, full_name, email, department, is_active, created_at
           FROM users WHERE role = 'staff' ORDER BY department, full_name"""
    ).fetchall()]
    db.close()
    return {"staff": staff}


@app.put("/api/admin/users/{user_id}/toggle")
async def toggle_user_status(user_id: int, user=Depends(get_current_user)):
    """Toggle user active status (Admin only)."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    db = get_db()
    target = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    new_status = 0 if target["is_active"] else 1
    db.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
    db.commit()
    db.close()
    return {"message": f"User {'activated' if new_status else 'deactivated'} successfully"}


# ══════════════════════════════════════
# ── PUBLIC STATS (Landing Page) ──
# ══════════════════════════════════════

@app.get("/api/stats")
async def get_public_stats():
    """Public stats for the landing page — no auth required."""
    db = get_db()
    total_complaints = db.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    resolved = db.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('Resolved', 'Closed')").fetchone()[0]
    total_citizens = db.execute("SELECT COUNT(*) FROM users WHERE role = 'citizen'").fetchone()[0]
    total_departments = db.execute("SELECT COUNT(DISTINCT department) FROM complaints").fetchone()[0]
    db.close()
    return {
        "total_complaints": total_complaints,
        "resolved": resolved,
        "total_citizens": total_citizens,
        "total_departments": total_departments
    }


# ══════════════════════════════════════
# ── Startup ──
# ══════════════════════════════════════

@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()
    print("🏛️  SmartGov API is running!")
    print("📖 API Docs: http://localhost:8000/api/docs")
    print("🌐 Frontend: http://localhost:8000")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
