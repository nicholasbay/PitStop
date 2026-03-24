from unittest.mock import patch

import pytest

from app.constants import DEFAULT_INTERVAL_MINS, AVG_SPEED_M_PER_MIN
from app.utils.find_parking import (
    _convert_time_interval_to_distance,
    _compute_cumsum_distances
)


class TestConvertTimeIntervalToDistance:
    def test_default_interval(self):  # Default: 30 mins
        result = _convert_time_interval_to_distance()
        assert result == DEFAULT_INTERVAL_MINS * AVG_SPEED_M_PER_MIN

    def test_custom_interval(self):
        result = _convert_time_interval_to_distance(interval_mins=60)
        assert result == 60 * AVG_SPEED_M_PER_MIN

    def test_negative_interval_raises_error(self):
        with pytest.raises(ValueError):
            _convert_time_interval_to_distance(-10)

    def test_zero_interval_raises_error(self):
        with pytest.raises(ValueError):
            _convert_time_interval_to_distance(0)

    def test_non_integer_interval_raises_error(self):
        with pytest.raises(TypeError):
            _convert_time_interval_to_distance("30")


class TestComputeCumsumDistances:
    def test_two_points(self):
        coords = [
            (103.68437, 1.35489),
            (103.69437, 1.35489)  # 0.01 degree east (~1.11 km at equator)
        ]
        result = _compute_cumsum_distances(coords)

        assert len(result) == 2
        assert result[0] == 0.0
        assert 1000 < result[1] < 1200


    def test_multiple_points(self):
        coords = [
            (103.68437, 1.35489),
            (103.69437, 1.35489),
            (103.71437, 1.35489),
        ]
        result = _compute_cumsum_distances(coords)

        assert len(result) == 3
        assert result[0] == 0.0
        assert 1000 < result[1] < 1200  # First leg
        assert 3200 < result[2] < 3600  # Second leg (cumulative)


    def test_single_point(self):
        coords = [
            (103.68437, 1.35489),
        ]
        result = _compute_cumsum_distances(coords)

        assert len(result) == 1
        assert result[0] == 0.0


    def test_identical_points(self):
        coords = [
            (103.68437, 1.35489),
            (103.68437, 1.35489),
            (103.68437, 1.35489),
        ]
        result = _compute_cumsum_distances(coords)

        assert len(result) == 3
        assert result[0] == 0.0
        assert result[1] == 0.0
        assert result[2] == 0.0


    def test_no_points_raises_error(self):
        coords = []
        with pytest.raises(ValueError):
            _compute_cumsum_distances(coords)


    def test_invalid_points_raises_error(self):
        coords = [
            ("hello", "world")
        ]
        with pytest.raises(TypeError):
            _compute_cumsum_distances(coords)


    def test_invalid_input_raises_error(self):
        coords = "hello world"
        with pytest.raises(TypeError):
            _compute_cumsum_distances(coords)


class TestQueryNearestParkingSpot:
    def test_valid_coord(self):
        coord = (103.68437, 1.35489)
        # mock_data = {
        #     "id": 1,
        #     "description": "BUS STOP 12345",
        #     "coord": 
        # }
        
        with patch('app.db.execute_query') as mock_execute_query:
            mock_execute_query.return_value
