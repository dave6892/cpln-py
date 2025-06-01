import time
import cpln
from cpln.errors import (
    APIError,
    WebSocketExitCodeError,
    WebSocketOperationError,
    WebSocketConnectionError,
)


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


workload_name = "test-clone"
location = "aws-us-west-2"
gvc = "apalis-dev"

# client.workloads.create(
#     name=workload_name,
#     gvc = gvc,
#     metadata_file_path="./ledgestone_apalis-dev_workloads.json",
# )

tmp = client.workloads.get(
    cpln.config.WorkloadConfig(
        gvc='apalis-dev',
        workload_id='broker-dashboard-api',
        location=location,
    )
)

tmp.clone(
    name=workload_name,
    gvc=gvc,
)

# # workloads[workload_name].unsuspend() # unsuspending the workload
workloads = client.workloads.list(gvc)
print(workloads[workload_name])
while True:
    response = workloads[workload_name].ping(location=location)
    if response["status"] == 200:
        print(f"Workload (workloads{[workload_name]}) is up and running!")
        break
    else:
        print(f"Workload (workloads{[workload_name]}) is down ({response['message']}, {response['exit_code']}). Retrying...")
        time.sleep(1)
        continue

workloads[workload_name].exec(
    command="echo hello world",
    location=location,
)


# # # try:
# # #     workloads[workload_name].exec(
# # #         command="aws s3 tmp",
# # #         location=location,
# # #     )
# # # except WebSocketExitCodeError as e:
# # #     print(f"Command failed with exit code: {e}")
# # # except Exception as e:
# # #     print(f"Unexpected error occurred: {e}")
# # # else:
# # #     print("Command executed successfully")
# # # finally:
# # #     print("Cleaning up...")
# # #     workloads[workload_name].suspend()


tmp = client.workloads.get(
    cpln.config.WorkloadConfig(
        gvc=gvc,
        workload_id=workload_name,
        location=location,
    )
)

tmp.delete()