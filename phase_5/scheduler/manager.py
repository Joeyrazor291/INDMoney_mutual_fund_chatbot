from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from .tasks import daily_data_refresh

# Persistent scheduler instance
scheduler = BackgroundScheduler()

def init_scheduler():
    """
    Initializes and starts the APScheduler.
    Sets up the 12:30 AM daily refresh job.
    """
    if not scheduler.running:
        # Add the daily refresh task
        # schedule for 00:30 (12:30 AM)
        scheduler.add_job(
            daily_data_refresh,
            trigger=CronTrigger(hour=0, minute=30),
            id="daily_refresh_task",
            name="Refresh Mutual Fund data from INDMoney",
            replace_existing=True
        )
        
        scheduler.start()
        logging.info("APScheduler initialized and started. Next run at 12:30 AM.")
    else:
        logging.info("APScheduler is already running.")

def shutdown_scheduler():
    """Shuts down the scheduler session."""
    if scheduler.running:
        scheduler.shutdown()
        logging.info("APScheduler shut down.")
