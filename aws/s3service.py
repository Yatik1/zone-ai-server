import boto3
from config import BUCKET_NAME, REGION_NAME, ACCESS_KEY, AWS_SECRET_KEY
import uuid as uuid

s3_client = boto3.client(
    's3',
    region_name=REGION_NAME,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

def upload_file_to_s3(file_content:bytes, file_name:str) -> str:
    unique_file_name = f"{uuid.uuid4()}_{file_name}"
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=unique_file_name,
            Body=file_content
        )

        return unique_file_name
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        return None

def generate_presigned_url(s3_key:str, expiry:int) -> str:
    try:
        url=s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket':BUCKET_NAME,
                'Key':s3_key
            },
            ExpiresIn=expiry
        )
        
        return url
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return None