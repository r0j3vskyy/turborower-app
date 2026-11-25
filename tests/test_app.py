from __future__ import annotations

import os
import gc
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta


TEST_DIRECTORY = tempfile.TemporaryDirectory()
TEST_DATABASE = Path(TEST_DIRECTORY.name) / "turborower-test.db"
os.environ["TURBOROWER_DATABASE"] = str(TEST_DATABASE)

from app import app
from database.db import get_connection
from database.init_db import initialize_database
from models.auth import create_user


class TurboRowerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = app.test_client()
        self.reset_database()

    def tearDown(self) -> None:
        self.client = None

    def reset_database(self) -> None:
        with get_connection() as connection:
            connection.execute("PRAGMA foreign_keys = OFF")
            for table in (
                "fault_reports",
                "rides",
                "reservations",
                "vehicles",
                "users",
            ):
                connection.execute(f"DELETE FROM {table}")
            connection.execute("DELETE FROM sqlite_sequence")
            connection.execute("PRAGMA foreign_keys = ON")
        initialize_database()

    def login_demo(self) -> None:
        response = self.client.post(
            "/login",
            data={
                "email": "demo@turborower.local",
                "password": "demo1234",
            },
        )
        self.assertEqual(response.status_code, 302)

    def login_admin(self) -> None:
        response = self.client.post(
            "/login",
            data={
                "email": "admin@turborower.local",
                "password": "admin1234",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_home_page_is_public_and_links_to_authentication(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Wypożycz pojazd elektryczny w Olsztynie".encode(), response.data)
        self.assertIn(b'href="/login"', response.data)
        self.assertIn(b'href="/register"', response.data)

    def test_vehicle_modal_is_available_for_authenticated_users(self) -> None:
        vehicle_id = self.get_vehicle_id("R-001")
        anonymous = self.client.get(f"/vehicles/{vehicle_id}/modal")
        self.assertEqual(anonymous.status_code, 302)

        self.login_demo()
        modal = self.client.get(f"/vehicles/{vehicle_id}/modal")
        self.assertEqual(modal.status_code, 200)
        self.assertIn(b"Zarezerwuj pojazd", modal.data)
        self.assertIn(b"Zg\xc5\x82o\xc5\x9b usterk\xc4\x99", modal.data)
        self.assertIn(b"vehicle-modal-map", modal.data)
        self.client.post(f"/vehicles/{vehicle_id}/reserve")
        reserved_modal = self.client.get(f"/vehicles/{vehicle_id}/modal")
        self.assertIn(b"Rozpocznij przejazd", reserved_modal.data)

    def test_pricing_is_public_and_configured_tariff_is_used_for_rides(self) -> None:
        pricing = self.client.get("/pricing")
        self.assertEqual(pricing.status_code, 200)
        self.assertIn(b"3.00", pricing.data)
        self.assertIn(b"0.50", pricing.data)

        original_start_fee = app.config["START_FEE"]
        original_rate = app.config["RATE_PER_MINUTE"]
        try:
            app.config["START_FEE"] = 4.25
            app.config["RATE_PER_MINUTE"] = 0.75
            self.login_demo()
            vehicle_id = self.get_vehicle_id("R-001")
            self.client.post(f"/vehicles/{vehicle_id}/reserve")
            with get_connection() as connection:
                reservation = connection.execute(
                    """
                    SELECT id FROM reservations
                    WHERE vehicle_id = ? AND status = 'ACTIVE'
                    """,
                    (vehicle_id,),
                ).fetchone()
            self.client.post(f"/reservations/{reservation['id']}/start")
            active_page = self.client.get("/activity")
            self.assertIn(b'data-start-fee="4.25"', active_page.data)
            self.assertIn(b'data-rate-per-minute="0.75"', active_page.data)
            self.assertIn("Przebyty dystans".encode(), active_page.data)
            with get_connection() as connection:
                ride = connection.execute(
                    "SELECT id FROM rides WHERE vehicle_id = ? AND status = 'ACTIVE'",
                    (vehicle_id,),
                ).fetchone()
                connection.execute(
                    "UPDATE rides SET started_at = ? WHERE id = ?",
                    (
                        (datetime.now() - timedelta(seconds=70)).isoformat(
                            timespec="seconds"
                        ),
                        ride["id"],
                    ),
                )
            self.client.post(f"/rides/{ride['id']}/end")
            with get_connection() as connection:
                completed = connection.execute(
                    "SELECT cost FROM rides WHERE id = ?",
                    (ride["id"],),
                ).fetchone()
            self.assertAlmostEqual(completed["cost"], 4.25 + 0.75 * 2)
        finally:
            app.config["START_FEE"] = original_start_fee
            app.config["RATE_PER_MINUTE"] = original_rate

    def get_vehicle_id(self, code: str) -> int:
        with get_connection() as connection:
            vehicle = connection.execute(
                "SELECT id FROM vehicles WHERE code = ?",
                (code,),
            ).fetchone()
        self.assertIsNotNone(vehicle)
        return int(vehicle["id"])

    def test_login_invalid_and_valid(self) -> None:
        invalid = self.client.post(
            "/login",
            data={
                "email": "demo@turborower.local",
                "password": "wrong",
            },
        )
        self.assertEqual(invalid.status_code, 200)

        self.login_demo()
        with self.client.session_transaction() as flask_session:
            self.assertIn("user_id", flask_session)
            self.assertEqual(flask_session["role"], "USER")

    def test_registration_and_duplicate_email(self) -> None:
        response = self.client.post(
            "/register",
            data={
                "name": "Nowy Użytkownik",
                "email": "mvc.test@turborower.local",
                "password": "testpass123",
            },
        )
        self.assertEqual(response.status_code, 302)

        with get_connection() as connection:
            user = connection.execute(
                "SELECT role FROM users WHERE email = ?",
                ("mvc.test@turborower.local",),
            ).fetchone()
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "USER")

        duplicate = self.client.post(
            "/register",
            data={
                "name": "Inna Nazwa",
                "email": "mvc.test@turborower.local",
                "password": "testpass123",
            },
        )
        self.assertEqual(duplicate.status_code, 200)

    def test_vehicle_reservation_and_admin_denial(self) -> None:
        self.login_demo()
        vehicles = self.client.get("/vehicles")
        self.assertEqual(vehicles.status_code, 200)
        self.assertIn(b"R-001", vehicles.data)

        reserve_vehicle_id = self.get_vehicle_id("R-001")
        reserve = self.client.post(
            f"/vehicles/{reserve_vehicle_id}/reserve",
            follow_redirects=True,
        )
        self.assertEqual(reserve.status_code, 200)
        self.assertIn(b"Zarezerwowany pojazd", reserve.data)

        denied_admin = self.client.get("/admin", follow_redirects=True)
        self.assertNotIn(b"Zarzad", denied_admin.data)

    def test_second_user_cannot_reserve_already_reserved_vehicle(self) -> None:
        self.login_demo()
        vehicle_id = self.get_vehicle_id("R-001")
        first_reservation = self.client.post(
            f"/vehicles/{vehicle_id}/reserve",
            follow_redirects=True,
        )
        self.assertEqual(first_reservation.status_code, 200)
        self.assertIn(b"Zarezerwowany pojazd", first_reservation.data)

        with get_connection() as connection:
            first_reservation_row = connection.execute(
                """
                SELECT user_id FROM reservations
                WHERE vehicle_id = ? AND status = 'ACTIVE'
                """,
                (vehicle_id,),
            ).fetchone()
        self.assertIsNotNone(first_reservation_row)

        create_user("Drugi użytkownik", "second@turborower.local", "testpass123")
        second_client = app.test_client()
        login = second_client.post(
            "/login",
            data={
                "email": "second@turborower.local",
                "password": "testpass123",
            },
        )
        self.assertEqual(login.status_code, 302)

        rejected_reservation = second_client.post(
            f"/vehicles/{vehicle_id}/reserve",
            follow_redirects=True,
        )
        self.assertEqual(rejected_reservation.status_code, 200)
        self.assertIn(
            "Ten pojazd nie jest już dostępny.".encode(),
            rejected_reservation.data,
        )

        with get_connection() as connection:
            vehicle = connection.execute(
                "SELECT status FROM vehicles WHERE id = ?",
                (vehicle_id,),
            ).fetchone()
            active_reservations = connection.execute(
                """
                SELECT user_id FROM reservations
                WHERE vehicle_id = ? AND status = 'ACTIVE'
                """,
                (vehicle_id,),
            ).fetchall()
        self.assertEqual(vehicle["status"], "RESERVED")
        self.assertEqual(len(active_reservations), 1)
        self.assertEqual(
            active_reservations[0]["user_id"],
            first_reservation_row["user_id"],
        )

    def test_ride_start_finish_history_and_fault(self) -> None:
        self.login_demo()
        vehicle_id = self.get_vehicle_id("R-001")
        fault_vehicle_id = self.get_vehicle_id("R-003")
        self.client.post(f"/vehicles/{vehicle_id}/reserve")

        with get_connection() as connection:
            reservation = connection.execute(
                """
                SELECT id FROM reservations
                WHERE vehicle_id = ? AND status = 'ACTIVE'
                LIMIT 1
                """,
                (vehicle_id,),
            ).fetchone()
        self.assertIsNotNone(reservation)

        start = self.client.post(
            f"/reservations/{reservation['id']}/start",
            follow_redirects=True,
        )
        self.assertEqual(start.status_code, 200)
        self.assertIn(b"Aktywny przejazd", start.data)

        with get_connection() as connection:
            ride = connection.execute(
                """
                SELECT id FROM rides
                WHERE vehicle_id = ? AND status = 'ACTIVE'
                LIMIT 1
                """,
                (vehicle_id,),
            ).fetchone()
        self.assertIsNotNone(ride)

        finish = self.client.post(
            f"/rides/{ride['id']}/end",
            follow_redirects=True,
        )
        self.assertEqual(finish.status_code, 200)

        with get_connection() as connection:
            completed = connection.execute(
                "SELECT status, duration_minutes, cost, distance_km FROM rides WHERE id = ?",
                (ride["id"],),
            ).fetchone()
        self.assertEqual(completed["status"], "COMPLETED")
        self.assertIsNotNone(completed["duration_minutes"])
        self.assertGreater(completed["cost"], 0)
        self.assertGreater(completed["distance_km"], 0)

        history = self.client.get("/history")
        self.assertEqual(history.status_code, 200)

        fault = self.client.post(
            f"/vehicles/{fault_vehicle_id}/fault",
            data={
                "category": "HAMULCE",
                "description": "Nie działa hamulec",
            },
        )
        self.assertEqual(fault.status_code, 302)
        with get_connection() as connection:
            status = connection.execute(
                "SELECT status FROM vehicles WHERE id = ?",
                (fault_vehicle_id,),
            ).fetchone()
        self.assertEqual(status["status"], "DAMAGED")

    def test_admin_status_reservation_and_fault_actions(self) -> None:
        self.login_admin()
        dashboard = self.client.get("/admin")
        self.assertEqual(dashboard.status_code, 200)

        vehicle_id = self.get_vehicle_id("R-001")
        response = self.client.post(
            f"/admin/vehicles/{vehicle_id}/status",
            data={"status": "CHARGING"},
        )
        self.assertEqual(response.status_code, 302)
        with get_connection() as connection:
            status = connection.execute(
                "SELECT status FROM vehicles WHERE id = ?",
                (vehicle_id,),
            ).fetchone()
        self.assertEqual(status["status"], "CHARGING")

        self.client.post("/logout")
        self.login_demo()
        fault_vehicle_id = self.get_vehicle_id("R-003")
        with get_connection() as connection:
            connection.execute(
                "UPDATE vehicles SET status = 'AVAILABLE' WHERE id = ?",
                (fault_vehicle_id,),
            )
        fault_post = self.client.post(
            f"/vehicles/{fault_vehicle_id}/fault",
            data={
                "category": "AKUMULATOR",
                "description": "Testowa usterka",
            },
        )
        self.assertEqual(fault_post.status_code, 302)

        with get_connection() as connection:
            fault = connection.execute(
                "SELECT id FROM fault_reports ORDER BY id DESC LIMIT 1"
            ).fetchone()
            damaged = connection.execute(
                "SELECT status FROM vehicles WHERE id = ?",
                (fault_vehicle_id,),
            ).fetchone()
        self.assertIsNotNone(fault)
        self.assertEqual(damaged["status"], "DAMAGED")

        self.client.post("/logout")
        self.login_admin()
        resolve = self.client.post(
            f"/admin/faults/{fault['id']}/resolve",
            follow_redirects=True,
        )
        self.assertEqual(resolve.status_code, 200)
        with get_connection() as connection:
            available = connection.execute(
                "SELECT status FROM vehicles WHERE id = ?",
                (fault_vehicle_id,),
            ).fetchone()
        self.assertEqual(available["status"], "AVAILABLE")

    def test_admin_cannot_override_active_fleet_state_or_open_fault(self) -> None:
        self.login_demo()
        vehicle_id = self.get_vehicle_id("R-001")
        self.client.post(f"/vehicles/{vehicle_id}/reserve")
        with get_connection() as connection:
            reservation = connection.execute(
                "SELECT id FROM reservations WHERE vehicle_id = ? AND status = 'ACTIVE'",
                (vehicle_id,),
            ).fetchone()

        self.client.post("/logout")
        self.login_admin()
        self.client.post(
            f"/admin/vehicles/{vehicle_id}/status",
            data={"status": "DAMAGED"},
        )
        with get_connection() as connection:
            status = connection.execute(
                "SELECT status FROM vehicles WHERE id = ?",
                (vehicle_id,),
            ).fetchone()
        self.assertEqual(status["status"], "RESERVED")

        self.client.post(f"/admin/reservations/{reservation['id']}/cancel")
        self.client.post("/logout")
        self.login_demo()
        self.client.post(
            f"/vehicles/{vehicle_id}/fault",
            data={"category": "HAMULCE", "description": "Problem z hamulcem"},
        )
        self.client.post("/logout")
        self.login_admin()
        self.client.post(
            f"/admin/vehicles/{vehicle_id}/status",
            data={"status": "AVAILABLE"},
        )
        with get_connection() as connection:
            damaged = connection.execute(
                "SELECT status FROM vehicles WHERE id = ?",
                (vehicle_id,),
            ).fetchone()
        self.assertEqual(damaged["status"], "DAMAGED")

    def test_resolving_faults_only_restores_vehicle_after_all_are_resolved(self) -> None:
        self.login_demo()
        vehicle_id = self.get_vehicle_id("R-003")
        for description in ("Usterka pierwsza", "Usterka druga"):
            self.client.post(
                f"/vehicles/{vehicle_id}/fault",
                data={"category": "HAMULCE", "description": description},
            )
        with get_connection() as connection:
            faults = connection.execute(
                "SELECT id FROM fault_reports WHERE vehicle_id = ? ORDER BY id",
                (vehicle_id,),
            ).fetchall()
        self.assertEqual(len(faults), 2)

        self.client.post("/logout")
        self.login_admin()
        self.client.post(f"/admin/faults/{faults[0]['id']}/resolve")
        with get_connection() as connection:
            status = connection.execute(
                "SELECT status FROM vehicles WHERE id = ?",
                (vehicle_id,),
            ).fetchone()
            still_open = connection.execute(
                "SELECT status FROM fault_reports WHERE id = ?",
                (faults[1]["id"],),
            ).fetchone()
        self.assertEqual(status["status"], "DAMAGED")
        self.assertEqual(still_open["status"], "OPEN")

        self.client.post(f"/admin/faults/{faults[1]['id']}/resolve")
        with get_connection() as connection:
            available = connection.execute(
                "SELECT status FROM vehicles WHERE id = ?",
                (vehicle_id,),
            ).fetchone()
        self.assertEqual(available["status"], "AVAILABLE")

    def test_fault_report_during_ride_keeps_vehicle_damaged_after_ride_ends(self) -> None:
        self.login_demo()
        vehicle_id = self.get_vehicle_id("R-001")
        self.client.post(f"/vehicles/{vehicle_id}/reserve")
        with get_connection() as connection:
            reservation = connection.execute(
                "SELECT id FROM reservations WHERE vehicle_id = ? AND status = 'ACTIVE'",
                (vehicle_id,),
            ).fetchone()
        self.client.post(f"/reservations/{reservation['id']}/start")
        with get_connection() as connection:
            ride = connection.execute(
                "SELECT id FROM rides WHERE vehicle_id = ? AND status = 'ACTIVE'",
                (vehicle_id,),
            ).fetchone()
        self.client.post(
            f"/vehicles/{vehicle_id}/fault",
            data={"category": "HAMULCE", "description": "Usterka w trakcie jazdy"},
        )
        self.client.post(f"/rides/{ride['id']}/end")
        with get_connection() as connection:
            status = connection.execute(
                "SELECT status FROM vehicles WHERE id = ?",
                (vehicle_id,),
            ).fetchone()
        self.assertEqual(status["status"], "DAMAGED")

    def test_users_cannot_modify_or_view_other_users_rides(self) -> None:
        self.login_demo()
        vehicle_id = self.get_vehicle_id("R-001")
        self.client.post(f"/vehicles/{vehicle_id}/reserve")
        with get_connection() as connection:
            reservation = connection.execute(
                "SELECT id FROM reservations WHERE vehicle_id = ? AND status = 'ACTIVE'",
                (vehicle_id,),
            ).fetchone()
        other_client = app.test_client()
        registration = other_client.post(
            "/register",
            data={
                "name": "Inny użytkownik",
                "email": "other.user@turborower.local",
                "password": "otherpass123",
            },
        )
        self.assertEqual(registration.status_code, 302)
        other_client.post(f"/reservations/{reservation['id']}/start")
        other_client.post(f"/reservations/{reservation['id']}/cancel")
        with get_connection() as connection:
            untouched_reservation = connection.execute(
                "SELECT status FROM reservations WHERE id = ?",
                (reservation["id"],),
            ).fetchone()
        self.assertEqual(untouched_reservation["status"], "ACTIVE")

        self.client.post(f"/reservations/{reservation['id']}/start")
        with get_connection() as connection:
            ride = connection.execute(
                "SELECT id FROM rides WHERE vehicle_id = ? AND status = 'ACTIVE'",
                (vehicle_id,),
            ).fetchone()
        self.assertIsNotNone(ride)
        other_client.post(f"/rides/{ride['id']}/end")
        other_client.post(f"/rides/{ride['id']}/cancel")
        with get_connection() as connection:
            unchanged = connection.execute(
                "SELECT status FROM rides WHERE id = ?",
                (ride["id"],),
            ).fetchone()
        self.assertEqual(unchanged["status"], "ACTIVE")

        self.client.post(f"/rides/{ride['id']}/end")
        other_history = other_client.get("/history")
        self.assertNotIn(b"R-001", other_history.data)

    def test_expired_reservation_returns_vehicle(self) -> None:
        self.login_demo()
        vehicle_id = self.get_vehicle_id("R-001")
        reserve = self.client.post(f"/vehicles/{vehicle_id}/reserve")
        self.assertEqual(reserve.status_code, 302)

        with get_connection() as connection:
            reservation = connection.execute(
                """
                SELECT id FROM reservations
                WHERE vehicle_id = ? AND status = 'ACTIVE'
                LIMIT 1
                """,
                (vehicle_id,),
            ).fetchone()
            connection.execute(
                "UPDATE reservations SET expires_at = '2000-01-01T00:00:00' WHERE id = ?",
                (reservation["id"],),
            )

        self.client.get("/activity")
        with get_connection() as connection:
            canceled = connection.execute(
                "SELECT status FROM reservations WHERE id = ?",
                (reservation["id"],),
            ).fetchone()
            vehicle_status = connection.execute(
                "SELECT status FROM vehicles WHERE id = ?",
                (vehicle_id,),
            ).fetchone()
        self.assertEqual(canceled["status"], "CANCELLED")
        self.assertEqual(vehicle_status["status"], "AVAILABLE")


def tearDownModule() -> None:
    gc.collect()
    TEST_DIRECTORY.cleanup()


if __name__ == "__main__":
    unittest.main()
