# Control Plane SDK for Python (cpln-py)

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyPI version](https://badge.fury.io/py/cpln-py.svg)](https://badge.fury.io/py/cpln-py)
[![codecov](https://codecov.io/gh/dave6892/cpln-py/graph/badge.svg?token=WRK7S1Z16G)](https://codecov.io/gh/dave6892/cpln-py)

A comprehensive Python library for interacting with the [Control Plane](https://controlplane.com) API. This SDK provides a Pythonic interface to manage GVCs (Global Virtual Clouds), workloads, images, and other Control Plane resources programmatically.

## Features

- **🚀 Easy-to-use client interface** - Simple Python client for Control Plane API
- **🔧 Workload Management** - Create, deploy, manage, and execute commands in workloads
- **🖼️ Image Management** - Handle container images in Control Plane registry
- **🌐 GVC Operations** - Manage Global Virtual Clouds and their configurations
- **⚡ WebSocket Support** - Real-time command execution with proper error handling
- **🔐 Authentication** - Secure API access with token-based authentication
- **🧪 Well-tested** - Comprehensive test suite with high coverage
- **📚 Type Hints** - Full type annotation support for better development experience

## Installation

### Using pip (when published):

```bash
pip install cpln-py
```

### Development Installation:

This project uses [PDM](https://pdm-project.org/) for dependency management:

```bash
# Clone the repository
git clone https://github.com/dave6892/cpln-py.git
cd cpln-py

# Install dependencies
make install

# Run examples to verify installation
pdm run python examples/example_cpln_gvc.py
pdm run python examples/example_cpln_images.py
pdm run python examples/example_cpln_workload.py
```

## Requirements

- Python 3.9+ (supports 3.9, 3.10, 3.11, 3.12, 3.13)
- Control Plane account with API access
- Service Account Key for authentication

## Quick Start

### 1. Authentication Setup

First, you'll need a Control Plane Service Account Key. See the [official documentation](https://docs.controlplane.com/reference/serviceaccount#service-account) for how to create one.

Create a `.env` file in your project:

```env
CPLN_TOKEN=your_service_account_key_here
CPLN_ORG=your_organization_name
CPLN_BASE_URL=https://api.cpln.io  # Optional, defaults to this
```

### 2. Basic Usage

```python
import cpln

# Initialize client from environment variables
client = cpln.CPLNClient.from_env()

# Or initialize with explicit parameters
client = cpln.CPLNClient(
    token="your_token_here",
    org="your_org_here",
    base_url="https://api.cpln.io"  # Optional
)
```

## Usage Examples

### Managing GVCs (Global Virtual Clouds)

```python
# List all GVCs
gvcs = client.gvcs.list()
for gvc in gvcs:
    print(f"GVC: {gvc.attrs['name']}")

# Get a specific GVC
gvc = client.gvcs.get("my-gvc")
print(f"GVC Details: {gvc.get()}")

# Create a new GVC
new_gvc = client.gvcs.model(
    attrs={"name": "test-gvc", "description": "Test GVC"}
)
new_gvc.create()

# Delete a GVC
gvc.delete()
```

### Managing Container Images

```python
# List all images in the registry
images = client.images.list()
for image in images:
    print(f"Image: {image.attrs['name']}")

# Get a specific image
image = client.images.get("my-image")
print(f"Image Details: {image.get()}")

# Delete an image
image.delete()
```

### Managing Workloads

```python
from cpln.config import WorkloadConfig

# List workloads in a GVC
workloads = client.workloads.list(gvc="my-gvc")
for name, workload in workloads.items():
    print(f"Workload: {name}")

# Get a specific workload
config = WorkloadConfig(gvc="my-gvc", workload_id="my-workload")
workload = client.workloads.get(config)

# Create a new workload
client.workloads.create(
    name="new-workload",
    gvc="my-gvc",
    description="A new workload",
    image="nginx:latest",
    container_name="web",
    workload_type="serverless"
)

# Execute commands in a workload
try:
    result = workload.exec("ls -la", location="aws-us-west-2")
    print(f"Command output: {result}")
except WebSocketExitCodeError as e:
    print(f"Command failed: {e}")

# Clone a workload
workload.clone(
    name="cloned-workload",
    gvc="target-gvc",
    workload_type="standard"
)

# Suspend/unsuspend workloads
workload.suspend()
workload.unsuspend()

# Get workload information
replicas = workload.get_replicas(location="aws-us-west-2")
containers = workload.get_containers(location="aws-us-west-2")
remote_url = workload.get_remote(location="aws-us-west-2")

# Ping a workload to check connectivity
ping_result = workload.ping(location="aws-us-west-2")
if ping_result["status"] == 200:
    print("Workload is responsive")
else:
    print(f"Workload ping failed: {ping_result['message']}")

# Export workload configuration
config_data = workload.export()
print(f"Workload config: {config_data}")
```

### Managing Containers (Workload-Centric)

```python
# List containers for a specific workload (workload-centric approach)
containers = client.containers.list(gvc="my-gvc", workload_name="my-workload")
for container in containers:
    print(f"Container: {container.name} ({container.image})")
    print(f"  Workload: {container.workload_name}")
    print(f"  Location: {container.location}")
    print(f"  Healthy: {container.is_healthy()}")

# List containers for specific workload in specific location
containers = client.containers.list(
    gvc="my-gvc",
    workload_name="my-workload",
    location="aws-us-west-2"
)

# Access containers through workloads (recommended pattern)
from cpln.config import WorkloadConfig

config = WorkloadConfig(gvc="my-gvc", workload_id="my-workload")
workload = client.workloads.get(config)
containers = workload.get_container_objects()

# Advanced container listing with caching, retry logic, and filtering (workload-centric)
from cpln.models.containers import AdvancedListingOptions

options = AdvancedListingOptions(
    enable_cache=True,
    cache_ttl_seconds=300,
    enable_retry=True,
    max_retries=3,
    filter_unhealthy=True
)

containers, stats = client.containers.list_advanced(
    gvc="my-gvc",
    workload_name="my-workload",
    options=options
)

print(f"Found {len(containers)} containers in {stats.duration_seconds:.2f}s")
print(f"API calls: {stats.api_calls_made}, Cache hits: {stats.cache_hits}")

# Count containers efficiently for a specific workload
count = client.containers.count_containers(gvc="my-gvc", workload_name="my-workload")
print(f"Total containers in workload: {count}")

# For multi-workload operations, iterate through workloads individually
workloads = client.workloads.list(gvc="my-gvc")
all_containers = []

for workload in workloads:
    workload_containers = workload.get_container_objects()
    all_containers.extend(workload_containers)
    print(f"Workload {workload.attrs['name']}: {len(workload_containers)} containers")

# Get container details
for container in containers:
    utilization = container.get_resource_utilization()
    if utilization["cpu"] or utilization["memory"]:
        print(f"Resource usage - CPU: {utilization['cpu']}%, Memory: {utilization['memory']}%")
```

### Advanced Workload Operations

```python
# Create workload with custom metadata
metadata = {
    "name": "custom-workload",
    "description": "Custom workload with specific configuration",
    "spec": {
        "type": "standard",
        "containers": [
            {
                "name": "app",
                "image": "my-app:latest",
                "env": [
                    {"name": "ENV", "value": "production"}
                ]
            }
        ],
        "defaultOptions": {
            "autoscaling": {
                "metric": "cpu",
                "minReplicas": 1,
                "maxReplicas": 10
            },
            "capacityAI": False
        }
    }
}

client.workloads.create(
    name="custom-workload",
    gvc="my-gvc",
    metadata=metadata
)
```

### Error Handling

```python
from cpln.errors import APIError, NotFound, WebSocketExitCodeError

try:
    # API operations
    workload = client.workloads.get(config)
    result = workload.exec("some-command", location="aws-us-west-2")
except NotFound:
    print("Resource not found")
except APIError as e:
    print(f"API error: {e}")
except WebSocketExitCodeError as e:
    print(f"Command execution failed with exit code {e.exit_code}: {e}")
```

## Configuration

### Environment Variables

The SDK supports the following environment variables:

- `CPLN_TOKEN`: Your Control Plane service account token (required)
- `CPLN_ORG`: Your organization name (required)
- `CPLN_BASE_URL`: API base URL (optional, defaults to `https://api.cpln.io`)

### Client Configuration

```python
# Custom timeout and other options
client = cpln.CPLNClient(
    token="your_token",
    org="your_org",
    base_url="https://api.cpln.io",
    timeout=30  # Custom timeout in seconds
)
```

## Development

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
pdm run pytest --cov=src/cpln

# Run specific test file
pdm run pytest tests/unit/cpln/models/test_workloads.py
```

### Code Quality

```bash
# Format code
pdm run ruff format src/ tests/

# Lint code
pdm run flake8 src/ tests/
pdm run ruff check src/ tests/

# Type checking
pdm run mypy src/
```

### Documentation

```bash
# Build and serve documentation
make docs
```

## API Reference

For detailed API documentation, see:

- [Control Plane API Documentation](https://docs.controlplane.com/api-reference/api)
- [SDK Documentation](./docs/) (when built locally)

## Architecture

The SDK is organized into several key components:

- **Client Layer** (`cpln.client`): High-level client interface
- **API Layer** (`cpln.api`): Low-level REST API client with authentication
- **Models** (`cpln.models`): Resource models for GVCs, Images, and Workloads
- **Utils** (`cpln.utils`): WebSocket communication, exit code handling, and utilities
- **Configuration** (`cpln.config`): Configuration management for different resource types

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass (`make test`)
6. Run code quality checks (`make lint` and `make format`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:

- 📖 Check the [Control Plane Documentation](https://docs.controlplane.com/)
- 🐛 [Report Issues](https://github.com/dave6892/cpln-py/issues)
- 💬 [Discussions](https://github.com/dave6892/cpln-py/discussions)

## Changelog

See [CHANGELOG.md](docs/change-log.md) for version history and changes.
