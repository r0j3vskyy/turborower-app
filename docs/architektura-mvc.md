# Architektura MVC - TurboRower v1.0

TurboRower używa prostego MVC dla Flask + SQLite. W konwencji Flask funkcje
obsługujące trasy są kontrolerami, a pliki Jinja są widokami.

## Mapa odpowiedzialności

| Rola | Pliki | Odpowiedzialność |
|---|---|---|
| Model | `database/db.py`, `database/init_db.py` | Połączenie SQLite, schemat i dane demonstracyjne. |
| Model | `models/auth.py` | Użytkownicy, hashowanie i weryfikacja haseł. |
| Model | `models/vehicles.py` | Odczyt pojazdów oraz reguły rezerwacji i anulowania. |
| Model | `models/rides.py` | Rozpoczynanie, kończenie i odczyt przejazdów. |
| Kontroler | `app.py` | Konfiguracja Flask, rejestracja tras, sesja i ochrona logowania. |
| Kontroler | `controllers/auth.py` | Logowanie, rejestracja i wylogowanie. |
| Kontroler | `controllers/vehicles.py` | Lista, szczegóły, rezerwacja i anulowanie. |
| Kontroler | `controllers/rides.py` | Start, koniec przejazdu i historia. |
| Widok | `templates/*.html` | Prezentacja danych, formularze i komunikaty flash. |
| Widok | `static/css/style.css`, `static/js/app.js` | Wygląd i zachowanie interfejsu. |

## Przepływ przykładowej funkcji F03

1. Formularz w `templates/vehicle.html` wysyła POST do kontrolera
   `reserve_vehicle`.
2. `controllers/vehicles.py` przekazuje użytkownika, pojazd i czas do
   `models/vehicles.py`.
3. Model w transakcji sprawdza status `AVAILABLE`, zapisuje rezerwację i
   zmienia status pojazdu na `RESERVED`.
4. Kontroler pokazuje komunikat i przekierowuje do szczegółów pojazdu.

Operacje zmieniające stan używają transakcji SQLite i zapytań parametryzowanych.
Pojazd nie jest dostępny do rezerwacji, jeśli jego status zmienił się wcześniej
na inny niż `AVAILABLE`.

## Funkcje MVP i kryteria

| Funkcja | Model | Widok | Kryterium poprawności |
|---|---|---|---|
| F01 konto i logowanie | `models/auth.py` | `login.html` | Poprawne dane tworzą sesję, błędne pokazują komunikat. |
| F02 lista pojazdów | `models/vehicles.py` | `vehicles.html`, `vehicle.html` | Lista pokazuje tylko `AVAILABLE`. |
| F03 rezerwacja/anulowanie | `models/vehicles.py` | `vehicle.html` | Rezerwacja zmienia status, a anulowanie go przywraca. |
| F04 start/koniec przejazdu | `models/rides.py` | `vehicle.html` | Powstaje przejazd `ACTIVE`, potem `COMPLETED` z kosztem. |
| F05 historia | `models/rides.py` | `history.html` | Użytkownik widzi wyłącznie własne zakończone przejazdy. |
