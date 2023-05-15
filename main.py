import exchange
import fuelprice
from apscheduler.schedulers.background import BlockingScheduler


# set up a blocking scheduler instance.
scheduler = BlockingScheduler()
# add a job to the scheduler the instance from "exchange" to be executed at 13:10 every day.
# scheduler.add_job(func=exchange.send_notification, trigger="cron", hour=13, minute=10)
scheduler.add_job(func=exchange.send_notification, trigger="interval", seconds=60)
# add a job to the scheduler the instance from "fuelprice" to be executed at 13:30 every day.
# scheduler.add_job(func=fuelprice.send_notification, trigger="cron", hour=13, minute=30)
scheduler.add_job(func=fuelprice.send_notification, trigger="interval", seconds=15)
# start the scheduler and run until requested to stop
scheduler.start()