# Contribution guidelines

Contributing to this project should be as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

## Github is used for everything

Github is used to host code, to track issues and feature requests, as well as accept pull requests.

Pull requests are the best way to propose changes to the codebase.

1. Fork the repo and create your branch from `main`.
2. If you've changed something, update the documentation.
3. Make sure your code passes all checks (see below).
4. Test your contribution.
5. Issue that pull request!

## Development Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=custom_components/eaton_ups_mqtt --cov-branch

# Format code
uv run ruff format .

# Lint and auto-fix
uv run ruff check . --fix

# Type check
uv run ty check

# Full pre-commit check
uv run pytest && uv run ruff format . && uv run ruff check . --fix && uv run ty check
```

## Use a Consistent Coding Style

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting. All code must pass:

- `uv run ruff check .` - Linting
- `uv run ruff format . --check` - Formatting
- `uv run ty check` - Type checking

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](../../issues)

GitHub issues are used to track public bugs.
Report a bug by [opening a new issue](../../issues/new/choose); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People *love* thorough bug reports. I'm not even kidding.

## Test your code modification

This custom component is based on [integration_blueprint template](https://github.com/ludeeus/integration_blueprint).

It comes with development environment in a container, easy to launch
if you use Visual Studio Code. With this container you will have a stand alone
Home Assistant instance running and already configured with the included
[`configuration.yaml`](./config/configuration.yaml)
file.

## Contributing Test Fixtures

To capture MQTT data from your UPS for test fixtures:

```bash
# 1. Capture raw data (requires TLS certs from UPS web interface)
uv run python scripts/dump_mqtt_data.py \
  --host YOUR_UPS --server-cert ca.pem --client-cert client.pem \
  --client-key client.key --output tests/fixtures/raw_ups_data.json

# 2. Sanitize PII (serial numbers, MACs, UUIDs, dates)
uv run python scripts/sanitize_fixture.py \
  --input tests/fixtures/raw_ups_data.json \
  --output tests/fixtures/mqtt_data_YOUR_MODEL.json

# 3. Delete raw data and submit PR with sanitized fixture
rm tests/fixtures/raw_ups_data.json
```

Existing fixtures: `mqtt_data_5px_g2.json` (Eaton 5PX 1500i RT2U G2)

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
