from b2sdk.v2 import InMemoryAccountInfo, B2Api
import os

# Load environment variables
B2_KEY_ID = os.getenv("B2_KEY_ID")
B2_APP_KEY = os.getenv("B2_APP_KEY")
B2_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")

# Validate environment variables
if not all([B2_KEY_ID, B2_APP_KEY, B2_BUCKET_NAME]):
    raise EnvironmentError("Missing one or more required B2 credentials (KEY_ID, APP_KEY, BUCKET_NAME)")

# Setup B2 API
info = InMemoryAccountInfo()
b2_api = B2Api(info)

try:
    b2_api.authorize_account("production", B2_KEY_ID, B2_APP_KEY)
    bucket = b2_api.get_bucket_by_name(B2_BUCKET_NAME)
except Exception as e:
    raise RuntimeError(f"Failed to connect to B2: {str(e)}")

def upload_pdf_to_b2(local_path: str, filename: str) -> str:
    """
    Uploads a PDF to B2 cloud and returns the public file URL.

    Args:
        local_path (str): Path to local PDF file.
        filename (str): Desired filename in the B2 bucket.

    Returns:
        str: Public URL to the uploaded file.
    """
    try:
        with open(local_path, "rb") as f:
            bucket.upload_bytes(f.read(), filename)

        return f"https://f000.backblazeb2.com/file/{B2_BUCKET_NAME}/{filename}"

    except Exception as e:
        raise RuntimeError(f"Failed to upload file to B2: {str(e)}")
