import base64
from io import BytesIO
import json
import os
import uuid
import boto3
from botocore.exceptions import ClientError
from openai import OpenAI


# Initialize OpenAI client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get('OPENAI_API_KEY')
)

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'),
    region_name='us-east-1'
)

# S3 bucket configuration
BUCKET_NAME = 'business-cards-bucket-mj'

def upload_to_s3(image):
    """Upload PIL Image to S3 and return URL"""
    try:
        # Convert PIL Image to bytes
        buffer = BytesIO()
        image.save(buffer, format='JPEG')
        buffer.seek(0)

        # Generate unique filename
        filename = f"card_{uuid.uuid4()}.jpg"

        # Upload to S3
        s3_client.upload_fileobj(buffer, BUCKET_NAME, filename)

        # Generate URL (valid for 5 minutes)
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': filename},
            ExpiresIn=36000  # 10 hours
        )

        # Return both URL and filename for cleanup
        return url, filename
    except ClientError as e:
        raise Exception(f"Failed to upload image to S3: {str(e)}")

def delete_from_s3(filename):
    """Delete file from S3 after processing"""
    try:
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=filename)
    except ClientError:
        pass  # Ignore deletion errors

def extract_card_info(image):
    """
    Extract information from business card image using GPT-4o

    Args:
        image: PIL Image object of the business card

    Returns:
        dict: Contains extracted information based on the defined schema
    """
    s3_filename = None
    try:
        # Upload image to S3 and get URL
        image_url, s3_filename = upload_to_s3(image)

        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="openai/gpt-4o-2024-08-06",
            # model="deepseek/deepseek-r1",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extract details from each business card image and format them as JSON objects following this schema:\n"
                                "{\n"
                                "  \"company_name\": \"\",\n"
                                "  \"contact_person\": [\n"
                                "    {\n"
                                "      \"name\": \"\",\n"
                                "      \"position\": \"\",\n"
                                "      \"personal_phone\": [{\"\"}],\n"
                                "      \"personal_email\": [{\"\"}]\n"
                                "    }\n"
                                "  ],\n"
                                "  \"company_address\": [\n"
                                "    {\n"
                                "      \"remaining\": \"\",\n"
                                "      \"city\": \"\",\n"
                                "      \"state\": \"\",\n"
                                "      \"country\": \"\",\n"
                                "      \"pincode\": \"\"\n"
                                "    }\n"
                                "  ],\n"
                                "  \"company_email\": [{\"\"}],\n"
                                "  \"company_phone\": [{\"\"}],\n"
                                "  \"company_fax\": [{\"\"}],\n"
                                "  \"company_website\": [{\"\"}],\n"
                                "  \"company_gstin\": [{\"\"}],\n"
                                "  \"company_details_if_any\": [{\"\"}]\n"
                                "}\n"
                                "Follow these Instructions:\n"
                                "- Return only the JSON object without any explanations or additional text.\n"
                                "- If a field is missing or information is not available, use null for that field.\n"
                                "- If multiple images are uploaded, provide separate JSON objects for each image.\n"
                                "- For unreadable or unclear images: provide a json in which set all fields to null and include a description of the issue in the 'company_name' field.\n"
                                "- If the state or country is missing, infer them based on the city.\n"
                                "- Format phone numbers with the appropriate country code based on the country."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )

        # Parse the response
        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        raise Exception(f"Failed to analyze image with GPT-4o: {str(e)}")
    finally:
        # Clean up S3 file if it was created
        if s3_filename:
            delete_from_s3(s3_filename)
