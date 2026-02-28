# 🏛️ SmartGov — Smart Public Complaint & Grievance Redressal System

> **Digitizing Civic Services | Bridging Citizens & Government**

A full-stack E-Governance web application that allows citizens to file, track, and follow up on civic complaints in real-time. Departmental staff resolve them, and admins oversee the entire system — all from a single, modern platform.

---

## 🎯 Problem Statement

Citizens face difficulties reporting civic issues like water supply failures, electricity cuts, pothole roads, and sanitation problems. SmartGov solves this with a **transparent, trackable, role-based digital platform**.

---

## ✨ Key Features

### 👤 For Citizens
- Register & login securely
- Submit complaints with category, department, location & priority
- Real-time complaint status tracking (Submitted → Resolved)
- Status timeline showing every action taken
- Rate resolved complaints with 1–5 star feedback
- Instant in-app notifications on status changes
- Delete own complaints (if still pending)

### ⚙️ For Staff (Per Department)
- Auto-filtered view — only see complaints from their department
- Acknowledge, update, and resolve complaints
- Add resolution notes to every update
- Full audit trail of actions taken

### 🏛️ For Admins
- System-wide dashboard with 8 KPI cards
- Complaints by Category bar chart
- Department Performance tracker
- Assign complaints to specific staff members
- Update status of any complaint
- Delete any complaint
- View all registered citizens and staff

---

## 🔄 Complaint Lifecycle

```
[Citizen Files]
     ↓
 SUBMITTED → ACKNOWLEDGED → IN PROGRESS → RESOLVED → CLOSED
     ↓           ↓                                      ↑
 REJECTED     REJECTED                           [Citizen Confirms]
```

---

## 🏗️ Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3 (Custom Design System), Vanilla JavaScript |
| Backend | Python 3.x + FastAPI (REST API) |
| Database | SQLite (complaints.db) |
| Authentication | JWT (JSON Web Tokens) |
| Password Security | SHA-256 Hashing |
| Server | Uvicorn (ASGI) |
| API Documentation | Swagger UI (auto-generated) |

---

## 📂 Project Structure

```
Smart Public Complaint/
├── backend/
│   ├── main.py                 # FastAPI app — all 15+ API routes
│   ├── database.py             # SQLite schema + seed data
│   ├── auth.py                 # JWT token + password hashing utils
│   ├── complaints.db           # SQLite database (auto-created)
│   ├── requirements.txt        # Python dependencies
│   └── uploads/                # Attached files from complaints
│
└── frontend/
    ├── index.html              # Public landing page
    ├── login.html              # Role-based login
    ├── register.html           # New user registration
    ├── css/
    │   └── styles.css          # Full design system (dark theme)
    ├── js/
    │   └── app.js              # API client + Auth + Utilities
    ├── citizen/
    │   ├── dashboard.html      # Citizen home
    │   ├── submit.html         # File a new complaint
    │   ├── my-complaints.html  # Full complaints list
    │   └── profile.html        # User profile
    ├── staff/
    │   └── dashboard.html      # Staff complaint management
    └── admin/
        ├── dashboard.html      # Admin analytics & KPIs
        ├── complaints.html     # All complaints management
        ├── analytics.html      # Detailed charts
        └── users.html          # User management
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- A modern web browser

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/smart-public-complaint.git
cd smart-public-complaint

# 2. Install Python dependencies
cd backend
pip install -r requirements.txt

# 3. Start the backend server
python main.py

# 4. Open the app in your browser
# → http://localhost:8000
```

> The database (`complaints.db`) is auto-created and seeded on first run with demo accounts.

---

## 🔑 Demo Login Credentials

| Role | Email | Password |
|------|-------|----------|
| 👤 Citizen | citizen@demo.in | Citizen@123 |
| ⚡ Staff (Electricity) | electric@smartgov.in | Staff@123 |
| 💧 Staff (Water) | water@smartgov.in | Staff@123 |
| 🗑️ Staff (Sanitation) | sanitation@smartgov.in | Staff@123 |
| 🏗️ Staff (Infrastructure) | infra@smartgov.in | Staff@123 |
| 🏛️ Admin | admin@smartgov.in | Admin@123 |

---

## 📡 REST API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | Public | Register new user |
| POST | `/api/auth/login` | Public | Login & receive JWT |
| GET | `/api/auth/me` | All | Current user details |
| GET | `/api/complaints` | All | List complaints (role-filtered) |
| POST | `/api/complaints` | Citizen | Submit new complaint |
| GET | `/api/complaints/{id}` | All | Complaint detail + timeline |
| PUT | `/api/complaints/{id}/status` | Staff/Admin | Update complaint status |
| DELETE | `/api/complaints/{id}` | Role-based | Delete complaint |
| POST | `/api/complaints/{id}/feedback` | Citizen | Rate resolution |
| POST | `/api/complaints/{id}/upload` | All | Upload file attachment |
| GET | `/api/notifications` | All | Get notifications |
| PUT | `/api/notifications/{id}/read` | All | Mark notification as read |
| GET | `/api/analytics/dashboard` | Admin | System analytics |
| GET | `/api/admin/users` | Admin | All users |
| GET | `/api/admin/staff` | Admin | Staff members list |

📖 Full interactive API docs: `http://localhost:8000/api/docs`

---

## 🔐 Security

- **JWT Tokens** — Stateless authentication
- **Role-Based Access** — Every API endpoint validates user role
- **Password Hashing** — SHA-256 (passwords never stored in plain text)
- **Input Validation** — Pydantic models enforce strict data types
- **Cascade Deletes** — Removing a complaint cleans up all related records

---

## 📊 Departments

| Category | Department | Typical Issues |
|----------|-----------|---------------|
| 💧 Water | Water Supply | No water, pipe leakage, dirty water |
| ⚡ Electricity | Electricity | Power cuts, wire damage, street lights |
| 🗑️ Sanitation | Sanitation | Garbage, clogged drains, sewage |
| 🏗️ Infrastructure | Infrastructure | Potholes, broken footpaths, bridges |

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

> **SmartGov — Making Governance Accountable, Transparent & Citizen-Centric** 🏛️
