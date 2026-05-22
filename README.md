# 🧠 Diagnostic MCP Backend

A backend system for a **Conversational Diagnostic Marketplace (MCP)** that enables users to query diagnostic tests, place orders, and manage workflows using role-based access control.

---

## 🚀 Features

* 🔐 JWT-based Authentication
* 👥 Role-Based Access Control (RBAC)
* 🧪 Diagnostic Test Query & Recommendation
* 📦 Order Placement & Tracking
* 🗄️ PostgreSQL Database Integration
* 🤖 MCP Server Integration (Claude Desktop)
* 📧 OTP-based Authentication (SMTP)
* 🧩 Clean Modular Architecture

---

## 👤 Roles Supported

The system supports four roles:

* **Doctor** → Query tests, place orders, view own orders
* **Coordinator** → Manage orders and update status
* **Lab** → Process tests and update completion status
* **Admin** → Full system control (users, tests, orders)

---

## 🔄 Order Lifecycle

```
Placed → Sample Collected → Processing → Completed
```

---

## 🧱 Tech Stack

* **Backend**: FastAPI
* **Database**: PostgreSQL
* **ORM**: SQLAlchemy
* **Auth**: JWT + OTP (SMTP)
* **MCP**: FastMCP (Claude Desktop integration)

---

## ⚙️ Setup Instructions

### 1. Clone Repository

```bash
git clone <your-repo-link>
cd diagnostic-mcp
```

---

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Setup PostgreSQL

* Install PostgreSQL
* Create database:

```
diagnostic_db
```

---

### 5. Configure Environment

Create `.env` file:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/diagnostic_db
JWT_SECRET=your_secret_key
EMAIL_USER=your_email
EMAIL_PASS=your_app_password
```

---

### 6. Run Backend

```bash
uvicorn app.main:app --reload
```

---

## 🧪 Mock Users (For Testing)

You can use these accounts:

```
doctor@test.com      / doctor123
coordinator@test.com / coordinator123
lab@test.com         / lab123
admin@test.com       / admin123
```

---

## 🔐 Authentication Flow

1. Register user with role
2. Login → Receive JWT token
3. Use token to access protected APIs
4. `/auth/me` returns user profile + role

---

## 🤖 MCP Integration

The MCP server allows:

* Natural language queries
* Tool-based execution
* Role-based access to actions

---

