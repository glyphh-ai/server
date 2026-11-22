"""Upload a rendered corpus to a private R2 prefix: every file first, the manifest last.

    uv run --with boto3 --with python-dotenv python datasets/applicants/upload.py --env ../server/.env \
        --bucket <private bucket> --out datasets/applicants/out
"""

import argparse
import mimetypes
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import boto3
from dotenv import dotenv_values

PREFIX: str = "datasets/applicants/v1/"
LAST: str = "manifest.jsonl"


def s3(env_file: Path):
    env = dotenv_values(env_file)
    return boto3.client(
        "s3",
        endpoint_url=env["R2_ENDPOINT"],
        aws_access_key_id=env["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
        region_name=env.get("R2_REGION") or "auto",
    )


def put(client, bucket: str, root: Path, path: Path) -> None:
    kind = mimetypes.guess_type(path.name)[0] or ("message/rfc822" if path.suffix == ".eml" else "text/plain")
    client.upload_file(str(path), bucket, PREFIX + str(path.relative_to(root)), ExtraArgs={"ContentType": kind})


def upload(client, bucket: str, root: Path) -> int:
    files = [p for p in sorted(root.rglob("*")) if p.is_file() and p.name != LAST]
    with ThreadPoolExecutor(16) as pool:
        list(pool.map(lambda p: put(client, bucket, root, p), files))
    put(client, bucket, root, root / LAST)
    return len(files) + 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", type=Path, required=True)
    ap.add_argument("--bucket", required=True)
    ap.add_argument("--out", type=Path, default=Path("datasets/applicants/out"))
    args = ap.parse_args()
    n = upload(s3(args.env), args.bucket, args.out / "corpus")
    print(f"uploaded {n} objects to {args.bucket}/{PREFIX}")


if __name__ == "__main__":
    main()
