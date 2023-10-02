import sqlite3
import pandas as pd
import requests
import json


class DBConnection:
    def __init__(self):
        self.conn = sqlite3.connect('database/fuelprice.db', check_same_thread=False)
        self.url = "https://app.wigeogis.com/kunden/omv/data/details.php"
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "origin": "https://www.omv.ro",
            "Accept": "application/json"
        }
        self.station_ids = list()

    def add_fuel_data(self, table: str, data: dict):
        # Connect to the SQLite database and create cursor
        c = self.conn.cursor()
        # Construct the initial update query
        query = f"INSERT INTO {table} ("
        # Initialize placeholders for column names and values
        columns = ""
        placeholders = ""
        for key, value in data.items():
            # Append each key as a column name in the query
            columns += f"'{key}', "
            # Append a placeholder for the corresponding value
            placeholders += "?, "
        # Remove the trailing comma and space from column names and placeholders
        columns = columns.rstrip(", ")
        placeholders = placeholders.rstrip(", ")
        # Complete the query by adding column names and placeholders
        query += f"{columns}) VALUES ({placeholders})"
        # Execute the update query with the corresponding values
        c.execute(query, list(data.values()))
        # Commit the changes to the database
        self.conn.commit()
        # Close the cursor and connection
        c.close()

    def station_sequence_list(self):
        # Create a cursor object
        c = self.conn.cursor()
        # Execute the SQL query to retrieve data from the table
        c.execute('SELECT "OMV_PETROM_station_id" FROM station_identification')
        # Fetch all the rows from the result set
        rows = c.fetchall()
        # Extract the values from the rows and store them in a list
        self.station_ids = ([row[0] for row in rows])
        # Close the cursor and connection
        c.close()

    def create_payload(self):
        payload = f"LNG=RO&CTRISO=ROU&VEHICLE=CAR&MODE=NEXTDOOR&BRAND=OMV&ID={self.station_ids[0]}&DISTANCE=0&HASH=" \
                  f"c072287be228e4c136126eff25336e4219072b8f&TS=1684328564"
        print(payload)
        return payload


    def scrape_station_info_and_upload_to_database(self, OMV_PETROM_station_id: str):
        data_dict = dict()
        # Prepare the payload for the POST request
        payload = f"LNG=RO&CTRISO=ROU&VEHICLE=CAR&MODE=NEXTDOOR&BRAND=OMV&ID={OMV_PETROM_station_id}&DISTANCE=0&HASH=c072287be228" \
                  "e4c136126eff25336e4219072b8f&TS=1684328564"
        # Send the POST request to the specified URL with payload and headers
        response = requests.post(self.url, data=payload, headers=self.headers)
        # Parse the response text as JSON and store it a variable
        raw_data_dict = json.loads(response.text)
        # Extract the station name from the raw data
        station_name = f'{raw_data_dict["siteDetails"]["brand_id"]} de pe strada ' \
                       f'{raw_data_dict["siteDetails"]["address_l"]}, {raw_data_dict["siteDetails"]["town_l"]}'
        # Store the station name in the data dictionary
        data_dict["station_name"] = station_name
        # Retrieve or create the station ID using the station name and OMV_PETROM_station_ID
        data_dict["station_id"] = self.get_or_create_station(st_name=station_name,
                                                             omv_petrom_station_id=OMV_PETROM_station_id)
        # Store the OMV PETROM station ID in the data dictionary
        data_dict["OMV_PETROM_station_id"] = raw_data_dict["siteDetails"]["sid"]

    def create_station_id_table(self):
        # Create a cursor object to interact with the database
        c = self.conn.cursor()
        # Execute the SQL query to create the station_identification table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS station_identification
                     (station_name TEXT PRIMARY KEY, station_id INTEGER, OMV_PETROM_station_id TEXT)''')
        # Close the cursor and connection
        c.close()

    def create_fueldb_table(self):
        # Create a cursor object to interact with the database
        c = self.conn.cursor()
        # Execute the SQL query to create the fuel_data table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS fuel_data
                     (date TEXT, station_id INTEGER, "Motorina Standard" REAL, "Motorina Premium" REAL, 
                     "Benzina Standard" REAL, "Benzina Premium" REAL, "GPL" REAL)''')
        # Close the cursor and connection
        c.close()

    def create_tables(self):
        self.create_fueldb_table()
        self.create_station_id_table()

    def get_or_create_station(self, st_name: str, omv_petrom_station_id: str):
        # Create a cursor object to interact with the database
        c = self.conn.cursor()
        # Check if the station exists in the station_identification table
        c.execute("SELECT station_id FROM station_identification WHERE station_name=?", (st_name,))
        result = c.fetchone()
        if result is None:
            # Get the next available ID
            c.execute("SELECT MAX(station_id) FROM station_identification")
            max_id = c.fetchone()[0]
            st_id = max_id + 1 if max_id is not None else 1
            # Insert the new station with the assigned ID
            c.execute(
                "INSERT INTO station_identification (station_name, station_id, OMV_PETROM_station_id) VALUES (?, ?, ?)",
                (st_name, st_id, omv_petrom_station_id))
            self.conn.commit()
            # Close the cursor and connection
            c.close()
            return st_id
        else:
            # Retrieve the existing ID
            st_id = result[0]
            # Close the cursor and connection
            c.close()
            return st_id

    def remove_station(self, OMV_PETROM_station_id):
        # Create a cursor object to interact with the database
        c = self.conn.cursor()
        # Define the table name
        table_name = "station_identification"
        # Construct the delete query
        delete_query = f"DELETE FROM {table_name} WHERE OMV_PETROM_station_id = ?"
        # Execute the delete query with the specified OMV_PETROM_station_id parameter
        c.execute(delete_query, (OMV_PETROM_station_id,))
        # Commit the changes to the database
        self.conn.commit()
        # Close the cursor and connection
        c.close()

    def delete_row(self, station_id: str, date: str):
        # Connect to the SQLite database and create cursor
        c = self.conn.cursor()
        # Variable with table name
        table_name = "fuel_data"
        # Prepare the SQL query to delete the row based on the provided parameters
        query = f"DELETE FROM {table_name} WHERE station_id = ? AND date = ?"
        # Execute the query
        c.execute(query, (station_id, date))
        # Commit the changes to the database
        self.conn.commit()
        # Close the cursor and connection
        c.close()

    def check_if_station_has_data_for_date(self, date: str, st_id: int):
        # Construct the SQL query to check if data exists for the given date and station ID
        existing_data_query = f"SELECT COUNT(*) FROM fuel_data WHERE Date = '{date}' AND station_id = {st_id}"
        # Execute the query and retrieve the count of existing data
        existing_data_count = pd.read_sql_query(existing_data_query, self.conn).iloc[0, 0]
        # Return True if data exists, False otherwise
        return existing_data_count != 0

    def change_fuel_data(self, table: str, data: dict):
        # Connect to the SQLite database and create cursor
        c = self.conn.cursor()
        # Construct the initial update query
        update_query = f"UPDATE {table} SET "
        for key, value in data.items():
            # Skip the "date" and "station_id" keys
            if key not in ["date", "station_id"]:
                # Append each key as a column name in the update query
                update_query += f'"{key}" = ?, '
        # Remove the trailing comma and space
        update_query = update_query.rstrip(', ')
        # Append the WHERE clause to match the specific row
        update_query += " WHERE date = ? AND station_id = ?"
        # Execute the update query with the corresponding values
        c.execute(update_query, list(data.values()))
        # Commit the changes to the database
        self.conn.commit()
        # Close the cursor and connection
        c.close()

    def retrieve_data_for_graph(self, station_id: int):
        c = self.conn.cursor()

        # Retrieve the station name
        station_name_query = f"SELECT station_name FROM station_identification WHERE station_id = '{station_id}'"
        c.execute(station_name_query)
        station_name = c.fetchone()[0]

        # Retrieve the list of dates
        date_query = f"SELECT date FROM fuel_data WHERE station_id = '{station_id}' ORDER BY date"
        c.execute(date_query)
        date_list = [row[0] for row in c.fetchall()]

        # Retrieve the fuel prices for each category
        fuel_query = f"SELECT [Motorina Standard], [Motorina Premium], [Benzina Standard], [Benzina Premium], [GPL] " \
                     f"FROM fuel_data WHERE station_id = {station_id} ORDER BY date"
        c.execute(fuel_query)
        results = c.fetchall()

        # Create empty lists to store the fuel prices
        motorina_standard_list = []
        motorina_premium_list = []
        benzina_standard_list = []
        benzina_premium_list = []
        gpl_list = []
        # Close the cursor and connection
        c.close()

        # Process the results and store in separate lists
        for row in results:
            motorina_standard = row[0]
            if motorina_standard is not None:
                motorina_standard_list.append(float(motorina_standard))

            motorina_premium = row[1]
            if motorina_premium is not None:
                motorina_premium_list.append(float(motorina_premium))

            benzina_standard = row[2]
            if benzina_standard is not None:
                benzina_standard_list.append(float(benzina_standard))

            benzina_premium = row[3]
            if benzina_premium is not None:
                benzina_premium_list.append(float(benzina_premium))

            gpl = row[4]
            if gpl is not None:
                gpl_list.append(float(gpl))

        # Return the collected data as a list
        return [station_name, date_list, motorina_standard_list, motorina_premium_list, benzina_standard_list,
                benzina_premium_list, gpl_list]

    def retrieve_station_name(self, station_id):
        # Create a cursor object
        c = self.conn.cursor()
        # Execute the SQL query to retrieve data from the table
        c.execute(f"SELECT station_name FROM 'station_identification' WHERE OMV_PETROM_station_id = '{station_id}'")
        # Fetch one from the result set
        result = c.fetchone()
        station_name = result[0] if result is not None else None
        # Close the cursor and connection
        c.close()
        return station_name

    def retrieve_station_id(self, name):
        # Create a cursor object
        c = self.conn.cursor()
        # Execute the SQL query to retrieve station ID
        c.execute(f"SELECT station_id FROM 'station_identification' WHERE station_name = '{name}'")
        st_id = c.fetchone()[0]
        # Close the cursor and connection
        c.close()
        return st_id

    def retrieve_all_stations_names_list(self):
        # Create a cursor object
        c = self.conn.cursor()
        # Execute the SQL query to retrieve all station names
        c.execute("SELECT station_name FROM station_identification")
        # Fetch all the rows and extract the station names
        station_names_list = [row[0] for row in c.fetchall()]
        # Close the cursor and connection
        c.close()
        return station_names_list


DB = DBConnection()
