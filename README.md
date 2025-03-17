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