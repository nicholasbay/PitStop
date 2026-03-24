import { useEffect } from 'react';
import { Marker, Polyline, Popup, useMap } from 'react-leaflet';

import { decodePolyline } from '@/utils';
import { DEFAULT_ZOOM } from '@/constants';
import { useRoutes } from '@/contexts/RoutesContext';

import { StartPointIcon, EndPointIcon, ParkingIcon, UserPositionIcon } from './Icons';

interface MapContentProps {
  userPosition: [number, number] | null;
}

export function MapContent({ userPosition }: MapContentProps) {
  const map = useMap();
  const { currentRoute } = useRoutes();

  // Center map on user position when it becomes available
  useEffect(() => {
    if (userPosition) {
      map.flyTo(userPosition, DEFAULT_ZOOM, { duration: 1.5 });
    }
  }, [userPosition, map]);

  // Center map on route start when currentRoute changes
  useEffect(() => {
    if (currentRoute) {
      const startCoord = decodePolyline(currentRoute.route_geometry)[0];
      map.flyTo(startCoord, DEFAULT_ZOOM, { duration: 1.5 });
    }
  }, [currentRoute, map]);

  const routeCoords: [number, number][] = decodePolyline(currentRoute?.route_geometry || '');

  return (
    <>
      {userPosition && (
        <Marker position={userPosition} icon={UserPositionIcon}>
          <Popup>Current Location</Popup>
        </Marker>
      )}

      {currentRoute && (
        <>
          <Polyline positions={routeCoords} color='red' weight={8} />

          <Marker 
            position={routeCoords[0]} 
            icon={StartPointIcon}
          >
            <Popup>
              <div>
                <h3 className='font-semibold'>Start Point</h3>
                <p>{currentRoute.route_summary.start_point}</p>
              </div>
            </Popup>
          </Marker>

          <Marker 
            position={routeCoords[routeCoords.length - 1]} 
            icon={EndPointIcon}
          >
            <Popup>
              <div>
                <h3 className='font-semibold'>End Point</h3>
                <p>{currentRoute.route_summary.end_point}</p>
              </div>
            </Popup>
          </Marker>
        </>
      )}

      {currentRoute?.parking_spots.map((spot) => (
        <Marker 
          key={spot.id}
          position={[spot.coordinates.lat, spot.coordinates.lon]}
          icon={ParkingIcon}
        >
          <Popup>
            <div className='space-y-2'>
              <h3 className='font-semibold text-base'>{spot.description}</h3>
              <div className='space-y-1 text-sm'>
                <div className='flex items-center gap-2'>
                  <span className='text-zinc-500'>Racks:</span>
                  <span>{spot.rack_count}</span>
                </div>
                <div className='flex items-center gap-2'>
                  <span className='text-zinc-500'>Type:</span>
                  <span>{spot.rack_type.replace(/_/g, ' ')}</span>
                </div>
                <div className='flex items-center gap-2'>
                  <span className='text-zinc-500'>Shelter:</span>
                  <span>{spot.shelter_indicator === 'Y' ? 'Yes' : 'No'}</span>
                </div>
                {spot.deviation_m && (
                  <div className='flex items-center gap-2'>
                    <span className='text-zinc-500'>Distance:</span>
                    <span>{Math.round(spot.deviation_m)}m from route</span>
                  </div>
                )}
              </div>
            </div>
          </Popup>
        </Marker>
      ))}
    </>
  );
}