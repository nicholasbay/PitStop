from typing import Annotated

from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Depends,
    status
)
from fastapi.responses import JSONResponse
import requests

from app.config import Settings, get_settings
from app.constants import DEFAULT_INTERVAL_MINS
from app.onemap import ApiKeyManager, get_api_key_manager
from app.utils.find_parking import find_parking_spots_along_route
from app.utils.route import transform_route_data

load_dotenv()
router = APIRouter(
    prefix='/api/v1',
    tags=['v1']
)
ApiDep = Annotated[ApiKeyManager, Depends(get_api_key_manager)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get('/search')
def search(
    api_dep: ApiDep,
    settings_dep: SettingsDep,
    searchVal: str,
    pageNum: int = 1
):
    """
    Search for locations in Singapore using OneMap's Search API.

    - `searchVal` (string, required): Search query (address, building name, postal code, etc.)

    - `pageNum` (integer, optional): Page number of results to return (default: 1)
    """
    try:
        token = api_dep.get_api_key()
        response = requests.get(
            f'{settings_dep.ONEMAP_BASE_URL}/api/common/elastic/search?searchVal={searchVal}&returnGeom=Y&getAddrDetails=Y&pageNum={pageNum}',
            headers={'Authorization': f'Bearer {token}'}
        )
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])
        return JSONResponse(
            content=results,
            status_code=status.HTTP_200_OK
        )
    except requests.RequestException as e:  # Error with OneMap API request
        return JSONResponse(
            content={'error': str(e)},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        return JSONResponse(
            content={'error': str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get('/routes')
def get_routes(
    api_dep: ApiDep,
    settings_dep: SettingsDep,
    start: str,
    end: str,
    intervalMins: int = DEFAULT_INTERVAL_MINS
) -> JSONResponse:
    """
    Find cycling routes with intermediate parking spots based on user-defined time intervals.

    - `start` (string, required): Starting coordinates in `latitude,longitude` format (e.g., `1.2840,103.8514`)

    - `end` (string, required): Ending coordinates in `latitude,longitude` format

    - `intervalMins` (integer, optional): Time interval in minutes for parking spot placement (default: 30)
    """
    ONEMAP_ALT_ROUTES_KEY = 'alternativeroute'

    try:
        token = api_dep.get_api_key()
        response = requests.get(
            f'{settings_dep.ONEMAP_BASE_URL}/api/public/routingsvc/route?start={start}&end={end}&routeType=cycle',
            headers={'Authorization': f'Bearer {token}'}
        )
        response.raise_for_status()
        route_data = response.json()

        routes_with_parking = []  # For returning

        # Find parking spots along the main route
        spots = find_parking_spots_along_route(route_data, interval_mins=intervalMins)
        routes_with_parking.append(transform_route_data(route_data, spots))

        # Handle any alternative routes
        alt_routes = route_data.get(ONEMAP_ALT_ROUTES_KEY, [])
        for alt_route in alt_routes:
            alt_spots = find_parking_spots_along_route(alt_route, interval_mins=intervalMins)
            routes_with_parking.append(transform_route_data(alt_route, alt_spots))

        routes_with_parking.sort(key=lambda x: x['route_summary']['total_time_s'])  # Sort by total time in ascending order

        return JSONResponse(
            content=routes_with_parking,
            status_code=status.HTTP_200_OK
        )
    except requests.RequestException as e:  # Error with OneMap API request
        return JSONResponse(
            content={'error': str(e)},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        import traceback
        return JSONResponse(
            content={'error': str(e), 'trace': traceback.format_exc()},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
