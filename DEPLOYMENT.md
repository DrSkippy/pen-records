# Pen Records

## Host PostgreSQL setup

Create a URL-safe password, then create the application role and database on the host:

```sh
openssl rand -hex 32
sudo -u postgres psql
```

```sql
CREATE ROLE pens LOGIN PASSWORD 'paste-generated-password';
CREATE DATABASE pens OWNER pens;
\q
```

PostgreSQL must listen on the host's Docker bridge interface. Set `listen_addresses` appropriately in `postgresql.conf`. Create the Compose network with `docker compose create`, inspect its subnet with `docker network inspect pen-records_default`, and add that exact subnet to `pg_hba.conf`, for example:

In `postgresql.conf`, allow PostgreSQL to listen on the Docker bridge as well as localhost. Using `*` is simplest, provided the host firewall keeps port 5432 closed to external networks:

```conf
listen_addresses = '*'
```

In `pg_hba.conf`, add an access line using the actual subnet reported by `docker network inspect`:

```conf
host    pens    pens    172.18.0.0/16    scram-sha-256
```

The fields are database, role, Docker subnet, and authentication method respectively. Do not copy `172.18.0.0/16` unless it matches the network inspection output. Restart PostgreSQL after changing either configuration file. Keep port 5432 blocked from external networks; it only needs to be reachable from the Docker bridge and localhost.

## Application setup

1. Copy `.env.example` to `.env` and set `POSTGRES_PASSWORD` to the role password. Adjust the database name, user, or port if the host uses non-default values.
2. Ensure `PENS_IMAGE_HOST_DIR` exists and is writable by the API container.
3. Validate with `docker compose config --quiet`.
4. Run `docker compose pull` followed by `docker compose up -d`. The API connects through `host.docker.internal` and applies Alembic migrations to the host database before starting.
5. Check `docker compose logs --tail=100 api` and request `http://127.0.0.1:8070/api/v1/health`.
6. Import the source data once:
   `docker compose exec api uv run pen-records "import_data/Pen Collection - Pen Data.csv"`.
   Re-running the command skips identical rows and reports any legacy image download failures.
7. Browse to `http://127.0.0.1:8070`. API documentation is available at `/api/docs`.

## Production

Use `deploy/nginx-host.conf.example` as the basis for the two TLS virtual hosts. Only the web container is bound to loopback; the API remains on the Compose network. Restrict the HTTPS origin to Cloudflare traffic so Cloudflare Access cannot be bypassed.

Back up both durable stores:

```sh
PGPASSWORD="$(sed -n 's/^POSTGRES_PASSWORD=//p' .env)" \
  pg_dump -h 127.0.0.1 -U pens -Fc pens > pens.dump
tar -C /var/www/html/resources -czf pen-images.tar.gz pens
```

Restore with `pg_restore --clean --if-exists -h 127.0.0.1 -U pens -d pens pens.dump`, then restore the image archive before starting the API.

## Development

- API: `uv sync`, set `PENS_DATABASE_URL`, then run `uv run alembic upgrade head` and `uv run uvicorn pen_records.main:app --reload`.
- UI: from `frontend`, run `npm install` followed by `npm run dev`.
- Tests: `uv run pytest` and `npm run build`.

## Importing local images

Place source images under `import_data/images` and map them in `import_data/images/manifest.csv`. Each manifest row identifies a filename, maker, model, optional acquisition date, caption, and display order. Paths may use nested directories under `images` but cannot escape that directory.

After adding or changing local images, rerun the existing import without remote downloads:

```sh
docker compose exec api uv run pen-records \
  "import_data/Pen Collection - Pen Data.csv" \
  --no-download-images
```

Existing pens are not recreated. Missing local images are converted to managed WebP files, attached to matching records, and reported as `local_images_added`. Repeated runs report them as `local_images_skipped` instead of creating duplicates. Review `local_image_failures` for missing or invalid files.
