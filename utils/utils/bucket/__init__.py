from google.cloud import storage
import tarfile
import os
from pathlib import Path

def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    blob.download_to_filename(destination_file_name)

    print('Blob {} downloaded to {}.'.format(
        source_blob_name,
        destination_file_name))

def bucket_contains(filename):
    storage_client = storage.Client()
    blobs = storage_client.list_blobs("poloma-models")
    for blob in blobs:
        if blob == filename: return True
    return False

def download_and_unzip(bucket_name, source_blob_name, out_dir, archive=False):
    fname = source_blob_name.split("/")[-1]
    destination = out_dir + fname
    if not os.path.isfile(destination):
        download_blob(bucket_name, source_blob_name, destination)
    assert os.path.isfile(destination)
    if archive:
        tar = tarfile.open(destination, "r:gz")
        tar.extractall(out_dir)
        tar.close()
        print(f'extracted {destination} to {out_dir}')