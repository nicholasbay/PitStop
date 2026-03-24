'use client';

import { ArrowDownUp, ArrowRight, ClockFading, LoaderCircle } from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';

import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Location } from '@/types';
import { fetchSearchResults } from '@/services';
import { useRoutes } from '@/contexts/RoutesContext';
import { useUserPosition } from '@/hooks/useUserPosition';

import { Loading } from './Loading';

interface SearchBoxProps {
  onSelect: (location: Location) => void;
  placeholder: string;
  iconColor: 'blue' | 'red';
  value?: string;
}

function SearchBox({ onSelect, placeholder, iconColor, value }: SearchBoxProps) {
  const { position: userPosition } = useUserPosition();

  const [query, setQuery] = useState<string>('');
  const [results, setResults] = useState<Location[]>([]);
  const [loadingSearch, setLoadingSearch] = useState<boolean>(false);
  const [isFocused, setIsFocused] = useState<boolean>(false);

  useEffect(() => {
    if (value !== undefined) {
      setQuery(value);
    }
  }, [value]);

  const searchLocation = useCallback(async (query: string) => {
    const results = await fetchSearchResults(query);

    if (results.length === 0) {
      return [];
    }

    return results.map(result => ({
      lat: parseFloat(result.LATITUDE),
      lon: parseFloat(result.LONGITUDE),
      address: result.ADDRESS
    }));
  }, []);

  const useCurrentLocation = () => {
    if (userPosition) {
      onSelect({ lat: userPosition[0], lon: userPosition[1], address: 'Current Location' });
      setQuery('Current Location');
      setResults([]);
      setIsFocused(false);
    }
  };

  return (
    <div className='relative flex flex-col gap-3'>
      <div className='flex flex-row items-center gap-2'>
        <img className='w-8 h-8' src={`/icons/location-${iconColor}.png`} alt='Location Icon' />
        <Input
          type='text'
          placeholder={placeholder}
          value={query}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setTimeout(() => setIsFocused(false), 1000)}
          onChange={async (e) => {
            const value = e.target.value;
            setQuery(value);

            if (!value.trim()) {
              setResults([]);
              setLoadingSearch(false);
              return;
            }

            setLoadingSearch(true);
            const results = await searchLocation(value);
            setResults(results);
            setLoadingSearch(false);
          }}
        />
      </div>

      {isFocused && (
        <div className='absolute top-full left-10 right-0 mt-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md shadow-md z-50'>
          <ul className='max-h-[50dvh] overflow-y-auto'>
            {/* Use current location, if available */}
            {userPosition && (
              <li
                className='p-2 hover:bg-zinc-100 dark:hover:bg-zinc-700 cursor-pointer text-sm border-b border-zinc-200 dark:border-zinc-600'
                onClick={useCurrentLocation}
              >
                Use Current Location
              </li>
            )}

            {/* Loading indicator */}
            {loadingSearch && (
              <li className='p-2 text-sm text-zinc-500'>
                <Loading className='flex flex-row items-center justify-center gap-2' message='Searching...' iconSize={20} />
              </li>
            )}

            {/* Search results */}
            {!loadingSearch && query.length > 0 && results.length > 0 && (
              results.map((result, index) => (
                <li
                  key={index}
                  className='p-2 hover:bg-zinc-100 dark:hover:bg-zinc-700 cursor-pointer text-sm border-b last:border-b-0 border-zinc-200 dark:border-zinc-600'
                  onClick={() => {
                    onSelect(result);
                    setQuery(result.address);
                    setResults([]);
                    setIsFocused(false);
                  }}
                >
                  {result.address}
                </li>
              ))
            )}

            {/* Prompt to enter query */}
            {!loadingSearch && query.length === 0 && (
              <li className='p-2 text-sm text-zinc-500 text-center'>
                Enter a query to search
              </li>
            )}

            {/* No results message */}
            {!loadingSearch && query.length > 0 && results.length === 0 && (
              <li className='p-2 text-sm text-zinc-500 text-center'>
                No results found
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}

interface IntervalInputProps {
  value: number;
  onChange: (value: number) => void;
}

function IntervalInput({ value, onChange }: IntervalInputProps) {
  const [inputValue, setInputValue] = useState<string>(value.toString());

  useEffect(() => {
    setInputValue(value.toString());
  }, [value]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;

    // Allow empty input for easier editing
    if (val === '') {
      setInputValue('');
      return;
    }

    // Only allow numeric characters
    if (!/^\d+$/.test(val)) {
      return;
    }

    // Only allow positive integers
    const numValue = parseInt(val, 10);
    if (!isNaN(numValue) && numValue > 0) {
      setInputValue(val);
      onChange(numValue);
    }
  };

  const handleBlur = () => {
    // Reset to previous valid value if input is empty
    if (inputValue === '') {
      setInputValue(value.toString());
    }
  };

  return (
    <div className='flex flex-col gap-3'>
      <div className='flex flex-row items-center gap-2'>
        <ClockFading className='w-6 h-6 mx-1.5 text-zinc-600' />
        <Input
          type='text'
          placeholder='Interval (minutes)'
          value={inputValue}
          onChange={handleChange}
          onBlur={handleBlur}
        />
      </div>
    </div>
  );
}

interface InputRowProps {
  children: React.ReactNode;
  button?: React.ReactNode;
}

function InputRow({ children, button }: InputRowProps) {
  return (
    <div className='flex items-center gap-2'>
      <div className='flex-1 min-w-0'>
        {children}
      </div>
      {button && (
        <div className='shrink-0'>
          {button}
        </div>
      )}
    </div>
  );
}

interface InputPanelProps {
  onStartSelect: (location: Location) => void;
  onEndSelect: (location: Location) => void;
  onIntervalChange: (value: number) => void;
  onSubmit: () => void;
  startPoint?: Location | null;
  endPoint?: Location | null;
  intervalMins: number;
}

export function InputPanel({
  onStartSelect,
  onEndSelect,
  onIntervalChange,
  onSubmit,
  startPoint,
  endPoint,
  intervalMins }: InputPanelProps) {
  const { loading: loadingRoutes } = useRoutes();
  const [isRotated, setIsRotated] = useState<boolean>(false);

  const handleSwap = () => {
    setIsRotated(!isRotated);
    if (startPoint) onEndSelect(startPoint);
    if (endPoint) onStartSelect(endPoint);
  };

  const isFormValid = startPoint && endPoint && intervalMins > 0;

  return (
    <div className='p-3 md:p-4 space-y-3 md:space-y-4 bg-white rounded-lg shadow-lg'>
      <InputRow
        button={
          <Button
            className='hover:bg-zinc-100'
            variant='outline'
            size='icon'
            onClick={handleSwap}
            title="Swap Start and End Points"
          >
            <ArrowDownUp className={`h-4 w-4 md:h-6 md:w-6 transition-transform duration-300 ${isRotated ? 'rotate-180' : ''}`} />
          </Button>
        }
      >
        <SearchBox onSelect={onStartSelect} placeholder="Start Point" iconColor='blue' value={startPoint?.address} />
      </InputRow>

      {/* Spacer button for alignment */}
      <InputRow button={<Button className='invisible pointer-events-none' disabled size='icon' />}>
        <SearchBox onSelect={onEndSelect} placeholder="End Point" iconColor='red' value={endPoint?.address} />
      </InputRow>

      <InputRow
        button={
          <Button
            className='hover:bg-zinc-100'
            variant='outline'
            size='icon'
            onClick={onSubmit}
            disabled={!isFormValid || loadingRoutes}
            title="Find Routes"
          >
            {loadingRoutes ? <LoaderCircle className='h-4 w-4 animate-spin' /> : <ArrowRight className='h-4 w-4' />}
          </Button>
        }
      >
        <IntervalInput value={intervalMins} onChange={onIntervalChange} />
      </InputRow>
    </div>
  );
}
