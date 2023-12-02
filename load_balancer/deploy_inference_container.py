# To run, use: python3 deploy_inference_container.py --nightly <version>
import docker
from scheduler import set_replace_main_schedule,clear_all_cron_jobs
import os
from dotenv import load_dotenv
load_dotenv()
import argparse

# Parse nightly version to pull it from dockerhub
parser = argparse.ArgumentParser(description="Pass in the version number")
parser.add_argument('--nightly', 
                    metavar='nightly', 
                    type=str, 
                    help='the version number')
args = parser.parse_args()
nightly_version = args.nightly

# Global variables
loadbalancer_deployed = False
main_inference_deployed = False
nightly_inference_deployed = False
client = docker.from_env()
LOAD_BALANCER_DIR = os.environ.get("CICD_SCRIPTS_PATH")

def docker_login():
    """
    Authenticate with Docker Hub using environment variables.
    """
    dockerhub_username = os.environ.get('DOCKERHUB_USERNAME')
    dockerhub_password = os.environ.get('DOCKERHUB_PASSWORD')
    
    if not dockerhub_username or not dockerhub_password:
        print("Docker Hub credentials not found in environment variables.")
        return False
    try:
        client.login(username=dockerhub_username, password=dockerhub_password)
        print("Logged in to Docker Hub successfully.")
        return True
    except docker.errors.APIError as err:
        print(f"Failed to log in to Docker Hub: {err}")
        return False

def remove_container(container_name):
    try:
        container = client.containers.get(container_name)
        container.stop()
        container.remove()
        print(f"Removed container {container_name}")
    except docker.errors.NotFound:
        print(f"Container {container_name} not found. No need to remove.")
        
def build_and_deploy_main_inference(port=3001):
    image_name = "blo7/comp585_team-5_recommender:latest"  # Define the image name here
    print(f"Pulling {image_name} image...")
    client.images.pull(image_name)
    print(f"Deploying {image_name} container on port {port}...")
    client.containers.run(
        image_name,
        name="main-inference-app",
        environment={'PORT': 3001},
        ports={'3001/tcp': 3001},  # Corrected the ports mapping
        network="monitoring-network",
        detach=True
    )

def build_and_deploy_nightly_inference(port=3002):
    image_name=image_name=f"blo7/comp585_team-5_recommender_nightly:{nightly_version if nightly_version else 'latest'}"
    print(f"Pulling {image_name} image...")
    client.images.pull(image_name)
    print(f"Deploying {image_name} container on port {port}...")
    client.containers.run(
        image_name,
        name="nightly-inference-app",
        environment={'PORT': 3002},
        ports={'3002/tcp': 3002},
        network="monitoring-network",
        detach=True
    )

def build_and_deploy_load_balancer():
    print("Building load_balancer image...")
    client.images.build(
        path=LOAD_BALANCER_DIR,  # Paths adjusted for team-5 user on McGill server
        dockerfile=f"{LOAD_BALANCER_DIR}/Dockerfile",
        tag="loadbalancer-app"
    )
    print("Deploying load_balancer container...")
    client.containers.run(
        "loadbalancer-app",
        name="loadbalancer-app",
        ports={'8082/tcp': 8082},
        network="monitoring-network",
        detach=True
    )
    
def check_container_status():
    global loadbalancer_deployed, main_inference_deployed, nightly_inference_deployed

    for container in client.containers.list(all=True):
        if container.name == "loadbalancer-app" and container.status == "running":
            loadbalancer_deployed = True
        elif container.name == "main-inference-app" and container.status == "running":
            main_inference_deployed = True
        elif container.name == "nightly-inference-app" and container.status == "running":
            nightly_inference_deployed = True
            
def deploy_container():
    clear_all_cron_jobs()
    if not loadbalancer_deployed:
        remove_container("loadbalancer-app")
        build_and_deploy_load_balancer()
    if not main_inference_deployed:
        remove_container("main-inference-app")
        remove_container("nightly-inference-app")
        build_and_deploy_main_inference()
    else: # We're adding a nightly container
        remove_container("nightly-inference-app")
        build_and_deploy_nightly_inference()
         # Set schedule to replace the deployed nightly to the main
        set_replace_main_schedule(nightly_version)
    
if __name__ == '__main__':
    docker_login()
    #get containers current status
    check_container_status()
    # Printing the status for verification
    print(f"Loadbalancer Deployed: {loadbalancer_deployed}")
    print(f"Main Inference Deployed: {main_inference_deployed}")
    print(f"Nightly Inference Deployed: {nightly_inference_deployed}")
    #deploy containers according to the status
    deploy_container()