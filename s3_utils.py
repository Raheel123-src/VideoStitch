import boto3
import os
from botocore.exceptions import ClientError
from typing import Optional

def upload_to_s3(file_path: str, bucket_name: str, s3_key: str) -> str:
    """
    Upload a file to S3 and return the public URL
    
    Args:
        file_path: Local path to the file
        bucket_name: S3 bucket name
        s3_key: S3 object key (filename in S3)
    
    Returns:
        Public URL of the uploaded file
    """
    # Check if AWS credentials are available
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    if not aws_access_key or not aws_secret_key:
        raise Exception("AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")
    
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        )
        
        # Upload file to S3
        s3_client.upload_file(
            file_path, 
            bucket_name, 
            s3_key,
            ExtraArgs={
                'ContentType': 'video/mp4',
            }
        )
        
        # Generate public URL
        public_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
        
        print(f"✅ Successfully uploaded {file_path} to S3: {public_url}")
        return public_url
        
    except ClientError as e:
        error_msg = f"Failed to upload to S3: {str(e)}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error uploading to S3: {str(e)}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)

def get_s3_bucket_name() -> str:
    """Get S3 bucket name from environment or use default"""
    return os.environ.get('S3_BUCKET_NAME', 'video-stitcher-outputs')

def generate_s3_key(filename: str) -> str:
    """Generate a unique S3 key for the video"""
    import uuid
    short_uuid = uuid.uuid4().hex[:8]
    return f"stitched-videos/{short_uuid}_{filename}"
