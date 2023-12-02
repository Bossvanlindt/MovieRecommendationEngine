import docker
from scheduler import clear_all_cron_jobs
from deploy_inference_container import remove_container, build_and_deploy_main_inference
client = docker.from_env()
import argparse
import os
from EmailNotifier import email_notifier
import subprocess
from db_utils.azure_db import get_session
from db_utils.user import UserModelMap
from sqlalchemy import delete

# Get the nightly version from the command line argument
parser = argparse.ArgumentParser(description="Pass in the version number")
parser.add_argument('--nightly', 
                    metavar='nightly', 
                    type=str, 
                    help='the version number')
args = parser.parse_args()
nightly_version = args.nightly
session =  get_session()

def rename_docker_image(current_name, new_name):
    """
    Function to rename a Docker image.

    Args:
    current_name (str): The current name (and tag) of the Docker image.
    new_name (str): The new name (and tag) for the Docker image.

    Returns:
    bool: True if successful, False otherwise.
    """
    client = docker.from_env()

    try:
        image = client.images.get(current_name)
        image.tag(new_name)
        print(f"Image {current_name} successfully renamed to {new_name}")
        return True
    except docker.errors.ImageNotFound:
        print(f"Image {current_name} not found.")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def push_docker_image(repository, tag='latest'):
    """
    Pushes a Docker image to Docker Hub using environment variables for credentials.

    Args:
    repository (str): Repository name on Docker Hub, including the username.
    tag (str): Tag for the image, defaults to 'latest'.
    """
    client = docker.from_env()

    # Retrieve credentials from environment variables
    dockerhub_username = os.environ.get('DOCKERHUB_USERNAME')
    dockerhub_password = os.environ.get('DOCKERHUB_PASSWORD')

    if not dockerhub_username or not dockerhub_password:
        print("Docker Hub credentials not found in environment variables.")
        return

    # Log in to Docker Hub
    try:
        client.login(username=dockerhub_username, password=dockerhub_password)
        print("Logged in to Docker Hub successfully.")
    except docker.errors.APIError as err:
        print(f"Failed to log in to Docker Hub: {err}")
        return

    # Push the image
    full_image_name = f"{repository}:{tag}"
    try:
        push_log = client.images.push(repository, tag=tag)
        print(f"Image {full_image_name} successfully pushed to Docker Hub.")
        print(push_log)
    except Exception as e:
        print(f"An error occurred while pushing the image: {e}")

# TODO: Gaurav, add your logic and the eval script runs to set this value accordingly

metric_main = subprocess.check_output("docker exec main-inference-app python3 online_eval.py main", shell = True) # the main at the end is container_name
metric_nightly = subprocess.check_output("docker exec nightly-inference-app python3 online_eval.py nightly", shell = True)
metric_main = float(metric_main.decode())
metric_nightly = float(metric_nightly.decode())

if metric_nightly >= metric_main:
    online_eval_passes = True
else:
    online_eval_passes = False

# print(metric_main)
# print(metric_nightly)
# print(online_eval_passes)

session.query(UserModelMap).delete()
session.commit()

if online_eval_passes:
    email_notifier.send_alert_email(subject=f"Online Evaluation Passed",error="Live is good everything worked alright :)")
    # Stop & remove the both main and nightly containers
    remove_container("main-inference-app")
    remove_container("nightly-inference-app")
    # Rename and push nightly image to dockerhub as main
    rename_docker_image(f"blo7/comp585_team-5_recommender_nightly:{nightly_version}", "blo7/comp585_team-5_recommender:latest")
    push_docker_image("blo7/comp585_team-5_recommender")
    # Build new Main Image
    build_and_deploy_main_inference()
else:
    email_notifier.send_alert_email(subject=f"Online Evaluation Failed",error="The sky is falling everything went wrong :(")
    remove_container("nightly-inference-app")
clear_all_cron_jobs()
