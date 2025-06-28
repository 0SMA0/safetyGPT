# get_hazards.py

import requests
import pandas as pd
from datetime import datetime, timedelta

# If you have an App Token, put it here. If not, it's okay, it will still work.
APP_TOKEN = '1Y1PWzBuDnFUTcKNDQ88wdgfF' 
DATASET_ID = "erm2-nwe9"

def get_311_data(days_ago=3):
    """
    Fetches 311 complaints from NYC OpenData using a more robust query.
    - Widens the date range.
    - Filters for relevant complaints that have location data.
    - Orders by date to get the most recent ones first.
    """
    date_filter = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%dT%H:%M:%S.000')
    
    # This list of complaint types is our primary filter.
    # We are including a broader set to increase our chances of getting data.
    complaint_types_filter = (
        "'Noise - Residential', 'UNSANITARY CONDITION', 'Homeless Encampment', "
        "'Homeless Person Assistance', 'Street Condition', 'Sidewalk Condition', "
        "'Illegal Parking', 'Blocked Driveway'"
    )

    # This is our new, more reliable query.
    # 1. $where: Filters for date, makes sure location exists, and checks complaint types.
    # 2. $order: Gets the most recent reports first.
    # 3. $limit: Fetches up to 1000 records to ensure we have a good pool of data.
    query = (
        f"https://data.cityofnewyork.us/resource/{DATASET_ID}.json?"
        f"$where=created_date > '{date_filter}' AND latitude IS NOT NULL AND complaint_type IN ({complaint_types_filter})"
        "&$order=created_date DESC"
        "&$limit=5000"
    )
    
    headers = {'X-App-Token': APP_TOKEN}
    
    try:
        response = requests.get(query, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            print(f"INFO: No matching 311 reports found in the last {days_ago} days.")
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        
        # Ensure required columns exist and have the correct data type
        df['latitude'] = pd.to_numeric(df['latitude'])
        df['longitude'] = pd.to_numeric(df['longitude'])
        
        # Fill in missing 'descriptor' values to prevent errors later
        if 'descriptor' not in df.columns:
            df['descriptor'] = 'N/A'
        df['descriptor'] = df['descriptor'].fillna('N/A')
            
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching 311 data: {e}")
        return pd.DataFrame()