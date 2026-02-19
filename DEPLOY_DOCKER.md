# Deploying IT-FIN-Track with Docker on Ubuntu

This guide shows how to deploy the IT-FIN-Track Django app using Docker and Docker Compose on an Ubuntu server.

High-level steps
- Prepare the Ubuntu host (install Docker, Docker Compose)
- Clone the repository and add environment variables
- Build and run containers (web + postgres + optional nginx)
- Run migrations, create superuser, collect static files
- Configure firewall / reverse proxy (optional)

Prerequisites
- Ubuntu 20.04/22.04/24.04 server with a non-root user that has sudo
- Domain name (optional) for production and TLS termination
- Ports: 80/443 (if using nginx), 8000 (dev server)

1 — Install Docker & Docker Compose plugin
Run the following on the Ubuntu server:

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Optional: allow your user to run docker without sudo
sudo usermod -aG docker $USER
newgrp docker
docker --version
```

2 — Clone repository and create `.env`

```bash
git clone <your-repo-url> it-fin-track
cd it-fin-track/IT-FIN-Track

# Create .env in the project root (example below)
cat > .env <<EOF
SECRET_KEY=change-this-to-a-strong-secret
DEBUG=False
ALLOWED_HOSTS=your.domain.com,localhost,127.0.0.1
DB_NAME=itfintrack_db
DB_USER=itfintrack_user
DB_PASSWORD=change_db_password
DB_HOST=db
DB_PORT=5432
EOF
```

3 — Example `Dockerfile` for the Django app

Create a `Dockerfile` in the project root (if you prefer the repository-managed file):

```dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

# system deps for Pillow, psycopg2, etc
RUN apt-get update && apt-get install -y build-essential libpq-dev gcc libjpeg-dev zlib1g-dev --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "itfintrack.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

4 — Example `docker-compose.yml`

Create `docker-compose.yml` in the project root:

```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data

  web:
    build: .
    restart: always
    env_file: .env
    depends_on:
      - db
    volumes:
      - .:/app:cached
    ports:
      - "8000:8000"
    command: gunicorn itfintrack.wsgi:application --bind 0.0.0.0:8000 --workers 3

  # Optional: nginx as reverse proxy (recommended for production)
  nginx:
    image: nginx:stable
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deploy/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - web

volumes:
  pgdata:
```

5 — Build and start containers

```bash
# build and run in detached mode
docker compose up -d --build

# check logs
docker compose logs -f web
```

6 — Run migrations, create superuser, collectstatic

```bash
docker compose exec web python manage.py migrate --noinput
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py collectstatic --noinput
```

7 — (Optional) Nginx config and TLS
- Create an `nginx` configuration that proxies to `web:8000` and terminate TLS with Certbot.
- You can use `certbot` on the host and mount certificates into the `nginx` container.

8 — Security & production notes
- Set `DEBUG=False` and strong `SECRET_KEY` in `.env`.
- Use a managed/postgres service for production if you prefer.
- Back up Postgres volume `pgdata` regularly.

9 — Common troubleshooting
- `psycopg2` build errors: The `Dockerfile` installs `libpq` and `libpq-dev` system deps to build psycopg2. If you still hit issues, ensure the base image provides build tools (we use `build-essential` + `libpq-dev`).
- Permission issues: ensure Docker volumes mount with appropriate permissions; you may need to adjust UID/GID for files created by the container.

10 — Useful commands

```bash
# Stop containers
docker compose down

# Rebuild if you change Dockerfile
docker compose build --no-cache web

# Inspect logs
docker compose logs -f
```

If you want, I can:
- add the `Dockerfile` and `docker-compose.yml` to the repo
- create a minimal `deploy/nginx.conf` example
- produce a systemd unit that brings the compose stack up on boot

Tell me which of the above you'd like me to add to the repository and I will update the TODOs and files.
