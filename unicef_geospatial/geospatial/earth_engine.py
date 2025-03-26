import os
from typing import List

import ee
from geospatial.demographic import get_children_population_metadata
from geospatial.floods import (
    get_coastal_flood_metadata,
    get_pluvial_flood_metadata,
    get_river_flood_metadata,
)
from geospatial.storms import get_storm_metadata
from google.cloud import storage
from google.cloud.storage.bucket import Bucket
from logging_config import get_logger
from utils.types import ALL_DATASETS, DatasetMetadata

logger = get_logger(__name__)


def get_dataset_metadata(dataset: ALL_DATASETS) -> DatasetMetadata:
    """Get metadata for a dataset.

    Args:
        dataset: The dataset to get metadata for

    Returns:
        DatasetMetadata: The metadata for the specified dataset
    """
    logger.info(f"Getting metadata for dataset: {dataset}")
    match dataset:
        case "river_flood":
            metadata = get_river_flood_metadata()
        case "coastal_flood":
            metadata = get_coastal_flood_metadata()
        case "pluvial_flood":
            metadata = get_pluvial_flood_metadata()
        case "tropical_storm":
            metadata = get_storm_metadata()
        case "children_population":
            metadata = get_children_population_metadata()
        case _:
            raise ValueError(f"Dataset {dataset} not supported")

    metadata.input_arguments = {"dataset": dataset}
    return metadata


def create_bucket(bucket_name: str, project_id: str) -> Bucket:
    """Create a new bucket in Google Cloud Storage.

    Creates a new bucket with COLDLINE storage class in the US region.

    Args:
        bucket_name: Name of the bucket to create
        project_id: Google Cloud project ID

    Returns:
        The created bucket object

    Example:
        >>> bucket = create_bucket("my-bucket", "my-project")
        Created bucket my-bucket in us with storage class COLDLINE
    """
    storage_client = storage.Client(project=project_id)

    bucket = storage_client.bucket(bucket_name)
    bucket.storage_class = "COLDLINE"
    new_bucket = storage_client.create_bucket(bucket, location="us")

    return new_bucket


def upload_blob(
    bucket_name: str, source_file_name: str, destination_blob_name: str, project_id: str
) -> None:
    """Upload a file to Google Cloud Storage bucket.

    Args:
        bucket_name: Name of the destination bucket
        source_file_name: Local path to the file to upload
        destination_blob_name: Path to store the file in the bucket
        project_id: Google Cloud project ID
    """
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"(upload_blob) File {source_file_name} uploaded to {destination_blob_name}.")


def upload_directory(
    bucket_name: str, source_dir: str, destination_dir: str, project_id: str
) -> None:
    """Recursively upload a directory to Google Cloud Storage bucket.

    Preserves the directory structure when uploading to the bucket.

    Args:
        bucket_name: Name of the destination bucket
        source_dir: Local directory path to upload
        destination_dir: Directory path in the bucket to store files
        project_id: Google Cloud project ID
    """
    print(f"(upload_directory) Uploading {source_dir} to {destination_dir}")
    for item in os.listdir(source_dir):
        source_path = os.path.join(source_dir, item)
        destination_path = os.path.join(destination_dir, item)

        if os.path.isfile(source_path):
            print(
                f"(upload_directory) 1) Uploading {source_path} to {destination_path}"
            )
            upload_blob(
                bucket_name,
                source_path,
                destination_path,
                project_id,
            )
        elif os.path.isdir(source_path):

            upload_directory(
                bucket_name,
                source_path,
                os.path.join(destination_dir, item),
                project_id,
            )


def upload_to_ee_from_gcs(
    bucket_name: str, blob_name: str, ee_asset_path: str, project_id: str
) -> dict:
    """Upload a file from Google Cloud Storage to Earth Engine.

    Args:
        bucket_name: Name of the GCS bucket containing the file
        blob_name: Name/path of the file in the bucket
        ee_asset_path: Destination path in Earth Engine where the asset will be created
        project_id: Google Cloud project ID

    Returns:
        Task object representing the Earth Engine ingestion task

    Raises:
        FileNotFoundError: If the specified file does not exist in the GCS bucket
    """
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    if not blob.exists():
        raise FileNotFoundError(
            f"File not found in GCS: gs://{bucket_name}/{blob_name}"
        )

    gcs_path = f"gs://{bucket_name}/{blob_name}"

    params = {
        "name": ee_asset_path,
        "tilesets": [{"sources": [{"uris": [gcs_path]}]}],
    }

    task_id = ee.data.newTaskId()[0]

    task = ee.data.startIngestion(
        request_id=task_id, params=params, allow_overwrite=False
    )

    print(f"Started ingestion from {gcs_path} to {ee_asset_path}")
    return task


def create_ee_asset_path(ee_root_path: str, blob_name: str) -> str:
    """Create directory structure in Earth Engine for asset upload.

    Args:
        ee_root_path: Root path in Earth Engine where directories will be created
        blob_name: Name of the blob/file to determine directory structure

    Returns:
        The created directory path in Earth Engine
    """
    directory = os.path.dirname(blob_name)
    ee_directory = os.path.join(ee_root_path, directory)

    try:
        ee.data.createAsset({"type": "FOLDER"}, ee_directory)
        print(f"Created directory: {ee_directory}")
    except ee.ee_exception.EEException:
        # Directory already exists
        pass


def upload_bucket_to_ee(
    bucket_name: str, project_id: str, ee_root_path: str
) -> List[dict]:
    """Upload all files from a GCS bucket to Earth Engine.

    Maintains the directory structure when uploading files to Earth Engine.

    Args:
        bucket_name: Name of the source GCS bucket
        project_id: Google Cloud project ID
        ee_root_path: Root path in Earth Engine where assets will be created

    Returns:
        List of task objects representing Earth Engine ingestion tasks
    """
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    tasks = []
    for blob in bucket.list_blobs():
        file_name = blob.name.split(".")[0]

        asset_path = create_ee_asset_path(ee_root_path, file_name)

        print(f"Uploading {blob.name} to {asset_path}")

        task = upload_to_ee_from_gcs(
            bucket_name,
            blob.name,
            os.path.join(ee_root_path, file_name),
            project_id,
        )
        tasks.append(task)

    return tasks
