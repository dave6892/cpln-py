import time
import cpln
from cpln.errors import APIError, WebSocketExitCodeError


client = cpln.from_env()
client = cpln.CPLNClient(
    token=client.api.config.token,
    org=client.api.config.org,
)
print(client)

# print("GVCs in my control plane:")
# for gvc in client.gvcs.list():
#     print(gvc)

# print()
# print("images in my control plane:")
# for image in client.images.list():
#     print(image)

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
        time.sleep(1)
        continue

workloads[workload_name].exec(
    command="echo hello world",
    location="aws-us-west-2",
)


try:

    workloads[workload_name].exec(
        command="aws s3 cp /var/local/storage/tmp.dump s3://apalis-postgres-backup/apalis_playground/tmp_test/postgres_backup.dump",
        location="aws-us-west-2",
    )
except WebSocketExitCodeError as e:
    print(f"Got the error {e}")


workloads[workload_name].suspend(True)