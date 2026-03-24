import json
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

import pytest

from app.db import get_db_connection
from app.utils import update_parking


def _is_db_configured() -> bool:
    required = [
        update_parking.settings.POSTGRES_HOST,
        update_parking.settings.POSTGRES_DATABASE,
        update_parking.settings.POSTGRES_USER,
        update_parking.settings.POSTGRES_PASSWORD,
    ]
    return all(required)


@contextmanager
def _db_or_skip():
    if not _is_db_configured():
        pytest.skip("PostgreSQL environment variables are not configured")

    try:
        with get_db_connection() as conn:
            yield conn
    except Exception as exc:
        pytest.skip(f"PostgreSQL not reachable for integration test: {exc}")


def _cleanup_descriptions(conn, descriptions: list[str]) -> None:
    if not descriptions:
        return

    with conn.cursor() as cursor:
        cursor.execute(
            "DELETE FROM parking_spots WHERE description = ANY(%s)",
            (descriptions,),
        )
        conn.commit()


class TestUpsertBatchIntegration:
    def test_upsert_batch_inserts_and_updates_records(self):
        unique = uuid4().hex[:8]
        desc_1 = f"integration-{unique}-A"
        desc_2 = f"integration-{unique}-B"

        initial_batch = [
            (desc_1, 103.9001, 1.3001, "Type A", 10, "Y"),
            (desc_2, 103.9002, 1.3002, "Type B", 20, "N"),
        ]
        updated_batch = [
            (desc_1, 103.9101, 1.3101, "Type A", 99, "N"),
            (desc_2, 103.9002, 1.3002, "Type B", 20, "N"),
        ]

        with _db_or_skip() as conn:
            _cleanup_descriptions(conn, [desc_1, desc_2])
            update_parking._upsert_batch(conn, initial_batch)
            update_parking._upsert_batch(conn, updated_batch)

            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT description, rack_count, shelter_indicator
                    FROM parking_spots
                    WHERE description = ANY(%s)
                    ORDER BY description
                    """,
                    ([desc_1, desc_2],),
                )
                rows = cursor.fetchall()

            _cleanup_descriptions(conn, [desc_1, desc_2])

        assert len(rows) == 2
        row_by_desc = {row[0]: row for row in rows}
        assert row_by_desc[desc_1][1] == 99
        assert row_by_desc[desc_1][2] == "N"
        assert row_by_desc[desc_2][1] == 20
        assert row_by_desc[desc_2][2] == "N"


class TestFetchAndUpdateIntegration:
    def test_fetch_and_update_spots_writes_expected_records(self, tmp_path: Path):
        unique = uuid4().hex[:8]
        desc_1 = f"integration-{unique}-spot-1"
        desc_2 = f"integration-{unique}-spot-2"

        locations = [
            {"Latitude": 1.3001, "Longitude": 103.9001},
            {"Latitude": 1.3002, "Longitude": 103.9002},
        ]
        locations_path = tmp_path / "locations.json"
        locations_path.write_text(json.dumps(locations))

        class DummyResponse:
            def __init__(self, payload: dict):
                self._payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self._payload

        payloads = [
            {
                "value": [
                    {
                        "Description": desc_1,
                        "Longitude": 103.9001,
                        "Latitude": 1.3001,
                        "RackType": "Type A",
                        "RackCount": 7,
                        "ShelterIndicator": "Y",
                    }
                ]
            },
            {
                "value": [
                    {
                        "Description": desc_2,
                        "Longitude": 103.9002,
                        "Latitude": 1.3002,
                        "RackType": "Type B",
                        "RackCount": 11,
                        "ShelterIndicator": "N",
                    }
                ]
            },
        ]

        with _db_or_skip() as conn:
            _cleanup_descriptions(conn, [desc_1, desc_2])

            with patch("app.utils.update_parking.LOCATIONS_FILE", locations_path), patch(
                "app.utils.update_parking.requests.get",
                side_effect=[DummyResponse(payloads[0]), DummyResponse(payloads[1])],
            ):
                update_parking.fetch_and_update_spots(snapshot=False)

            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT description, rack_count, shelter_indicator
                    FROM parking_spots
                    WHERE description = ANY(%s)
                    ORDER BY description
                    """,
                    ([desc_1, desc_2],),
                )
                rows = cursor.fetchall()

            _cleanup_descriptions(conn, [desc_1, desc_2])

        assert len(rows) == 2
        row_by_desc = {row[0]: row for row in rows}
        assert row_by_desc[desc_1][1] == 7
        assert row_by_desc[desc_1][2] == "Y"
        assert row_by_desc[desc_2][1] == 11
        assert row_by_desc[desc_2][2] == "N"
