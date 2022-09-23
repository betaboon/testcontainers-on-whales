import pathlib

import botocore
import pytest

from testcontainers_on_whales.minio import MinioContainer


def test_minio_container_default():
    with MinioContainer() as minio:
        minio.wait_ready(timeout=120)
        minio.get_bucket("test")


def test_minio_container_extra_env():
    user = "root"
    passwd = "samplepass"
    # Anti pattern, don't overwrite user/pass via env in real life
    extra_env = {
        "MINIO_ROOT_USER": user,
        "MINIO_ROOT_PASSWORD": passwd,
    }
    with MinioContainer(extra_env=extra_env) as minio:
        minio.wait_ready(20)
        with pytest.raises(botocore.exceptions.ClientError):
            # credentials are wrong as we overwrote them via env
            minio.get_bucket("sample")
            assert False


def test_minio_container_with_upload_download():
    with MinioContainer() as minio:
        minio.wait_ready(timeout=120)
        bucket = minio.get_bucket("test")
        its_me = pathlib.Path(__file__).resolve()
        target_key = its_me.name

        bucket.upload_file(str(its_me), target_key)
        object = bucket.Object(target_key)
        object.get()  # might raise if not found
        assert object.key == target_key
