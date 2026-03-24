import re
from typing import List, Dict, Tuple

import polyline
import numpy as np

from app.constants import AVG_SPEED_M_PER_MIN, DEFAULT_SEARCH_RADIUS_M, EXPANDED_SEARCH_RADIUS_M
from app.db import execute_query


def find_parking_spots_along_route(route, interval_mins: int) -> List[Dict]:
    """
    Find parking spots spots along a given route within the specified interval distance.

    Args:
        route: Route object with geometry and summary.
        interval_mins (int): Time interval in minutes (default 30 mins).

    Returns:
        List of parking spots with their positions along the route.
    """
    interval_m = _convert_time_interval_to_distance(interval_mins)
    total_distance_m = route['route_summary']['total_distance']
    route_geometry = route['route_geometry']

    coords = polyline.decode(route_geometry, geojson=True)  # List of (lon, lat) tuples representing the route
    distances = _compute_cumsum_distances(coords)  # List of cumulative distances at each coordinate along the route

    ckpts = []
    cur_distance_m = interval_m

    while True:
        ckpts.append(cur_distance_m)  # First checkpoint at interval_m
        cur_distance_m += interval_m
        if cur_distance_m > total_distance_m:
            break

    if ckpts[-1] < total_distance_m:  # Add checkpoint at endpoint if not already included
        ckpts.append(total_distance_m)

    parking_spots = []
    for ckpt in ckpts:
        idx = (np.abs(distances - ckpt)).argmin()
        coord = coords[idx]

        nearest_spot = _query_nearest_parking_spot(coord)

        if nearest_spot:
            parking_spots.append(nearest_spot)
        else:
            nearest_spot = _query_nearest_parking_spot(coord, search_radius_m=EXPANDED_SEARCH_RADIUS_M)  # Expand search radius to 1km

            if nearest_spot:
                parking_spots.append(nearest_spot)

            # If still no parking spot found, skip this checkpoint

    return parking_spots


def _convert_time_interval_to_distance(interval_mins: int = 30) -> int:
    """
    Convert time interval in minutes to distance in meters.
    Assumes average cycling speed of 10 km/h (167 m/min).
    
    Args:
        interval_mins (int): Time interval in minutes.
        
    Returns:
        Integer representing distance in meters.
    """
    if type(interval_mins) is not int:
        raise TypeError("Interval must be an integer.")
    elif interval_mins <= 0:
        raise ValueError("Interval must be a positive integer.")

    return interval_mins * AVG_SPEED_M_PER_MIN


def _compute_cumsum_distances(coords: List[Tuple]) -> List[float]:
    """
    Compute cumulative distances along a list of coordinates.
    
    Args:
        coords: List of (lon, lat) tuples.
        
    Returns:
        List of cumulative distances for every coordinate in meters.
    """
    if type(coords) is not list:
        raise TypeError("Coordinates must be a list.")
    elif len(coords) == 0:
        raise ValueError("Coordinates list must not be empty.")

    coords_rad = np.radians(coords)

    # Shift array to compare i-th point with i+1-th point
    lon1, lat1 = coords_rad[:-1, 0], coords_rad[:-1, 1]
    lon2, lat2 = coords_rad[1:, 0], coords_rad[1:, 1]

    # Haversine Formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    EARTH_RADIUS_M = 6_371_000

    segment_dists = EARTH_RADIUS_M * c

    cumulative_dists = np.concatenate(([0], np.cumsum(segment_dists)))

    return cumulative_dists


def _query_nearest_parking_spot(coord: Tuple[float, float], search_radius_m: int = DEFAULT_SEARCH_RADIUS_M) -> Dict:
    """
    Query database for nearest parking spot within search radius.

    Args:
        coord (tuple): (lon, lat) tuple
        search_radius_m (int): Search radius in meters.

    Returns:
        Dictionary containing parking spot info or None
    """
    if type(coord) is not tuple:
        raise TypeError("Coordinate must be a tuple.")
    elif len(coord) != 2:
        raise ValueError("Coordinate must contain only two values.")
    elif type(coord[0]) is not float or type(coord[1]) is not float:
        raise TypeError("Coordinate values must be a float.")

    lon, lat = coord
    query = """
        SELECT
            id,
            description,
            ST_AsText(coordinates) AS coord,
            rack_type,
            rack_count,
            shelter_indicator,
            ST_Distance(
                coordinates::geography,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
            ) AS deviation  -- Casting to `geography` type converts distance from degrees to meters
        FROM parking_spots
        WHERE ST_DWithin(
            coordinates::geography,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
            %s
            )
        ORDER BY deviation ASC
        LIMIT 1;
    """
    result = execute_query(query, (lon, lat, lon, lat, search_radius_m))
    if not result:
        return None

    # Preprocess returned coordinates
    # Query returns: "POINT(123.456, 1.2345)"
    # Extract the coordinates and return as floats in (lon, lat) order
    pattern = r'POINT\(([-+]?[0-9]*\.?[0-9]+) ([-+]?[0-9]*\.?[0-9]+)\)'
    lon = float(re.search(pattern, result[0]["coord"]).group(1))
    lat = float(re.search(pattern, result[0]["coord"]).group(2))

    result[0]["coord"] = (lon, lat)
    return result[0]
