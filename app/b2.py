from b2sdk.v2 import InMemoryAccountInfo, B2Api
import os

info = InMemoryAccountInfo()
b2_api = B2Api(info)
b2_api.authorize_account("production", os.getenv("B2_KEY_ID"), os.getenv("B2_APP_KEY"))
bucket = b2_api.get_bucket_by_name(os.getenv("B2_BUCKET_NAME"))

def upload_pdf_to_b2(local_path, filename):
    with open(local_path, "rb") as f:
        bucket.upload_bytes(f.read(), filename)
    return f"https://f000.backblazeb2.com/file/{os.getenv('B2_BUCKET_NAME')}/{filename}"