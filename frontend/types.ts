
export interface SearchResult {
  SEARCHVAL: string;
  BLK_NO: string;
  ROAD_NAME: string;
  BUILDING_NAME: string;
  ADDRESS: string;
  POSTAL: string;
  X: string;
  Y: string;
  LATITUDE: string;
  LONGITUDE: string;
}

export interface RouteResult {
  route_geometry: string;
  route_instructions: string[];
  route_summary: {
    start_point: string;
    end_point: string;
    total_distance_m: number;
    total_time_s: number;
  };
  parking_spots: ParkingSpot[];
}

export interface ParkingSpot {
  id: number;
  description: string;
  coordinates: {
    lat: number;
    lon: number;
  };
  rack_type: string;
  rack_count: number;
  shelter_indicator: string;
  deviation_m?: number;
}

export interface Location {
  lat: number;
  lon: number;
  address: string;
}

export interface RoutesContextType {
  routes: RouteResult[];
  currentRoute: RouteResult | null;
  loading: boolean;
  error: string | null;
  setRoutes: (routes: RouteResult[]) => void;
  setCurrentRoute: (route: RouteResult | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearRoutes: () => void;
}
