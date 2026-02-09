# IT FIN Track

<p align="center">
  <img src="https://img.shields.io/badge/Django-5.0-green?style=for-the-badge&logo=django" alt="Django">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Bootstrap-5.3-purple?style=for-the-badge&logo=bootstrap" alt="Bootstrap">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">
</p>

A professional **IT Finance Tracking System** built with Django for managing income, expenses, recurring bills, and financial reports.

## ✨ Features

### 💰 Financial Management
- **Income Tracking** - Track all income sources with categories and remaining balances
- **Expense Management** - Record expenses with approval workflow
- **Recurring Bills** - Manage monthly bills with payment tracking and overdue alerts
- **Payment Tracker** - Link payments to income sources

### 📊 Reports & Analytics
- **Dashboard** - Real-time financial overview with charts
- **Monthly/Yearly Reports** - Detailed financial summaries
- **Category Reports** - Expense breakdown by category
- **Vendor Reports** - Spending analysis by vendor
- **Audit Trail** - Complete activity logging (Admin only)

### 👥 User Management
- **Role-Based Access Control** - Admin, Executive, Accountant, Manager, Viewer
- **Permission System** - Granular access to features
- **User Profiles** - Personal settings and preferences

### 🔧 Masters
- **Income Sources** - Manage income categories
- **Vendors** - Track vendor information
- **Categories** - Organize expenses by category

---

## 🛠️ Tech Stack

| Technology | Version |
|------------|---------|
| Python | 3.10+ |
| Django | 5.0 |
| Bootstrap | 5.3 |
| SQLite | Default DB |
| Chart.js | 4.4 |

---

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git

### 🖥️ Windows Setup

```powershell
# 1. Clone the repository
git clone https://github.com/your-username/itfintrack.git
cd itfintrack

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Setup database
python manage.py migrate

# 6. Create superuser (Admin)
python manage.py createsuperuser

# 7. Run development server
python manage.py runserver

# Access at: http://127.0.0.1:8000
```

### 🐧 Linux Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/itfintrack.git
cd itfintrack

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Setup database
python manage.py migrate

# 6. Create superuser (Admin)
python manage.py createsuperuser

# 7. Run development server
python manage.py runserver

# Access at: http://127.0.0.1:8000
```

### 🍎 macOS Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/itfintrack.git
cd itfintrack

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Setup database
python manage.py migrate

# 6. Create superuser (Admin)
python manage.py createsuperuser

# 7. Run development server
python manage.py runserver

# Access at: http://127.0.0.1:8000
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
itfintrack/
├── core/                   # Main application
│   ├── models/             # Database models
│   ├── views/              # View functions
│   ├── templates/          # HTML templates
│   └── static/             # CSS, JS, images
├── templates/              # Base templates
├── static/                 # Static files
├── itfintrack/             # Project settings
├── manage.py               # Django CLI
├── requirements.txt        # Dependencies
└── README.md               # This file
```

---

## 🚀 Production Deployment

### Using Gunicorn (Linux/Mac)

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn itfintrack.wsgi:application --bind 0.0.0.0:8000
```

### Environment Variables

Create a `.env` file in the project root:

```env
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

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

**Faizan** - TeraFort IT

---

## 📞 Support

For support, email: support@terafortit.com

---

<p align="center">
  Made with ❤️ by <strong>Faizan</strong> at TeraFort IT
</p>
