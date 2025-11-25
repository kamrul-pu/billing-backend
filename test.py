# import boto3
# from botocore.client import Config

# # If using AWS S3:
# session = boto3.session.Session()

# # s3 = session.client(
# #     "s3",
# #     aws_access_key_id="YOUR_ACCESS_KEY",
# #     aws_secret_access_key="YOUR_SECRET_KEY",
# #     region_name="YOUR_REGION",
# # )

# # If using MinIO or any S3-compatible provider (example):

# s3 = boto3.client(
#     "s3",
#     endpoint_url="https://media.billsheba.com",
#     aws_access_key_id="admin",
#     aws_secret_access_key="Letmein2211##",
#     config=Config(signature_version="s3v4"),
#     region_name="us-east-1",
# )


# # Path of local file
# local_file = "me.jpg"

# # Key (path inside your bucket)
# bucket_key = "media/me.jpg"

# # Name of your bucket
# bucket_name = "bill-sheba-media"

# try:
#     s3.upload_file(local_file, bucket_name, bucket_key)
#     print("Uploaded successfully!")
# except Exception as e:
#     print("Upload failed:", e)

import boto3
from botocore.client import Config

# Create MinIO S3 client
s3 = boto3.client(
    "s3",
    endpoint_url="https://media.billsheba.com",
    aws_access_key_id="admin",
    aws_secret_access_key="Letmein2211##",
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)

local_file = "me.jpg"
bucket_name = "bill-sheba-media"
bucket_key = "media/me.jpg"

try:
    # Upload file (NO ACL!)
    s3.upload_file(local_file, bucket_name, bucket_key)

    # Public URL (CORRECT)
    public_url = f"https://media.billsheba.com/{bucket_name}/{bucket_key}"

    print("Uploaded successfully!")
    print("Public URL:", public_url)

except Exception as e:
    print("Upload failed:", e)
