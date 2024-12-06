# %%
import os

import ee
import ee.data

from buckets import (
    create_bucket,
    upload_bucket_to_ee,
    upload_directory,
)

ee.Authenticate()
ee.Initialize(project="unicef-geospatial")

bucket_name = "unicef-geospatial-ee"
project_id = "unicef-geospatial"
data_dir = "./data"
bucket_directory = "heatwaves"
ee_root_path = "projects/unicef-geospatial/assets"

# %%

bucket = create_bucket(bucket_name, project_id)
upload_directory(bucket_name, data_dir, bucket_directory, project_id)
# %%

tasks = upload_bucket_to_ee(bucket_name, project_id, ee_root_path)


import time

finished = [False] * len(tasks)
while not all(finished):
    for i, task in enumerate(tasks):
        status = ee.data.getTaskStatus(task["id"])[0]
        if status["state"] == "COMPLETED" or status["state"] == "FAILED":
            finished[i] = True
        if status["state"] == "FAILED":
            print(status)
    time.sleep(5)
# %%
