import cpln

client = cpln.from_env()
client = cpln.CPLNClient(
    token=client.api.config.token,
    org=client.api.config.org,
    # base_url=client.api.config.base_url,
    # version=client.api.config.version,
    # timeout=client.api.config.timeout,
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


print(workloads["insurance-api-standard"])