import cpln

client = cpln.from_env()
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
for workload in client.workloads.list(gvc):
    print(workload)
