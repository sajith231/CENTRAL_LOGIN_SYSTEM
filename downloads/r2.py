import os, boto3
from dotenv import load_dotenv

load_dotenv()

def get_r2():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("CLOUDFLARE_R2_BUCKET_ENDPOINT"),
        aws_access_key_id=os.getenv("CLOUDFLARE_R2_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("CLOUDFLARE_R2_SECRET_KEY"),
        region_name="auto"
    )