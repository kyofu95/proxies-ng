## Installation

Note: To run the development version locally, make sure to add the domain name used by the application (e.g. example.local) to your /etc/hosts file:
 ```sh
 127.0.0.1 example.local
 ```

Before running the tests, you need to download the GeoIP database.

1. Create the `geoip` directory:
  ```sh
  mkdir geoip
  ```
2. Download the GeoIP database using curl:
  ```sh
  curl -LO --output-dir geoip/ https://git.io/GeoLite2-City.mmdb
  ```

## Testing

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