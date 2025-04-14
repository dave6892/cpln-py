import cpln
from cpln.errors import APIError


client = cpln.from_env()
client = cpln.CPLNClient(
    token=client.api.config.token,
    org=client.api.config.org,
)
print(client)

print("GVCs in my control plane:")
for gvc in client.gvcs.list():
    print(gvc)

print()
print("images in my control plane:")
for image in client.images.list():
    print(image)

gvc = 'apalis-dev'
print()
print(f"Workload in my control plane GVC {gvc}:")
for workload in (workloads:=client.workloads.list(gvc)):
    print(workload)


workload_name = "insurance-api-standard"
workloads[workload_name].suspend(False) # unsuspending the workload

while True:
    try:
        workloads[workload_name].ping(location="aws-us-west-2")
        print(f"Workload (workloads{[workload_name]}) is up and running!")
        break
    except APIError as e:
        print("Retrying...")
        continue

workloads[workload_name].exec(
    command="echo hello world",
    location="aws-us-west-2",
)

workloads[workload_name].suspend(True)