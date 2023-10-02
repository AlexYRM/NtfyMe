from fastapi.responses import FileResponse
from db_connection import DBConnection
from fastapi import APIRouter, Query
from squash import SquashConnection
import json
import datetime
import fuelprice

router = APIRouter()
DB = DBConnection()
SQ = SquashConnection()

# Define an endpoint to add a station to the database
@router.post("/add_station_to_database")
def add_station_to_database(station_id: str = Query(
            ...,
            description="Write a OMV or PETROM station id found on their website in details.php post request, "
                        "request, ID ")):
    # Call your function to add data to the database
    DB.scrape_station_info_and_upload_to_database(station_id)
    return {"message": "Data added to the database"}


# Define an endpoint to remove a station from the database
@router.post("/remove_station_in_st_identification")
def remove_station_from_database(OMV_PETROM_station_id: str):
    DB.remove_station(OMV_PETROM_station_id=OMV_PETROM_station_id)
    return {"message": "Station was successfully removed from station_identification table"}


# Define an endpoint to download the database file
@router.get("/get_file")
async def download_file():
    path = "./database/fuelprice.db"
    return FileResponse(path=path, filename="fuelprice.db", media_type="application/octet-stream")


# Define an endpoint to delete an entire row of data in fuel_data table
@router.post("/delete_row")
def delete_row_or_rows(station_id: str = Query(..., description="Write the station ID in fuel_data. Example: 2"),
                       date: str = Query(..., description="Write the date from which data to be deleted. Format should "
                                                          "be YYYY-MM-DD. Can select multiple days to delete from a "
                                                          "month in this format YYYY-MM-DD,DD,DD ...  "
                                                          "Example: 2023-05-04,05,23")):

    # Check if station_id contains only digits
    if not station_id.isdigit():
        return {"error": "station_id must be a number."}
    # Check if date is in the format YYYY-MM-DD
    try:
        # Split the date string into a list if it contains comma (",") or create a single-item list
        date_list = date.split(",") if "," in date else [date]
        datetime.datetime.strptime(date_list[0], "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Please use YYYY-MM-DD."}
    if len(date_list) > 1:
        # Extract year and month from the first date in the list
        year, month, _ = date_list[0].split('-')
        # Transform the remaining dates in the list to match the format of the first date
        transformed_date_list = [f"{year}-{month}-{day.strip()}" for day in date_list[1:]]
        # Insert the original first date back to the beginning of the transformed list
        transformed_date_list.insert(0, date_list[0])
        # Delete rows for each date
        for every_date in transformed_date_list:
            DB.delete_row(station_id=station_id, date=every_date)
    else:
        # Delete a single row with the provided date
        DB.delete_row(station_id=station_id, date=date)
    return {"message": "Row deleted successfully"}


# Define an endpoint to change entire row of data in fuel_data table
@router.post("/change_data_fuel_data")
def change_data_table_fuel_data(
        new_data: str = Query(
            ...,
            description="Write a dictionary containing all the new values to be introduced in the table",
            example={'Motorina Standard': 6.380, 'Motorina Premium': 6.740, 'Benzina Standard': 6.390,
                     'Benzina Premium': 6.850, "GPL": 3.83, 'date': '2023-05-18', 'station_id': 1})
):
    try:
        # Parse the string and convert it into a Python dictionary object
        new_data = json.loads(new_data)
    except:
        # Check if the input is in the correct format
        return {"message": "You did not write the correct format. Try again!"}
    else:
        # If the data in correct, check for it not to be the given example
        if new_data == {'Motorina Standard': 6.380, 'Motorina Premium': 6.740, 'Benzina Standard': 6.390,
                        'Benzina Premium': 6.850, "GPL": 3.83, 'date': '2023-05-18', 'station_id': 1}:
            return {"message": "Congratulations! You have successfully uploaded the example that was already given. "
                               "You've mastered the art of following instructions to the letter!. Try something else!"}
        else:
            table_name = "fuel_data"
            DB.change_fuel_data(table=table_name, data=new_data)
            return {"message": "Data was successfully updated in fuel data table"}


# Define an endpoint to add data manually to fuel_data table
@router.post("/manually_add_fuel_data")
def manually_add_data_table_fuel_data(
        new_data: str = Query(
            ...,
            description="Write a dictionary containing all the new values to be introduced in the table",
            example={'date': '2023-05-18', 'station_id': 1, 'Motorina Standard': 6.380, 'Motorina Premium': 6.740,
                     'Benzina Standard': 6.390, 'Benzina Premium': 6.850, "GPL": 3.83})
):
    try:
        new_data = json.loads(new_data)
    except:
        return {"message": "You did not write the correct format. Try again!"}
    else:
        if new_data == {'date': '2023-05-18', 'station_id': 1, 'Motorina Standard': 6.380, 'Motorina Premium': 6.740,
                        'Benzina Standard': 6.390, 'Benzina Premium': 6.850, "GPL": 3.83}:
            return {"message": "Congratulations! You have successfully uploaded the example that was already given. "
                               "You've mastered the art of following instructions to the letter!. Try something else!"}
        else:
            table_name = "fuel_data"
            DB.add_fuel_data(table=table_name, data=new_data)
            return {"message": "Data was successfully inserted in fuel data table"}


# Define an endpoint to manually run fuelprice.py
@router.post("/manually_execute_fuelprice.py")
def manually_execute_fuelprice():
    fuelprice.send_notification()
    return {"message": "fuelprice.py was executed manually"}


# Define an endpoint to rescrape and send the data in a notification
@router.post("/check_squash_avbl")
def check_again():
    SQ.send_notification()
    return {"message": "notification was sent again"}