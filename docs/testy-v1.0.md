# Testy TurboRower v1.0

## Środowisko i polecenie

- Windows, Python 3.13, Flask 3.1
- Baza: `instance/turborower.db`
- Test: klient testowy Flask, z osobną bazą tymczasową
- Uruchomienie: `py -3 -m database.init_db`, następnie
  `py -3 -m flask --app app run`

## Wyniki wykonane 2026-11-16

| ID | Scenariusz | Oczekiwany wynik | Wynik |
|---|---|---|---|
| T01 | GET `/login` | HTTP 200 | działa |
| T02 | Logowanie demo | Przekierowanie do `/vehicles` i sesja | działa |
| T03 | Lista pojazdów | Widoczne pojazdy `AVAILABLE` | działa |
| T04 | Rezerwacja dostępnego pojazdu | Rekord `ACTIVE`, pojazd `RESERVED` | działa |
| T05 | Rezerwacja zajętego pojazdu | Odmowa i komunikat błędu | działa |
| T06 | Start przejazdu bez własnej rezerwacji | Odmowa | działa |
| T07 | Start i koniec przejazdu | `COMPLETED`, czas i dodatni koszt | działa |
| T08 | Historia | Tylko własny zakończony przejazd | działa |
| T09 | Restart aplikacji | Dane pozostają w SQLite | działa |
| T10 | MVC: rejestracja konta | Kontroler wywołuje model i zapisuje rolę `USER` | działa |
| T11 | MVC: duplikat e-mail | Model zwraca konflikt, kontroler pokazuje komunikat | działa |
| T12 | MVC: role sesji | Administrator trafia do `/admin`, użytkownik jest blokowany | działa |
| T13 | MVC: dwa pojazdy i rezerwacje | Dwie rezerwacje pozostają aktywne jednocześnie | działa |
| T14 | MVC: start jednego przejazdu | Druga rezerwacja nie znika po rozpoczęciu przejazdu | działa |
| T15 | MVC: zakończenie przejazdu | Zapisują się status, czas, koszt i dystans | działa |
| T16 | MVC: historia i usterka | Historia działa, a usterka zmienia pojazd na `DAMAGED` | działa |
| T17 | MVC: panel administratora | Kontroler i model admina zwracają dane panelu | działa |
| T18 | MVC: zmiana statusu pojazdu | Administrator zmienia status przez model | działa |
| T19 | MVC: anulowanie rezerwacji admina | Rezerwacja zostaje anulowana, pojazd wraca do `AVAILABLE` | działa |
| T20 | MVC: rozwiązanie usterki | Zgłoszenie zostaje rozwiązane, pojazd wraca do `AVAILABLE` | działa |
| T21 | MVC: martwe szablony | Usunięte stare rejestracja/rezerwacja i drugi CSS nie są wymagane | działa |

## Testy Etapu 9 - wykonane 2026-11-18

Polecenie:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Wynik rzeczywisty: **6 testów uruchomiono i wszystkie 6 przeszło**.

| Test | Pokrycie |
|---|---|
| `test_login_invalid_and_valid` | Logowanie poprawne i błędne oraz role sesji |
| `test_registration_and_duplicate_email` | Rejestracja, role `USER` i duplikat e-mail |
| `test_vehicle_reservation_and_admin_denial` | Lista pojazdów, rezerwacja i blokada panelu admina |
| `test_ride_start_finish_history_and_fault` | Start, koniec, historia i zgłoszenie usterki |
| `test_admin_status_reservation_and_fault_actions` | Panel admina, status pojazdu i usterka |
| `test_expired_reservation_returns_vehicle` | Wygasanie rezerwacji i zwolnienie pojazdu |

Testy używają osobnej, tymczasowej bazy SQLite ustawionej przez
`TURBOROWER_DATABASE`. Nie zapisują danych do `instance/turborower.db`.

## Pozostała kontrola ręczna

Kontrola w przeglądarce u obu osób jest oznaczona jako **niewykonana**,
ponieważ nie został potwierdzony rzeczywisty przebieg obu użytkowników w UI.
Do wykonania ręcznie:

1. Uruchomić aplikację u jednej i drugiej osoby.
2. Zalogować konto demo i administratora.
3. Przejść rezerwację -> start -> koniec.
4. Sprawdzić wygasanie rezerwacji po 15 minutach.
5. Zgłosić usterkę i zamknąć ją jako administrator.
6. Sprawdzić dane po zatrzymaniu i ponownym starcie serwera.

## Kontrola architektury

- Model, widok i kontroler są rozdzielone: działa.
- Zapytania SQL są parametryzowane: działa.
- Operacje rezerwacji, startu i końca przejazdu są transakcyjne: działa.
- Test przeglądarkowy: niewykonany; ścieżkę potwierdzono klientem testowym
  Flask.

## Punkt 7 - kryteria odbioru

| Kryterium | Status | Dowód |
|---|---|---|
| Wszystkie 3-5 funkcji MVP i pełna ścieżka użytkownika | działa | T01-T21 |
| Rozdzielenie modelu, widoku i kontrolera | działa | `docs/architektura-mvc.md` |
| Przypadki poprawne i błędne oraz trwałość danych | działa | T04-T21 |
| README i oznaczenie stanu v1.0 | działa | README oraz niniejszy dokument |
