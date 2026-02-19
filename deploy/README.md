Production deploy notes
----------------------

Place the project on the server under `/srv/itfintrack` and create a secure `.env` there with `SECRET_KEY`, DB and ALLOWED_HOSTS values.

Quick install steps on Ubuntu server:

```bash
# clone into /srv
sudo mkdir -p /srv/itfintrack
sudo chown $USER /srv/itfintrack
cd /srv/itfintrack
git clone <your-repo-url> .

# create .env (example)
cp .env.example .env
# edit .env with production values

# start services
sudo docker compose -f docker-compose.prod.yml up -d --build

# run management tasks
sudo docker compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput
sudo docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# register systemd service so stack starts on reboot
sudo cp deploy/itfintrack.service /etc/systemd/system/itfintrack.service
sudo systemctl daemon-reload
sudo systemctl enable --now itfintrack.service
```

Notes:
- Ensure `docker` and `docker compose` are installed on the server.
- Keep `.env` out of source control.
- `staticfiles` and `media` are Docker volumes; confirm backups for `pgdata` volume.
