import googlemaps
from datetime import datetime

# Replace with your actual API key
API_KEY = ''
gmaps = googlemaps.Client(key=API_KEY)

def get_google_maps_route(start, end, mode="walking"):
    """Fetches a route from Google Maps for a specific travel mode."""
    now = datetime.now()
    try:
        # We don't need alternatives for this new logic, we'll get the best route for each mode.
        directions_result = gmaps.directions(start,
                                             end,
                                             mode=mode,
                                             departure_time=now)
        
        if not directions_result:
            return None # Return None if no route is found
            
        return directions_result[0] # Return just the first, best route
    except Exception as e:
        print(f"Error fetching {mode} directions: {e}")
        return None

# --- Test it ---
if __name__ == '__main__':
    start_location = "Times Square, New York, NY"
    end_location = "Empire State Building, New York, NY"
    routes = get_google_maps_route(start_location, end_location)
    
    print(f"Found {len(routes)} routes.")
    # Each 'route' is a dictionary with lots of info, including a polyline
    # A polyline is an encoded string representing the route's path
    for i, route in enumerate(routes):
        print(f"Route {i+1} summary: {route['summary']}")
        print(f"Encoded Polyline: {route['overview_polyline']['points'][:50]}...")