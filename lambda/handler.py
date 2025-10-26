"""
Main Lambda function handler for Daily Stoic Reflection service.

This is the entry point triggered daily by EventBridge to generate and send
stoic reflections via email.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any
import boto3
from botocore.exceptions import ClientError

# Import local modules
from themes import get_monthly_theme
from quote_tracker import QuoteTracker
from quote_loader import QuoteLoader
from email_formatter import (
    format_html_email,
    format_plain_text_email,
    create_email_subject,
    validate_email_content
)
from anthropic_client import generate_reflection_only

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
ses_client = boto3.client('ses')
s3_client = boto3.client('s3')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda function triggered daily by EventBridge.

    Args:
        event: EventBridge event (empty for scheduled triggers)
        context: Lambda context object

    Returns:
        Response dictionary with status and message
    """
    logger.info("Starting Daily Stoic Reflection generation")

    try:
        # 1. Get environment variables
        bucket_name = os.environ.get('BUCKET_NAME')
        sender_email = os.environ.get('SENDER_EMAIL')
        anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
        aws_region = os.environ.get('AWS_REGION', 'us-west-2')

        # Validate environment variables
        if not all([bucket_name, sender_email, anthropic_api_key]):
            raise ValueError("Missing required environment variables")

        logger.info(f"Using bucket: {bucket_name}")
        logger.info(f"Sender email: {sender_email}")

        # 2. Determine current date, month, and theme
        current_date = datetime.now()
        current_date_str = current_date.strftime('%Y-%m-%d')
        current_month = current_date.month

        theme_info = get_monthly_theme(current_month)
        theme_name = theme_info['name']

        logger.info(f"Date: {current_date_str}")
        logger.info(f"Month: {current_month}")
        logger.info(f"Theme: {theme_name}")

        # 3. Load today's quote from the 365-day database
        logger.info("Loading today's quote from database...")
        quote_loader = QuoteLoader(bucket_name)
        quote_data = quote_loader.get_quote_for_date(current_date)

        quote = quote_data['quote']
        attribution = quote_data['attribution']
        # Note: theme from quote_data matches the monthly theme
        logger.info(f"Loaded quote for {current_date_str}: {attribution}")

        # 4. Load recipient config from S3
        recipients = load_recipients_from_s3(bucket_name)
        logger.info(f"Found {len(recipients)} recipients")

        if not recipients:
            raise ValueError("No recipients configured")

        # 5. Generate reflection via Anthropic API
        logger.info("Generating reflection via Anthropic API...")
        reflection = generate_reflection_only(
            quote=quote,
            attribution=attribution,
            theme=theme_name,
            api_key=anthropic_api_key
        )

        if not reflection:
            raise Exception("Failed to generate reflection from Anthropic API")

        logger.info(f"Generated reflection ({len(reflection)} chars)")

        # Validate content
        validation = validate_email_content(quote, attribution, reflection)
        if not validation['is_valid']:
            logger.warning(f"Content validation issues: {validation}")

        # 6. Update history in S3 (for posterity)
        logger.info("Updating quote history...")
        tracker = QuoteTracker(bucket_name)
        history = tracker.load_history()

        # Add today's entry with reflection preview
        history = tracker.add_quote(history, current_date_str, quote, attribution, reflection, theme_name)

        # Cleanup old quotes (keep 400 days for reasonable file size)
        history = tracker.cleanup_old_quotes(history, keep_days=400)

        tracker.save_history(history)
        logger.info(f"History updated. Total entries: {tracker.get_quote_count(history)}")

        # 7. Format and send email
        html_content = format_html_email(quote, attribution, reflection, theme_name)
        plain_text = format_plain_text_email(quote, attribution, reflection)
        subject = create_email_subject(theme_name)

        logger.info("Sending emails...")
        success_count = 0
        failure_count = 0

        for recipient in recipients:
            try:
                send_email_via_ses(
                    sender=sender_email,
                    recipient=recipient,
                    subject=subject,
                    html_body=html_content,
                    text_body=plain_text,
                    region=aws_region
                )
                success_count += 1
                logger.info(f"Successfully sent email to {recipient}")

            except Exception as e:
                failure_count += 1
                logger.error(f"Failed to send email to {recipient}: {e}")
                # Continue with other recipients

        # 8. Return success
        logger.info(
            f"Email sending complete. Success: {success_count}, Failed: {failure_count}"
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully sent to {success_count} of {len(recipients)} recipients',
                'date': current_date_str,
                'theme': theme_name,
                'attribution': attribution,
                'success_count': success_count,
                'failure_count': failure_count
            })
        }

    except Exception as e:
        logger.error(f"Fatal error in lambda_handler: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


def load_recipients_from_s3(bucket_name: str) -> List[str]:
    """
    Load recipient email addresses from S3 config file.

    Args:
        bucket_name: S3 bucket name

    Returns:
        List of email addresses

    Raises:
        Exception: If S3 read fails or config is invalid
    """
    try:
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key='recipients.json'
        )
        content = response['Body'].read().decode('utf-8')
        config = json.loads(content)

        recipients = config.get('recipients', [])

        if not isinstance(recipients, list):
            raise ValueError("Recipients must be a list")

        # Filter out empty strings
        recipients = [r.strip() for r in recipients if r.strip()]

        return recipients

    except ClientError as e:
        logger.error(f"Error loading recipients from S3: {e}")
        raise


def send_email_via_ses(
    sender: str,
    recipient: str,
    subject: str,
    html_body: str,
    text_body: str,
    region: str = 'us-west-2'
) -> None:
    """
    Send an email via Amazon SES.

    Args:
        sender: Sender email address
        recipient: Recipient email address
        subject: Email subject line
        html_body: HTML email body
        text_body: Plain text email body (fallback)
        region: AWS region (default: us-west-2)

    Raises:
        Exception: If email send fails
    """
    try:
        response = ses_client.send_email(
            Source=sender,
            Destination={
                'ToAddresses': [recipient]
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Html': {
                        'Data': html_body,
                        'Charset': 'UTF-8'
                    },
                    'Text': {
                        'Data': text_body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )

        logger.info(f"SES MessageId: {response['MessageId']}")

    except ClientError as e:
        logger.error(f"Error sending email via SES: {e}")
        raise
