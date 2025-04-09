# Control Plane SDK for Python (Developer Edition)

A Python library for the [Control Plane](https://controlplane.com) API. It lets you do many things the `cpln` command does within Python -- execute commands in workloads, manage workloads, manage images, manage containers, etc.

For more information about the API, [see here](https://docs.controlplane.com/api-reference/api).

## Installation

This project is structured using the package and depencies manager [PDM](https://pdm-project.org/en/latest/). To install the dependencies for this project:
```bash
pdm install
```

Run the following script to make sure everything is running fine.
```bash
pdm run main.py
```

## Getting started

### Get the API key
I use the Service Account Key to access the use of the API

See [the documentation](https://docs.controlplane.com/reference/serviceaccount#service-account) to learn how to create one.

### Setup the environment
There are two variables required in the project `.env` file

- `CPLN_TOKEN`: The API access key.

- `CPLN_ORG`: The organization namespace of your control plane service.

### Starting of example
To connect to the Control Plane API, you must first instantiate a client. You can do this by using the `CPLNClient` class:

```python
import os
import cpln
client = cpln.CPLNClient(
	token=os.environ.get("CPLN_TOKEN"),
	org=os.environ.get("CPLN_ORG"),
)
```
or the confirguration in environment:
```python
client = cpln.from_env()
```

You can manage GVCs:
```python
client.gvcs.list()
```

You can manage images in the Control Plane registry:
```python
client.images.list()
```

You can also manage workloads:
```python
gvc = 'test_gvc'
workload_name = 'test_workload'

# You can get a list of workloads in the specified GVC
workloads = client.workloads.list(gvc)

# Once you have the workload, you can execute commands from the workload
workloads[workload_name].exec_workload(
	config=WorkloadConfig(
		gvc=gvc
		workload_id=workload_name
		location='aws-us-west-2'
	),
	command=["echo", "hello", "world"]
)
```
That’s just a glimpse of what you can do with the Control Plane SDK for Python. For more, take a look at the reference.