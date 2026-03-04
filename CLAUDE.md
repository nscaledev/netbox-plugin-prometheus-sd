g# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A NetBox plugin that exposes Prometheus HTTP Service Discovery (http_sd) compatible API endpoints. NetBox objects (devices, VMs, services, IP addresses) are serialized into Prometheus target groups with `__meta_netbox_*` labels.

## Development Commands

All tasks use the [invoke](https://www.pyinvoke.org/) task runner. NetBox version is controlled via `NETBOX_VER` env var (default: `latest`; tested: `v4.0.11`, `v4.1.11`, `v4.2.5`).

```bash
# Build Docker image
invoke build [--netbox-ver=v4.2.5]

# Run all tests (spins up containers)
invoke tests [--netbox-ver=v4.2.5]

# Local dev environment
invoke start    # detached
invoke debug    # interactive (logs visible)
invoke stop
invoke destroy  # also removes volumes

# Utilities (requires running containers)
invoke cli       # bash shell in NetBox container
invoke nbshell   # NetBox management shell
invoke create-user
```

Linting uses flake8 (max 130 chars) and black (via pre-commit). Run pre-commit manually with:
```bash
pre-commit run --all-files
```

## Architecture

### Plugin Entry Point

`netbox_prometheus_sd/__init__.py` — defines the `PrometheusSD` plugin config class. No required or default settings.

### API Layer (`netbox_prometheus_sd/api/`)

- **`views.py`**: Four read-only ViewSets (`DeviceViewSet`, `VirtualMachineViewSet`, `ServiceViewSet`, `IPAddressViewSet`). Pagination is disabled for Prometheus compatibility. Reuses NetBox's authentication and RBAC.
- **`serializers.py`**: Converts NetBox model instances to Prometheus target group format: `{"targets": [...], "labels": {...}}`. `SDConfigContextDuplicateSerializer` duplicates an object once per config context entry (to support multi-port scraping).
- **`utils.py`**: Label extraction functions that pull NetBox attributes into `__meta_netbox_*` Prometheus labels. Special chars in label names are replaced with underscores.
- **`urls.py`**: Routes the four endpoints under `/api/plugins/prometheus-sd/`.

### Filtersets (`filtersets.py`)

Extends NetBox's native filtersets:
- `ServiceFilterSet`: adds tenant filtering by slug/ID across device/VM parent relationships
- `DeviceFilterSet`: adds case-insensitive cluster name filtering

### Config Context Integration

Devices/VMs can embed per-object Prometheus config in their NetBox config context:
```yaml
prometheus-plugin-prometheus-sd:
  - metrics_path: /custom/metrics
    port: 9100
    scheme: https
```
If a list, the object is duplicated once per entry (enabling multi-port monitoring). This emits `__metrics_path__` and `__scheme__` labels (without the `__meta_netbox_` prefix).

### NetBox Version Compatibility

The plugin supports NetBox 4.0+. `views.py` and `utils.py` use `try/except` imports to handle API changes across versions:
- ViewSet base class names changed across versions
- FilterSet module path changed (`filters` → `filtersets`)
- Device role renamed `device_role` → `role` (v3.6+)
- Cluster scope changed from `site` FK to `scope` GenericFK (v4.2+)

## Testing

Tests run inside Docker against a real NetBox instance (not mocked). The test suite is in `netbox_prometheus_sd/tests/`:
- `test_api.py` — endpoint integration tests
- `test_serializers.py` — primary test coverage for label output
- `test_filtersets.py` — filter parameter tests
- `test_utils.py` — utility function tests
- `utils.py` — fixture builders (`build_device_full`, `build_vm_full`, `build_full_ip`)

To run a single test module, exec into the container directly:
```bash
invoke start
docker compose -f develop/docker-compose.yml -p netbox_prometheus_sd exec netbox \
  python manage.py test netbox_prometheus_sd.tests.test_serializers --keepdb
```

## Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/). Semantic release reads commit messages to bump versions and update `__VERSION__` in `__init__.py`.