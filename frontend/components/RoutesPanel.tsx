'use client';

import { Bike } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { RouteResult } from '@/types';
import { useRoutes } from '@/contexts/RoutesContext';

interface RouteItemProps {
  route: RouteResult;
  isSelected?: boolean;
  onSelect?: () => void;
}

function RouteItem({ route, isSelected, onSelect }: RouteItemProps) {
  const [showDetails, setShowDetails] = useState<boolean>(false);
  const [showSpots, setShowSpots] = useState<boolean>(false);

  return (
    <div 
      className={`max-w-full gap-2 p-2 rounded cursor-pointer transition-colors border ${
        isSelected
          ? 'bg-blue-50 border-blue-200'
          : 'hover:bg-zinc-100 border-zinc-200'
      }`}
      onClick={onSelect}
      title={`${isSelected ? 'Deselect' : 'Select'} route`}
    >
      <div className='flex flex-row items-center justify-between'>
        <Bike
          size={32}
          className={isSelected ? 'text-blue-600' : 'text-zinc-600'}
        />

        <div>
          <p className={`text-sm text-right font-semibold ${isSelected ? 'text-blue-600' : ''}`}>
            {Math.round(route.route_summary.total_time_s / 60)} min
          </p>
          <p className='text-sm text-right'>
            {(route.route_summary.total_distance_m / 1000).toFixed(2)} km
          </p>
        </div>
      </div>

      <div className='flex flex-col items-start'>
        <Button
          variant='link'
          className='px-0'
          onClick={(e) => {
            e.stopPropagation(); // Prevent triggering route selection
            setShowDetails(!showDetails);
          }}
        >
          {`${showDetails ? 'Hide' : 'Show'} Route Details`}
        </Button>
        {showDetails && (
          <div className='mt-2 p-2 max-h-30 w-full overflow-y-auto bg-zinc-50 rounded-md'>
            <ol className='list-decimal list-inside space-y-2 text-sm'>
              {route.route_instructions.map((instruction, idx) => (
                <li key={idx}>{instruction}</li>
              ))}
            </ol>
          </div>
        )}

        <Button
          variant='link'
          className='px-0'
          onClick={(e) => {
            e.stopPropagation(); // Prevent triggering route selection
            setShowSpots(!showSpots);
          }}
        >
          {`${showSpots ? 'Hide' : 'Show'} Parking Spots (${route.parking_spots.length})`}
        </Button>
        {showSpots && (
          <div className='mt-2 p-2 max-h-30 w-full overflow-y-auto bg-zinc-50 rounded-md'>
            <ol className='list-decimal list-inside space-y-2 text-sm'>
              {route.parking_spots.map((spot, idx) => (
                <li key={idx}>{spot.description}</li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}

interface RoutesPanelProps {
  routes: RouteResult[];
}

export function RoutesPanel({ routes }: RoutesPanelProps) {
  const { currentRoute, setCurrentRoute } = useRoutes();

  if (!routes || routes.length === 0) {
    return null;
  }

  const handleRouteClick = (route: RouteResult) => {
    if (currentRoute === route) {
      setCurrentRoute(null);
    } else {
      setCurrentRoute(route);
    }
  };

  const startPoint = routes[0].route_summary.start_point || 'START POINT';
  const endPoint = routes[0].route_summary.end_point || 'END POINT';

  return (
    <div className='p-3 md:p-4 space-y-1 bg-white rounded-lg shadow-lg w-full'>
      <h2
        className='text-sm md:text-md font-semibold mb-2 line-clamp-1'
        title={`${startPoint} to ${endPoint}`}
      >
        {startPoint} to {endPoint}
      </h2>
      {routes.map((route, index) => (
        <RouteItem
          key={index}
          route={route}
          isSelected={currentRoute === route}
          onSelect={() => handleRouteClick(route)}
        />
      ))}
    </div>
  );
}
