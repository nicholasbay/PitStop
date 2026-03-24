import { LoaderCircle } from 'lucide-react';

interface LoadingProps {
  className: string;
  message?: string;
  iconSize?: number;
}

export function Loading({
  className,
  message = 'Loading...',
  iconSize = 32
}: LoadingProps) {
  return (
    <div className={className}>
      <LoaderCircle className="animate-spin" size={iconSize} />
      <p>{message}</p>
    </div>
  );
}