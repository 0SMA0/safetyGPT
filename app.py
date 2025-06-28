# app.py (Fully Instrumented for Debugging)

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

from get_route import get_google_maps_route
from get_hazards import get_311_data
from ai_analyzer_local import analyze_hazard_local
from shapely.geometry import Point, LineString
from googlemaps.convert import decode_polyline

app = Flask(__name__)
CORS(app)

def is_hazard_near_route(route_polyline, hazard_point, buffer_distance=0.0005):
    """
    HEAVILY INSTRUMENTED version to debug the geometry check.
    """
    # --- In-Function Debug Print 1 ---
    print(f"\n--- Running is_hazard_near_route for point: {hazard_point} ---")
    
    try:
        decoded_path = decode_polyline(route_polyline)
        # --- In-Function Debug Print 2 ---
        print(f"    - Decoded polyline into {len(decoded_path)} points.")

        if not decoded_path:
            print("    - [!!!] ERROR: Decoded path is empty. Returning False.")
            return False

        path_lon_lat = [(p['lng'], p['lat']) for p in decoded_path]
        
        route_line = LineString(path_lon_lat)
        hazard_loc = Point(hazard_point[1], hazard_point[0]) # (lon, lat)

        # --- In-Function Debug Print 3 (THE MOST IMPORTANT PART) ---
        # Instead of just checking if it's contained, we will calculate the actual distance.
        # The distance unit will be in degrees, but it's perfect for comparison.
        distance = route_line.distance(hazard_loc)
        
        print(f"    - Calculated distance from point to route: {distance:.6f} (in degrees)")
        print(f"    - Buffer (maximum allowed distance):      {buffer_distance:.6f} (in degrees)")

        # The final check
        is_near = distance < buffer_distance
        
        print(f"    - Is point within buffer? -> {is_near}")
        
        return is_near

    except Exception as e:
        print(f"    - [!!!] An exception occurred inside is_hazard_near_route: {e}")
        return False


@app.route('/get_safe_route', methods=['POST'])
def get_safe_route():
    data = request.json
    start = data.get('start')
    end = data.get('end')
    user_unsafe_categories = data.get('unsafe_categories', [])

    print("\n" + "="*50)
    print(f"NEW REQUEST: {start} -> {end}")
    print(f"RECEIVED UNSAFE CATEGORIES FROM USER: {user_unsafe_categories}")
    print("="*50)

    if not start or not end:
        return jsonify({"error": "Missing 'start' or 'end' location"}), 400

    walking_route_data = get_google_maps_route(start, end, mode="walking")
    transit_route_data = get_google_maps_route(start, end, mode="transit")

    walking_analysis = None
    if walking_route_data:
        hazards_on_route = []
        total_hazard_score = 0
        all_hazards_df = get_311_data(days_ago=3)
        print(f"Found {len(all_hazards_df)} total 311 reports to check against.")

        if not all_hazards_df.empty:
            # We will only print the detailed check for the first 5 hazards to avoid flooding the log
            for i, (_, hazard) in enumerate(all_hazards_df.iterrows()):
                polyline = walking_route_data['overview_polyline']['points']
                
                try:
                    lat = float(hazard['latitude'])
                    lon = float(hazard['longitude'])
                    hazard_location = (lat, lon)
                except (ValueError, TypeError):
                    if i < 5: print(f"WARNING: Could not parse coordinates for hazard. Skipping. Data: {hazard}")
                    continue
                
                # Only print the detailed check for the first few items
                if i < 5:
                    is_near = is_hazard_near_route(polyline, hazard_location)
                else:
                    # For the rest, run without the heavy logging to speed things up
                    is_near = is_hazard_near_route_quiet(polyline, hazard_location)

                if is_near:
                    print(f"\n[✓✓✓] SUCCESS! Found a hazard inside the corridor: '{hazard['complaint_type']}'")
                    ai_analysis = analyze_hazard_local(hazard['complaint_type'], hazard['descriptor'])
                    is_counted = ai_analysis['category'] in user_unsafe_categories
                    if is_counted:
                        total_hazard_score += ai_analysis['score']
                    hazards_on_route.append({
                        "complaint": hazard['complaint_type'],"descriptor": hazard['descriptor'],
                        "location": hazard_location,"ai_analysis": ai_analysis,"is_counted": is_counted
                    })
        
        walking_analysis = {
            "route_data": walking_route_data,
            "total_hazard_score": total_hazard_score,
            "hazards": hazards_on_route
        }
        print(f"\n>>> FINAL WALKING SCORE: {walking_analysis['total_hazard_score']} <<<")

    transit_analysis = {"route_data": transit_route_data, "warnings": transit_route_data.get('warnings', [])} if transit_route_data else None

    if not walking_analysis and not transit_analysis:
        return jsonify({"error": "Could not find any routes for the locations provided."}), 404

    return jsonify({"walking_route_analysis": walking_analysis, "transit_route_analysis": transit_analysis})


def is_hazard_near_route_quiet(route_polyline, hazard_point, buffer_distance=0.0005):
    """A non-logging version for performance."""
    try:
        decoded_path = decode_polyline(route_polyline)
        if not decoded_path: return False
        path_lon_lat = [(p['lng'], p['lat']) for p in decoded_path]
        route_line = LineString(path_lon_lat)
        hazard_loc = Point(hazard_point[1], hazard_point[0])
        return route_line.distance(hazard_loc) < buffer_distance
    except Exception:
        return False


if __name__ == '__main__':
    app.run(debug=True)