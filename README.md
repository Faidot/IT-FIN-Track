# IT FIN Track

<p align="center">
  <img src="https://img.shields.io/badge/Django-5.0-green?style=for-the-badge&logo=django" alt="Django">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Bootstrap-5.3-purple?style=for-the-badge&logo=bootstrap" alt="Bootstrap">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Version-2.0.0-orange?style=for-the-badge" alt="Version">
</p>

A professional **IT Finance Tracking System** built with Django for managing income, expenses, recurring bills, and financial reports.

## ✨ Features

### 💰 Financial Management
- **Income Tracking** — Track all income sources with categories and remaining balances
- **Expense Management** — Record expenses with multi-level approval workflow (Pending → Approved / Rejected)
- **Recurring Bills** — Manage monthly/quarterly/yearly bills with payment tracking, overdue alerts, and auto-expense creation
- **Payment Tracker** — Unified ledger linking payments to income sources

### 📊 Dashboard & Reports
- **Dashboard** — Real-time financial overview with charts, recurring bills summary card (paid/pending/overdue), and recent transactions
- **Monthly/Yearly Reports** — Detailed financial summaries with Excel export
- **Category Reports** — Expense breakdown by category with charts
- **Vendor Reports** — Spending analysis by vendor
- **Income vs Expense** — Side-by-side comparison statements
- **Audit Trail** — Complete activity logging (Admin only)

### 👥 User & Role Management
- **Role-Based Access Control** — Admin, Executive, Accountant, Manager, Viewer
- **Granular Permissions** — View, Add/Edit, Delete, Approve, Reports, Audit access per role
- **User Profiles** — Personal settings and password management

### 🔧 Masters
- **Income Sources** — Manage income categories (e.g., Budget Allocation, Reimbursement)
- **Vendors** — Track vendor/supplier information
- **Categories** — Organize expenses by category with icons and colors

### 🛡️ System
- **Backup & Restore** — Full database backup/restore with JSON export (Admin only)
- **Environment Config** — `.env`-based configuration for secrets and deployment settings

---

## 🛠️ Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Runtime |
| Django | 5.0 | Web Framework |
| PostgreSQL / SQLite | — | Database (auto-switches via `.env`) |
| Bootstrap | 5.3 | UI Framework |
| Chart.js | 4.4 | Dashboard Charts |
| WhiteNoise | 6.6 | Static File Serving |
| Gunicorn | latest | WSGI Server |
| Crispy Forms | 2.5 | Form Rendering |

---

## 📦 Quick Start

### Prerequisites
- Python 3.10+
- pip
- Git

### Setup (any OS)

```bash
# 1. Clone
git clone https://github.com/your-username/itfintrack.git
cd itfintrack

# 2. Virtual environment
python3 -m venv venv
source venv/bin/activate    # Windows: .\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env        # Then edit .env with your settings

# 5. Setup database
python manage.py migrate

# 6. Create admin user
python manage.py createsuperuser

# 7. Run
python manage.py runserver
# → http://127.0.0.1:8000
```

---

## 🔐 Default Roles & Permissions

| Role | View | Add/Edit | Delete | Approve | Reports | Audit Trail |
|------|:----:|:--------:|:------:|:-------:|:-------:|:-----------:|
| **Admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Executive** | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Accountant** | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Manager** | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| **Viewer** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 📁 Project Structure

```
IT-FIN-Track/
├── core/                       # Main application
│   ├── models/                 # Database models (User, Income, Expense, RecurringBill, etc.)
│   ├── views/                  # View functions (dashboard, bills, reports, etc.)
│   ├── forms/                  # Form classes
│   ├── signals/                # Django signals
│   ├── middleware/              # Custom middleware (Audit)
│   └── management/             # Management commands
├── templates/
│   ├── base.html               # Base layout with sidebar & navigation
│   └── core/                   # Feature templates (dashboard, bills, expenses, etc.)
├── static/css/                 # Custom stylesheets
├── itfintrack/                 # Project settings (settings.py, urls.py, wsgi.py)
├── media/                      # User uploads (receipts, bills)
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration
├── DEPLOYMENT_GUIDE.md         # Full Ubuntu + PostgreSQL + Nginx deployment guide
└── README.md                   # This file
```

---

## 🚀 Production Deployment

### Quick Checklist

```bash
# 1. Set environment
DEBUG=False
SECRET_KEY=<generate-a-strong-key>
ALLOWED_HOSTS=your-domain.com

# 2. Collect static files
python manage.py collectstatic --noinput

# 3. Run migrations
python manage.py migrate

# 4. Start with Gunicorn
gunicorn itfintrack.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

> 📖 For the **full step-by-step deployment guide** (Ubuntu + PostgreSQL + Nginx + Supervisor), see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### Environment Variables

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `DEBUG` | ✅ | `False` | Enable debug mode |
| `SECRET_KEY` | ✅ | — | Django secret key |
| `ALLOWED_HOSTS` | ✅ | `localhost` | Comma-separated allowed hosts |
| `DB_NAME` | ❌ | — | PostgreSQL database name (omit for SQLite) |
| `DB_USER` | ❌ | `postgres` | Database user |
| `DB_PASSWORD` | ❌ | `postgres` | Database password |
| `DB_HOST` | ❌ | `localhost` | Database host |
| `DB_PORT` | ❌ | `5432` | Database port |

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Developer

**Faizan** — TeraFort IT

---

## 📞 Support

For support, email: support@terafortit.com

---

<p align="center">
  Made with ❤️ by <strong>Faizan</strong> at TeraFort IT
</p>
