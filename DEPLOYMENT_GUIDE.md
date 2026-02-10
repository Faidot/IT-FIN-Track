
# IT FIN Track - Production Deployment Guide (Ubuntu + PostgreSQL)

This comprehensive guide details the step-by-step process to deploy the **IT FIN Track** Django application on a fresh Ubuntu server. This setup uses **PostgreSQL** as the database, **Gunicorn** as the application server, and **Nginx** as the reverse proxy.

## Overview of Components

- **Ubuntu Server**: The operating system hosting the application.
- **PostgreSQL**: A powerful, open-source object-relational database system. use for production data storage instead of SQLite for better performance and data integrity.
- **Gunicorn**: A Python WSGI HTTP Server for UNIX. It runs the Django Python code.
- **Nginx**: A high-performance web server that acts as a reverse proxy, handling client requests, serving static files, and passing dynamic requests to Gunicorn.
- **Supervisor**: A process control system that ensures Gunicorn keeps running and restarts it if it crashes.

---

## 1. System Updates & Prerequisites

**Why?** Ensures your server has the latest security patches and software repositories.
**How?** Run the following commands:

```bash
sudo apt update && sudo apt upgrade -y
```

Install the necessary system packages:
**Why?** `python3-pip` and `python3-dev` are for Python package management and building C extensions. `libpq-dev` is required for the PostgreSQL adapter (`psycopg2`). `nginx` is the web server.

```bash
sudo apt install python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx curl git -y
```

Install `virtualenv` to manage python environments:
**Why?** To keep project dependencies isolated from the system Python packages.
```bash
sudo -H pip3 install --upgrade pip
sudo -H pip3 install virtualenv
```

## 2. PostgreSQL Database Setup

**Why?** We moved from SQLite to PostgreSQL because SQLite is a file-based database not suitable for high-concurrency production environments. PostgreSQL handles multiple simultaneous users and large datasets much better.
**How?**

1.  **Start and enable PostgreSQL**:
    ```bash
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    ```

2.  **Create Database and User**:
    Switch to the postgres user and access the database shell:
    ```bash
    sudo -u postgres psql
    ```

    Run the following SQL commands (change 'yourpassword' to a secure password):
    ```sql
    CREATE DATABASE itfintrack;
    CREATE USER itfinuser WITH PASSWORD 'yourpassword';
    ALTER ROLE itfinuser SET client_encoding TO 'utf8';
    ALTER ROLE itfinuser SET default_transaction_isolation TO 'read committed';
    ALTER ROLE itfinuser SET timezone TO 'UTC';
    GRANT ALL PRIVILEGES ON DATABASE itfintrack TO itfinuser;
    \q
    ```
    *Note: The `\q` command exits the psql shell.*

## 3. Project Setup

**Why?** We place the code in `/var/www` as it's the standard convention for web data.
**How?**

1.  **Clone/Copy Project**:
    ```bash
    sudo mkdir -p /var/www/itfintrack
    sudo chown -R $USER:$USER /var/www/itfintrack
    cd /var/www/itfintrack
    
    # Clone your repo logic here:
    # git clone <your-repo-url> .
    # OR upload files via SCP/FileZilla
    ```

2.  **Create Virtual Environment**:
    ```bash
    virtualenv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**:
    **Why?** Installs all Python libraries your project needs, including `psycopg2-binary` for connecting to PostgreSQL.
    ```bash
    pip install -r requirements.txt
    pip install gunicorn  # Ensure gunicorn is also installed
    ```

## 4. Environment Configuration

**Why?** Hardcoding secrets (like passwords and secret keys) in code is a security risk. We use a `.env` file to store these securely on the server.
**How?**

Create a `.env` file in the project root:
```bash
nano .env
```

Add the following content (update with your actual values):
```ini
DEBUG=False
SECRET_KEY=your-secure-production-secret-key-here
ALLOWED_HOSTS=YOUR_SERVER_IP,domain.com
DB_NAME=itfintrack
DB_USER=itfinuser
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
```
*Note: Using `python-decouple`, Django will read these values automatically.*

## 5. Django Initialization

**How?**

1.  **Collect Static Files**:
    **Why?** Nginx serves static files (CSS, JS, Images) directly for speed. This command copies them all to one folder (`staticfiles`).
    ```bash
    python manage.py collectstatic --noinput
    ```

2.  **Apply Migrations**:
    **Why?** Creates the necessary tables in your new PostgreSQL database.
    ```bash
    python manage.py migrate
    ```

3.  **Create Superuser**:
    **Why?** To access the Django Admin interface.
    ```bash
    python manage.py createsuperuser
    ```

## 6. Gunicorn Setup

**Why?** Gunicorn executes the Python code. We test it first to ensure it runs, then configure Supervisor to keep it running permanently.
**How?**

1.  **Test Gunicorn**:
    ```bash
    gunicorn --bind 0.0.0.0:8000 itfintrack.wsgi
    ```
    Visit `http://YOUR_SERVER_IP:8000` to verify. Press `Ctrl+C` to stop.

2.  **Configure Supervisor**:
    **Why?** If the server restarts or the app crashes, Supervisor automatically restarts it.
    
    Install Supervisor:
    ```bash
    sudo apt install supervisor -y
    ```

    Create configuration file:
    ```bash
    sudo nano /etc/supervisor/conf.d/itfintrack.conf
    ```

    Content:
    ```ini
    [program:itfintrack]
    directory=/var/www/itfintrack
    command=/var/www/itfintrack/venv/bin/gunicorn --workers 3 --bind unix:/var/www/itfintrack/app.sock itfintrack.wsgi:application
    autostart=true
    autorestart=true
    stderr_logfile=/var/log/itfintrack.err.log
    stdout_logfile=/var/log/itfintrack.out.log
    user=ubuntu
    group=www-data
    environment=LANG=en_US.UTF-8,LC_ALL=en_US.UTF-8
    ```
    *Change `user=ubuntu` to your actual server username.*

    Start Supervisor:
    ```bash
    sudo supervisorctl reread
    sudo supervisorctl update
    sudo supervisorctl status
    ```

## 7. Nginx Setup

**Why?** Nginx sits in front of Gunicorn. It handles SSL (optional but recommended), serves static files instantly, and balances load.
**How?**

1.  Create Nginx config:
    ```bash
    sudo nano /etc/nginx/sites-available/itfintrack
    ```

2.  Content:
    ```nginx
    server {
        listen 80;
        server_name YOUR_SERVER_IP;

        location = /favicon.ico { access_log off; log_not_found off; }
        
        # Serve Static Files Directly
        location /static/ {
            root /var/www/itfintrack;
        }

        # Serve Media Files Directly
        location /media/ {
            root /var/www/itfintrack;
        }

        # Pass other requests to Gunicorn socket
        location / {
            include proxy_params;
            proxy_pass http://unix:/var/www/itfintrack/app.sock;
        }
    }
    ```

3.  Enable Site:
    ```bash
    sudo ln -s /etc/nginx/sites-available/itfintrack /etc/nginx/sites-enabled/
    sudo rm /etc/nginx/sites-enabled/default
    ```

4.  Restart Nginx:
    ```bash
    sudo nginx -t
    sudo systemctl restart nginx
    ```

## 8. Firewall (UFW)

**Why?** Security. Only allow necessary ports.
**How?**
```bash
sudo ufw allow 'Nginx Full'
```

---

**You're Live!**
Your app is now running in production with PostgreSQL.
