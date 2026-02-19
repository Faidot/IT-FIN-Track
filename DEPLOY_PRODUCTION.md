# IT-FIN-Track — Docker Production Deployment

This guide shows step-by-step how to containerize and deploy the IT-FIN-Track Django app with Docker and Docker Compose for production on an Ubuntu server.

Prerequisites
- A development machine (Mac/Windows) with Docker installed
- An Ubuntu server with sudo access
- A domain name you control (optional but recommended)

IMPORTANT: Keep secrets out of the repo. Use a `.env` file on the server and never commit it.

PART 1 — Local Docker setup (build and test locally)

1. Deactivate any virtualenv:

```bash
deactivate
```

2. Create `requirements.txt` (either automatically or manually):

```bash
pip freeze > requirements.txt
# or create minimal requirements with:
# Django
# gunicorn
# psycopg2-binary
```

3. Create a simple `Dockerfile` (example):

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "itfintrack.wsgi:application", "--bind", "0.0.0.0:8000"]
```

4. Create `docker-compose.yml` (example):

```yaml
version: "3.9"
services:
  db:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: myuser
      POSTGRES_PASSWORD: mypassword
    volumes:
      - postgres_data:/var/lib/postgresql/data/

  web:
    build: .
    command: gunicorn itfintrack.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
    restart: always

volumes:
  postgres_data:
```

5. (Optional) Update `itfintrack/settings.py` to use Postgres when testing with Docker:

```python
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'mydb'),
        'USER': os.getenv('DB_USER', 'myuser'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'mypassword'),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', 5432),
    }
}

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

6. Build and run locally:

```bash
docker-compose build
docker-compose up
# in another terminal
docker-compose exec web python manage.py migrate
```

Open `http://localhost:8000` to verify.

PART 2 — Prepare for Production (do not expose port 8000 publicly)

1. Update `docker-compose.yml` to make the app internal and add `nginx` as reverse proxy:

```yaml
version: "3.9"
services:
  db: # same as before
  web:
    build: .
    command: gunicorn itfintrack.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    expose:
      - "8000"
    depends_on:
      - db
    restart: always

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx:/etc/nginx/conf.d
      - ./staticfiles:/static
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    depends_on:
      - web
    restart: always

volumes:
  postgres_data:
```

2. Create `nginx/default.conf` with proxy and static settings (example):

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /static/ {
        alias /static/;
    }

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. Rebuild the stack (local test or server):

```bash
docker-compose down
docker-compose up -d --build
docker-compose exec web python manage.py migrate --noinput
docker-compose exec web python manage.py collectstatic --noinput
```

PART 3 — Deploy to Ubuntu server

On your Mac (or dev machine):

```bash
git init
git add .
git commit -m "Add Docker production deployment"
git remote add origin <your-git-remote>
git push -u origin main
```

On your Ubuntu server:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose git
git clone <your-repo-url> myproject
cd myproject
# create a secure .env with SECRET_KEY, DB_* values, ALLOWED_HOSTS
docker-compose up -d --build
docker-compose exec web python manage.py migrate --noinput
docker-compose exec web python manage.py collectstatic --noinput
```

Then open `http://server-ip` to confirm.

PART 4 — Use a domain and enable HTTPS (Let's Encrypt)

1. Point your domain A records to the server IP (root and www).

2. Stop nginx container and obtain certificates via certbot:

```bash
docker compose stop nginx
sudo apt install -y certbot
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

3. Update `nginx/default.conf` to redirect HTTP -> HTTPS and serve certificates:

```nginx
server { listen 80; server_name yourdomain.com www.yourdomain.com; return 301 https://$host$request_uri; }

server {
  listen 443 ssl;
  server_name yourdomain.com www.yourdomain.com;
  ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
  location /static/ { alias /static/; }
  location / { proxy_pass http://web:8000; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; }
}
```

4. Start containers again:

```bash
docker-compose up -d
```

5. Auto-renew certbot (crontab):

```bash
sudo crontab -e
# add line:
0 3 * * * certbot renew --quiet
```

Production Checklist
- Set `DEBUG=False` and `ALLOWED_HOSTS=['yourdomain.com']` in `.env` or settings
- Use strong `SECRET_KEY`
- Persist Postgres data with Docker volume
- Use `restart: always` and a systemd unit if desired to auto-start compose on boot
- Monitor logs: `docker-compose logs -f`

Notes about architecture and cross-arch builds
- If building on Apple Silicon and deploying to x86_64 server, use `docker buildx` to build linux/amd64 images or build on an x86 machine.

Transfer options
- Push the image to Docker Hub or GitHub Container Registry and `docker pull` on the server
- Or `docker save` → `scp` → `docker load` on the server (less convenient for CI)

If you want, I can add CI (GitHub Actions) config to build multi-arch images and push to a registry automatically.

🔹 Quick deploy workflow (Mac -> Ubuntu server)

STEP 1 — On Mac

Make changes locally, test and push:

```bash
# test locally
docker-compose up

# if working
git add .
git commit -m "Feature update"
git push origin main
```

STEP 2 — On Ubuntu Server

SSH into the server and pull latest code:

```bash
ssh user@server-ip
cd myproject
git pull origin main
```

STEP 3 — Build new version

```bash
docker-compose up -d --build
```

What happens internally:
- New web container built
- Old web container stopped
- New one started
- DB container untouched
- Nginx untouched

Downtime is typically 3–5 seconds.

STEP 4 — Run migrations (if models changed)

```bash
docker-compose exec web python manage.py migrate
```

STEP 5 — Collect static (if needed)

```bash
docker-compose exec web python manage.py collectstatic --noinput
```

Why this is safe

Because you did NOT run `docker-compose down -v` — the Postgres volume remains, only the web container is recreated, and data is preserved.

