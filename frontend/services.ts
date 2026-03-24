import { SearchResult, RouteResult, Location } from '@/types';

export const fetchSearchResults = async (query: string): Promise<SearchResult[]> => {
  if (!query.trim()) return [];

  try {
    const response = await fetch(`/api/v1/search?searchVal=${encodeURIComponent(query)}`
    );
    return await response.json() || [];
  } catch (error) {
    console.error('Search error:', error);
    return [];
  }
};

export const fetchRoute = async (start: Location, end: Location, intervalMins: number): Promise<RouteResult[]> => {
  if (!start || !end) {
    throw new Error('Start and end points must be provided');
  }

  try {
    const startParam = encodeURIComponent(`${start.lat},${start.lon}`);
    const endParam = encodeURIComponent(`${end.lat},${end.lon}`);
    const response = await fetch(`/api/v1/routes?start=${startParam}&end=${endParam}&intervalMins=${intervalMins}`);
    return await response.json();
  }
  catch (error) {
    console.error('Route fetching error:', error);
    throw error;
  }
}
