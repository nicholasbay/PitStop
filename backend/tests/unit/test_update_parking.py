import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import requests

from app.utils import update_parking


class TestLoadLocations:
    def test_load_locations_success(self, tmp_path: Path):
        locations = [{"Latitude": 1.3, "Longitude": 103.8}]
        file_path = tmp_path / "locations.json"
        file_path.write_text(json.dumps(locations))

        result = update_parking._load_locations(file_path)

        assert result == locations

    def test_load_locations_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            update_parking._load_locations(Path("/not-found/locations.json"))

    def test_load_locations_invalid_json_raises(self):
        with patch("builtins.open", mock_open(read_data="{bad json")):
            with pytest.raises(json.JSONDecodeError):
                update_parking._load_locations(Path("locations.json"))


class TestFetchSpots:
    def test_fetch_spots_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"value": [{"Description": "A"}]}
        mock_response.raise_for_status.return_value = None

        with patch("app.utils.update_parking.requests.get", return_value=mock_response) as mock_get:
            result = update_parking._fetch_spots(1.3, 103.8)

        assert result == [{"Description": "A"}]
        mock_get.assert_called_once_with(
            update_parking.DATAMALL_URL,
            params={"Lat": 1.3, "Long": 103.8, "Dist": update_parking.DISTANCE_KM},
            headers={"AccountKey": update_parking.settings.DATAMALL_ACCOUNT_KEY},
            timeout=update_parking.TIMEOUT_S,
        )

    def test_fetch_spots_request_exception_returns_empty_list(self):
        with patch(
            "app.utils.update_parking.requests.get",
            side_effect=requests.exceptions.RequestException("network error"),
        ):
            result = update_parking._fetch_spots(1.3, 103.8)

        assert result == []

    def test_fetch_spots_invalid_json_returns_empty_list(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("bad", "doc", 0)

        with patch("app.utils.update_parking.requests.get", return_value=mock_response):
            result = update_parking._fetch_spots(1.3, 103.8)

        assert result == []


class TestSaveSnapshot:
    def test_save_snapshot_writes_ndjson(self):
        spots = [{"Description": "A"}, {"Description": "B"}]

        with patch("builtins.open", mock_open()) as m_open:
            update_parking._save_snapshot(spots)

        handle = m_open()
        expected_calls = [
            ((json.dumps(spots[0]) + "\n",),),
            ((json.dumps(spots[1]) + "\n",),),
        ]
        actual_calls = [tuple(call.args) for call in handle.write.call_args_list]
        assert actual_calls == [c[0] for c in expected_calls]

    def test_save_snapshot_io_error_is_handled(self):
        with patch("builtins.open", side_effect=IOError("disk full")):
            update_parking._save_snapshot([{"Description": "A"}])


class TestTransformSpots:
    def test_transform_spots_maps_fields_in_correct_order(self):
        spots = [
            {
                "Description": "Spot A",
                "Longitude": 103.9,
                "Latitude": 1.31,
                "RackType": "Type A",
                "RackCount": 10,
                "ShelterIndicator": "Y",
            }
        ]

        result = update_parking._transform_spots(spots)

        assert result == [
            (
                "Spot A",
                103.9,
                1.31,
                "Type A",
                10,
                "Y",
            )
        ]

    def test_transform_spots_empty_input_returns_empty_list(self):
        assert update_parking._transform_spots([]) == []


class TestUpsertBatch:
    def test_upsert_batch_success_commits(self):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cursor

        update_parking._upsert_batch(conn, [("A", 103.9, 1.31, "Type A", 10, "Y")])

        cursor.executemany.assert_called_once()
        conn.commit.assert_called_once()
        conn.rollback.assert_not_called()

    def test_upsert_batch_db_error_rolls_back(self):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.executemany.side_effect = update_parking.psycopg.Error("db error")
        conn.cursor.return_value.__enter__.return_value = cursor

        update_parking._upsert_batch(conn, [("A", 103.9, 1.31, "Type A", 10, "Y")])

        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()


class TestFetchAndUpdateSpots:
    def test_fetch_and_update_spots_happy_path_without_snapshot(self):
        locations = [
            {"Latitude": 1.3, "Longitude": 103.8},
            {"Latitude": 1.31, "Longitude": 103.81},
        ]
        fetched_1 = [{"Description": "A"}]
        fetched_2 = [{"Description": "B"}]
        transformed = [
            ("A", 103.8, 1.3, "Type A", 1, "Y"),
            ("B", 103.81, 1.31, "Type B", 2, "N"),
        ]

        conn = MagicMock()
        conn_cm = MagicMock()
        conn_cm.__enter__.return_value = conn
        conn_cm.__exit__.return_value = None

        with (
            patch("app.utils.update_parking._load_locations", return_value=locations),
            patch("app.utils.update_parking._fetch_spots", side_effect=[fetched_1, fetched_2]) as mock_fetch,
            patch("app.utils.update_parking._transform_spots", return_value=transformed) as mock_transform,
            patch("app.utils.update_parking._upsert_batch") as mock_upsert,
            patch("app.utils.update_parking._save_snapshot") as mock_snapshot,
            patch("app.utils.update_parking.get_db_connection", return_value=conn_cm),
        ):
            update_parking.fetch_and_update_spots(snapshot=False)

        assert mock_fetch.call_count == 2
        mock_transform.assert_called_once_with(fetched_1 + fetched_2)
        mock_upsert.assert_called_once_with(conn, transformed)
        mock_snapshot.assert_not_called()

    def test_fetch_and_update_spots_with_snapshot_calls_save_snapshot(self):
        locations = [{"Latitude": 1.3, "Longitude": 103.8}]
        fetched = [{"Description": "A"}]
        transformed = [("A", 103.8, 1.3, "Type A", 1, "Y")]

        conn = MagicMock()
        conn_cm = MagicMock()
        conn_cm.__enter__.return_value = conn
        conn_cm.__exit__.return_value = None

        with (
            patch("app.utils.update_parking._load_locations", return_value=locations),
            patch("app.utils.update_parking._fetch_spots", return_value=fetched),
            patch("app.utils.update_parking._transform_spots", return_value=transformed),
            patch("app.utils.update_parking._upsert_batch"),
            patch("app.utils.update_parking._save_snapshot") as mock_snapshot,
            patch("app.utils.update_parking.get_db_connection", return_value=conn_cm),
        ):
            update_parking.fetch_and_update_spots(snapshot=True)

        mock_snapshot.assert_called_once_with(fetched)

    def test_fetch_and_update_spots_skips_invalid_coordinates(self):
        locations = [
            {"Latitude": None, "Longitude": 103.8},
            {"Latitude": 1.3, "Longitude": 103.8},
        ]

        conn = MagicMock()
        conn_cm = MagicMock()
        conn_cm.__enter__.return_value = conn
        conn_cm.__exit__.return_value = None

        with (
            patch("app.utils.update_parking._load_locations", return_value=locations),
            patch("app.utils.update_parking._fetch_spots", return_value=[]) as mock_fetch,
            patch("app.utils.update_parking._transform_spots", return_value=[]),
            patch("app.utils.update_parking._upsert_batch"),
            patch("app.utils.update_parking.get_db_connection", return_value=conn_cm),
        ):
            update_parking.fetch_and_update_spots()

        mock_fetch.assert_called_once_with(1.3, 103.8)

    def test_fetch_and_update_spots_batches_by_batch_size(self):
        locations = [{"Latitude": 1.3, "Longitude": 103.8}]
        transformed = [
            ("A", 103.8, 1.3, "Type A", 1, "Y"),
            ("B", 103.81, 1.31, "Type B", 2, "N"),
            ("C", 103.82, 1.32, "Type C", 3, "Y"),
        ]

        conn = MagicMock()
        conn_cm = MagicMock()
        conn_cm.__enter__.return_value = conn
        conn_cm.__exit__.return_value = None

        with (
            patch("app.utils.update_parking._load_locations", return_value=locations),
            patch("app.utils.update_parking._fetch_spots", return_value=[{"Description": "A"}]),
            patch("app.utils.update_parking._transform_spots", return_value=transformed),
            patch("app.utils.update_parking._upsert_batch") as mock_upsert,
            patch("app.utils.update_parking.get_db_connection", return_value=conn_cm),
            patch.object(update_parking, "BATCH_SIZE", 2),
        ):
            update_parking.fetch_and_update_spots()

        assert mock_upsert.call_count == 2
        first_call_batch = mock_upsert.call_args_list[0].args[1]
        second_call_batch = mock_upsert.call_args_list[1].args[1]
        assert len(first_call_batch) == 2
        assert len(second_call_batch) == 1

    def test_fetch_and_update_spots_catches_top_level_exception(self):
        with patch("app.utils.update_parking._load_locations", side_effect=RuntimeError("boom")):
            update_parking.fetch_and_update_spots()
