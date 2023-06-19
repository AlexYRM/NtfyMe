from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from db_connection import DBConnection
import exchange
import fastapiendpoints
import fuelprice
import uvicorn
import website

# Create an instance of the DBConnection class and assign it to the variable DB
DB = DBConnection()
# set up a blocking scheduler instance.
scheduler = BackgroundScheduler()
# Create the tables in the database
DB.create_tables()
# Create a FastAPI application instance
app = FastAPI()
# Include the router from "fastapiendpoints.py"
app.include_router(fastapiendpoints.router)

print("Start Scheduling jobs")
# add a job to the scheduler the instance from "exchange" to be executed at 13:10 every day.
scheduler.add_job(func=exchange.send_notification, trigger="cron", hour=13, minute=10)
# add a job to the scheduler the instance from "fuelprice" to be executed at 13:20 every day.
scheduler.add_job(func=fuelprice.send_notification, trigger="interval", minutes=10)
# scheduler.add_job(func=fuelprice.send_notification, trigger="cron", hour=12, minute=55)

# start the scheduler and run until requested to stop
scheduler.start()
# run the NiceGUI website
website.init(fastapi_app=app)

# keep scheduler running until stopped manually
while True:
    uvicorn.run(app, host="0.0.0.0", port=3110)
