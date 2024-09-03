from flask import Flask, request
import json
import requests
import subprocess
import os
import sys

print("Python version:", sys.version)
print("Python executable:", sys.executable)

app = Flask(__name__)

@app.route('/sns', methods=['POST'])
def sns_listener():
    # Handle empty or non-JSON payloads
    if not request.data:
        print("Received an empty POST request")
        return '', 400  # Bad Request

    try:
        data = json.loads(request.data)
    except json.JSONDecodeError:
        print("Received a request with invalid JSON")
        return '', 400  # Bad Request

    # Check if it's a SubscriptionConfirmation request
    if data.get('Type') == 'SubscriptionConfirmation' and 'SubscribeURL' in data:
        subscribe_url = data['SubscribeURL']
        requests.get(subscribe_url)
        print("Subscription confirmed.")
        return '', 200

    # Otherwise, it's a notification
    message = json.loads(data['Message'])
    print(f"Received message: {message}")

    # Extract the bucket and object key from the SNS message
    records = message.get('Records', [])
    if not records:
        print("No records found in the message.")
        return '', 400

    bucket_name = records[0]['s3']['bucket']['name']
    object_key = records[0]['s3']['object']['key']

    # Define the full path to the script
    script_path = '/home/ec2-user/DocumentAI_extraction/app_aws.py'

    # Call the app_aws.py script using subprocess
    try:
        with open("/tmp/app_aws_output.log", "a") as f:
            subprocess.Popen(['python3', script_path, bucket_name, object_key], stdout=f, stderr=f)
        print(f"Started processing {object_key} from bucket {bucket_name}.")
    except Exception as e:
        print(f"Failed to start app_aws.py: {e}")
        return '', 500

    return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)