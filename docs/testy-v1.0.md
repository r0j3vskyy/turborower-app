# Testy TurboRower v1.0.0

## Środowisko

- Windows, Python 3.13, Flask 3.1.
- Produkcyjna baza SQLite: `instance/turborower.db`.
- Testy automatyczne korzystają z osobnej bazy tymczasowej wskazanej przez
  `TURBOROWER_DATABASE`.

## Testy automatyczne

Ostatnie wykonanie: **2026-11-25**.

Uruchom poleceniem:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Wynik: **13 testów uruchomiono i wszystkie 13 przeszło**.

| Test | Pokrycie |
|---|---|
| `test_admin_cannot_override_active_fleet_state_or_open_fault` | Zmiana statusu nie nadpisuje aktywnej rezerwacji ani otwartej usterki |
| `test_admin_status_reservation_and_fault_actions` | Panel administratora, status pojazdu i obsługa usterki |
| `test_expired_reservation_returns_vehicle` | Wygaśnięcie rezerwacji i zwolnienie pojazdu |
| `test_fault_report_during_ride_keeps_vehicle_damaged_after_ride_ends` | Usterka zgłoszona w trakcie przejazdu pozostaje statusem pojazdu po jego zakończeniu |
| `test_home_page_is_public_and_links_to_authentication` | Publiczna strona główna oraz linki do logowania i rejestracji |
| `test_login_invalid_and_valid` | Poprawne i błędne logowanie oraz role sesji |
| `test_pricing_is_public_and_configured_tariff_is_used_for_rides` | Publiczny cennik, wspólne ustawienia taryfy oraz koszt zapisany po przejeździe |
| `test_registration_and_duplicate_email` | Rejestracja użytkownika i odrzucenie duplikatu e-mail |
| `test_resolving_faults_only_restores_vehicle_after_all_are_resolved` | Pojazd wraca do dostępnych dopiero po rozwiązaniu wszystkich usterek |
| `test_ride_start_finish_history_and_fault` | Przejazd, statystyki, historia i zgłoszenie usterki |
| `test_users_cannot_modify_or_view_other_users_rides` | Własność rezerwacji/przejazdu i prywatność historii |
| `test_vehicle_modal_is_available_for_authenticated_users` | Szczegóły modalne, akcje pojazdu i ochrona logowaniem |
| `test_vehicle_reservation_and_admin_denial` | Lista i rezerwacja pojazdu oraz blokada panelu administratora |

Testy nie modyfikują `instance/turborower.db`.

## Kontrola ręczna

Kontrolę aplikacji w przeglądarce u obu osób oznaczono jako wykonaną.
Potwierdzono również zachowanie danych zapisanych w SQLite po ponownym
uruchomieniu aplikacji.

| ID | Scenariusz | Oczekiwany wynik | Wynik |
|---|---|---|---|
| R01 | Logowanie użytkownika i administratora | Poprawne strony i uprawnienia dla każdej roli | działa |
| R02 | Rezerwacja, rozpoczęcie i zakończenie przejazdu | Przejazd zapisany z podsumowaniem | działa |
| R03 | Rezerwacja bez rozpoczęcia przejazdu | Po 15 minutach pojazd wraca do dostępnych | działa |
| R04 | Zgłoszenie usterki i jej obsługa | Pojazd otrzymuje status uszkodzonego; administrator rozwiązuje zgłoszenie | działa |
| R05 | Ponowne uruchomienie aplikacji | Dane zapisane w SQLite pozostają dostępne | działa |
| R06 | Strona główna i nawigacja | Strona powitalna oraz przejścia do logowania i aplikacji działają | działa |
| R07 | Szczegóły pojazdu z listy i mapy | Modal pokazuje lokalizację oraz właściwe akcje pojazdu | działa |
| R08 | Statystyki aktywnego przejazdu | Czas, koszt i przebyty dystans aktualizują się w przeglądarce | działa |

## Kryteria odbioru

| Kryterium | Status | Dowód |
|---|---|---|
| Funkcje MVP i pełna ścieżka użytkownika | działa | Testy automatyczne i kontrola ręczna |
| Rozdzielenie modelu, widoku i kontrolera | działa | `docs/architektura-mvc.md` |
| Przypadki poprawne i błędne | działa | `tests/test_app.py` |
| Dokumentacja uruchomienia i testów | działa | `README.md` |
