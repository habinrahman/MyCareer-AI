import asyncio
import logging

from supabase import Client

logger = logging.getLogger(__name__)


async def upload_bytes(
    client: Client,
    bucket: str,
    path: str,
    data: bytes,
    content_type: str,
) -> None:
    def _upload() -> None:
        client.storage.from_(bucket).upload(
            path,
            data,
            file_options={"content-type": content_type},
        )

    await asyncio.to_thread(_upload)
    logger.info("storage.upload bucket=%s path=%s bytes=%s", bucket, path, len(data))


async def download_bytes(client: Client, bucket: str, path: str) -> bytes:
    def _download() -> bytes:
        return client.storage.from_(bucket).download(path)

    data = await asyncio.to_thread(_download)
    logger.info("storage.download bucket=%s path=%s bytes=%s", bucket, path, len(data))
    return data


async def create_signed_url(
    client: Client,
    bucket: str,
    path: str,
    expires_in: int,
) -> str | None:
    def _sign() -> dict:
        return client.storage.from_(bucket).create_signed_url(path, expires_in)

    try:
        result = await asyncio.to_thread(_sign)
    except Exception as exc:
        logger.warning("storage.sign_failed bucket=%s path=%s err=%s", bucket, path, exc)
        return None
    signed = result.get("signedURL") or result.get("signedUrl")
    return str(signed) if signed else None
