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

## Kontrola architektury

- Model, widok i kontroler są rozdzielone: działa.
- Zapytania SQL są parametryzowane: działa.
- Operacje rezerwacji, startu i końca przejazdu są transakcyjne: działa.
- Test przeglądarkowy: niewykonany; ścieżkę potwierdzono klientem testowym
  Flask.

## Punkt 7 - kryteria odbioru

| Kryterium | Status | Dowód |
|---|---|---|
| Wszystkie 3-5 funkcji MVP i pełna ścieżka użytkownika | działa | T01-T09 |
| Rozdzielenie modelu, widoku i kontrolera | działa | `docs/architektura-mvc.md` |
| Przypadki poprawne i błędne oraz trwałość danych | działa | T04-T09 |
| README i oznaczenie stanu v1.0 | działa | README oraz niniejszy dokument |
