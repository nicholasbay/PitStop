var polyUtil = require('polyline-encoded');

export const decodePolyline = (polylineStr: string): [number, number][] => {
  return polyUtil.decode(polylineStr);
};
