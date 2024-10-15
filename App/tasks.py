from celery import Celery
from selenium_script import fill_form
import requests
import json
import redis

# Configure Celery with Redis as both the broker and the result backend
app = Celery('form_filling_tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

WEBHOOK_BASE_URL = "https://mk25fcg4-4001.inc1.devtunnels.ms/api/v1/user/passport-form/{}/form-fill-success"

# Define the Celery task to fill the form using Selenium
@app.task
def fill_form_task(user_data):
    
    redis_client.flushdb()
    print("Redis cache cleared successfully.")
    
    result = None
    
    # Extract the form ID from user_data
    form_id = str(user_data.get('_id', {}).get('$oid'))  # Assuming _id is in this format

    # Construct the full webhook URL with the form ID
    webhook_url = WEBHOOK_BASE_URL.format(form_id)
    
    try:
        # Fill the form using Selenium (this part can raise exceptions)
        result = fill_form(user_data)
        
        # If form filling is successful, send success notification to the webhook
        payload = {
            "status": "SUCCESS",
            "message": "Form filled successfully.",
            "result": result  # Result of the form-filling task, e.g., the download URL
        }
        headers = {'Content-Type': 'application/json'}
        requests.post(webhook_url, data=json.dumps(payload), headers=headers)

    except Exception as e:
        # If any error occurs (e.g., Selenium or file upload failure), send error notification
        payload = {
            "status": "FAILURE",
            "message": "An error occurred during form filling.",
            "error": str(e)
        }
        headers = {'Content-Type': 'application/json'}
        requests.post(webhook_url, data=json.dumps(payload), headers=headers)

    return result