import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogOverlay,
  DialogTitle
} from '@/components/ui/dialog';

interface InfoDialogProps {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}

export function InfoDialog({isOpen, setIsOpen}: InfoDialogProps) {
  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      {/* Ensure dialog overlay and content appear above map tiles */}
      <DialogOverlay className='z-1000' />

      <DialogContent className='z-1000'>
        <DialogHeader>
          <DialogTitle className='flex items-center'>
            <img src='/icons/distance.png' alt='App Icon' className='w-8 h-8 mr-2' />
            PitStop
          </DialogTitle>
          <DialogDescription>
            Plan cycling routes that stay within bike-sharing time limits.
          </DialogDescription>
        </DialogHeader>

        <div className='max-h-[50dvh] overflow-y-auto space-y-2'>
          <h2 className='text-lg font-semibold'>How to Use</h2>
          <ol className='list-decimal list-inside space-y-1 pb-1'>
            <li>Enter a start point in the "Start Point" field.</li>
            <li>Enter an end point in the "End Point" field.</li>
            <li>Specify the desired interval (in minutes) between parking spots.</li>
            <li>Click the button to find routes with the intermediate parking spots.</li>
          </ol>

          <h2 className='text-lg font-semibold'>Icons</h2>
          <ul className='list-none list-inside space-y-1 pb-1'>
            <li className='flex items-center'>
              <img src='/icons/location-blue.png' alt="Start Point" className='w-8 h-8 inline-block mr-2'/>
              Start Point
            </li>
            <li className='flex items-center'>
              <img src='/icons/location-red.png' alt="End Point" className='w-8 h-8 inline-block mr-2'/>
              End Point
            </li>
            <li className='flex items-center'>
              <img src='/icons/bike-parking.png' alt="Parking Spot" className='w-8 h-8 inline-block mr-2'/>
              Parking Spot
            </li>
            <li className='flex items-center'>
              <img src='/icons/position.png' alt="Current Location" className='w-8 h-8 inline-block mr-2'/>
              Current Location
            </li>
          </ul>

          <h2 className='text-lg font-semibold'>Acknowledgments</h2>
          <ul className='list-none list-inside space-y-1'>
            <li>
              Map tiles, location search, and routing data provided by <a href='https://www.onemap.gov.sg/apidocs/' className='text-blue-600 underline' target='_blank' rel='noopener noreferrer'>OneMap API</a>.
            </li>
            <li>
              Parking spot data provided by <a href='https://datamall.lta.gov.sg/content/datamall/en.html' className='text-blue-600 underline' target='_blank' rel='noopener noreferrer'>LTA DataMall</a>.
            </li>
            <li>
              All icons provided by <a href='https://www.flaticon.com/' className='text-blue-600 underline' target='_blank' rel='noopener noreferrer'>Flaticon</a> and <a href='https://lucide.dev' className='text-blue-600 underline' target='_blank' rel='noopener noreferrer'>Lucide</a>.
            </li>
          </ul>
        </div>

        <DialogFooter className='sm:justify-center'>
          <Button
            className='flex items-center gap-2'
            variant='ghost'
            asChild
          >
            <a 
              href='https://github.com/nicholasbay/PitStop'
              target='_blank'
              rel='noopener noreferrer'
              className='flex items-center gap-2'
            >
              <img src='/icons/github.png' alt='GitHub Icon' className='w-5 h-5' />
              View on GitHub
            </a>
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}