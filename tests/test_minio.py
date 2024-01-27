import pathlib

from testcontainers_on_whales.minio import MinioContainer


def test_minio_container_default() -> None:
    with MinioContainer() as minio:
        minio.wait_ready(timeout=120)
        minio.get_bucket("test")


def test_minio_container_with_upload_download() -> None:
    with MinioContainer() as minio:
        minio.wait_ready(timeout=120)
        bucket = minio.get_bucket("test")
        its_me = pathlib.Path(__file__).resolve()
        target_key = its_me.name

        bucket.upload_file(str(its_me), target_key)

        filtered = bucket.objects.filter(Prefix=target_key)
        assert filtered
        found = False
        for f in filtered:
            if f.key == target_key:
                found = True
        assert found
