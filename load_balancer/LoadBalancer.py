from flask import Flask, request
import requests
import random
import subprocess
import json
import threading
from db_utils.azure_db import get_session
from db_utils.user import RecommendationsHistory, UserModelMap
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
nightlyActive = True
main_url = os.environ.get("MAINURL")
nightly_url = os.environ.get("NIGHTLYURL")

session = get_session()

class LoadBalancer:
    def __init__(self):
        self.user_container_map = {}
        self.save_interval = 60  # in seconds, set your desired interval

    def get_container_url(self, user_id):
        if not nightlyActive:
            return main_url

        # If the user has already been assigned a model version, return the corresponding container URL
        q = session.query(UserModelMap).filter(UserModelMap.user_id == user_id)
        if q.count() > 0:
            model_version = q.first().model_version
            return nightly_url if model_version == 'nightly' else main_url

        # Otherwise, assign a model version to the user and save it to the database
        container_url = main_url if random.random() < 0.8 else nightly_url
        model_version = 'nightly' if container_url[-4:] == '3002' else 'main'
        user_model_map = UserModelMap(user_id=user_id, model_version=model_version)
        session.add(user_model_map)
        session.commit()

        return container_url
        
    def check_nightly_inference_health(self):
        global nightlyActive
        try:
            # Using ping command. Adjust the count (-c) as needed.
            response = subprocess.run(['ping', '-c', '1', 'nightly-inference-app'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            nightlyActive = response.returncode == 0
        except Exception as e:
            print(f"Error during ping: {e}")
            nightlyActive = False
        # Schedule the next health check
        threading.Timer(60, self.check_nightly_inference_health).start()  # Check every 60 seconds

# Start periodic health checks
load_balancer = LoadBalancer()
load_balancer.check_nightly_inference_health()  

@app.route('/<service>/<user_id>', methods=['GET'])
def proxy(service, user_id):
    # Validate user_id
    if not user_id:
        return "User ID is required", 400

    # Determine the backend service URL
    container_url = load_balancer.get_container_url(user_id)

    # Construct the full URL
    full_url = f"{container_url}/{service}/{user_id}"

    # Forward the request to the backend service
    response = requests.get(url=full_url)

    # Store to the database for data provenance
    model_version = 'nightly' if container_url[-4:] == '3002' else 'main'
    history = RecommendationsHistory(user_id=user_id, model_version=model_version, watch_history='Use Watched & timestamp to find it', recommendations=response.content.decode())
    session.add(history)
    session.commit()

    # Send the response back to the client
    return response.content

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000)
