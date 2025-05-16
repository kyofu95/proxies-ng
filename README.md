## Installation

**Note**: This project requires [docker and docker compose plugin](https://www.docker.com/get-started/) to be installed on your system.

#### 1. Clone the repository:
   ```sh
   git clone git@github.com:kyofu95/proxies-ng.git
   cd proxies-ng
   ```
#### 2. Download the GeoIP database
1. Create the `geoip` directory:
  ```sh
  mkdir geoip
  ```
2. Download the GeoIP database using curl:
  ```sh
  curl -LO --output-dir geoip/ https://git.io/GeoLite2-City.mmdb
  ```
#### 3. Configure Environment Variables
Create the .env file based on the provided example:
```sh
cp .env.sample .env
```
Pay special attention to the following variables:
- JWT_SECRET_KEY — secret key used for signing JWT tokens. It must be random and sufficiently long. You can generate one using:
  ```sh
  openssl rand -hex 16
  ```
- DOMAIN_NAME — domain name used for issuing TLS certificates. You should prepare this domain in advance. A simple and free option is to use duckdns.org.
- EMAIL — your email address, used for registering TLS certificates with Let's Encrypt.
- CORS_ORIGINS — origins allowed for CORS. Must be specified in JSON array format, e.g.:
   ```json
   ["https://mydomain.org"]
   ```
#### 4. Start the application using Docker Compose
For production:
```sh
docker compose --env-file .env -f docker-compose.yml up --build
```
For development:
```sh
docker compose --env-file .env -f docker-compose.dev.yml up --build 
```
**Note**: To run the development version locally, make sure to add the domain name used by the application (e.g. example.local) to your /etc/hosts file:
 ```sh
 127.0.0.1 example.local
 ```
**Note**: If you're running the development version, installation and setup are complete at this point.

#### 5. First Run
After the containers are up and running, you need to initialize the database schema and populate initial data.

1. Access the `fastapi_app` container:
```sh
docker exec -it fastapi_app bash
```
2. Apply database migrations using Alembic:
```sh
alembic upgrade head
```
3. Populate initial data:
```sh
python3 -m app.init_data
```
This command fills lookup tables and creates a default administrative user.
By default, the admin account will be created with login: admin and password: admin
Please change these credentials immediately after the first login to ensure security.
You can override the default credentials by setting the environment variables ADMIN_LOGIN and ADMIN_PASSWORD before running the command. For example:
```sh
ADMIN_LOGIN=superadmin ADMIN_PASSWORD=strongpassword python3 -m app.init_data
```

## Testing
**Note**: Before running the tests, you need to download the GeoIP database. Refer to Installation.

This project uses `pytest` for testing. Tests are categorized into unit tests and integration tests.

### Running Unit Tests
Unit tests are marked with `unit` and can be executed in two ways:
- By using the marker:
  ```sh
  pytest -m unit
  ```
- By running tests from the tests/unit directory:
  ```sh
  pytest tests/unit
  ```

### Running Integration Tests
Integration tests are marked with `integration` and can be executed in two ways:
- By using the marker:
  ```sh
  pytest -m integration
  ```
- By running tests from the tests/unit directory:
  ```sh
  pytest tests/integration
  ```
Integration tests use testcontainers to provide real service dependencies, making them slower than unit tests.
