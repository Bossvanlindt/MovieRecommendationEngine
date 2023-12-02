from crontab import CronTab
import datetime
import os
from dotenv import load_dotenv
load_dotenv()

LOAD_BALANCER_DIR = os.environ.get("CICD_SCRIPTS_PATH")

# Modify this to affect the time till execution
HOURS=12
MINUTES=0

def clear_all_cron_jobs():
    # Access the current user's crontab
    cron = CronTab(user=True)
    # Remove all cron jobs
    cron.remove_all()
    # Write the changes to the crontab
    cron.write()

def modify_crontab(nightly_version):
    # Access the current user's crontab
    cron = CronTab(user=True)

    # Calculate future time from now
    future_time = datetime.datetime.now() + datetime.timedelta(hours=HOURS, minutes=MINUTES)

    # Create a new job with the specific command
    job = cron.new(command=f'/usr/bin/python3 {LOAD_BALANCER_DIR}/replace_main_for_nightly.py --nightly {nightly_version}', comment='MyCronJob')

    # Set the exact time for the job
    job.minute.on(future_time.minute)
    job.hour.on(future_time.hour)
    job.day.on(future_time.day)
    job.month.on(future_time.month)
    job.dow.on(future_time.weekday())

    # Write the job to the crontab
    cron.write()

def set_replace_main_schedule(nightly_version='latest'):
    clear_all_cron_jobs()
    modify_crontab(nightly_version)

if __name__ == '__main__':
    set_replace_main_schedule()
