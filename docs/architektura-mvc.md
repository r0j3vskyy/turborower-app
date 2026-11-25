# Architektura MVC - TurboRower v1.0.0

TurboRower jest aplikacją Flask z widokami Jinja i bazą SQLite. Warstwa
kontrolerów obsługuje żądania HTTP, modele realizują dostęp do danych i reguły
biznesowe, a szablony prezentują dane użytkownikowi.

## Podział odpowiedzialności

| Warstwa | Pliki | Odpowiedzialność |
|---|---|---|
| Punkt wejścia i trasy | `app.py` | Konfiguracja Flask, inicjalizacja bazy, endpointy, sesja oraz dekoratory dostępu. |
| Baza danych | `database/db.py`, `database/init_db.py` | Połączenia i zapytania SQLite, schemat oraz dane demonstracyjne. |
| Modele | `models/auth.py`, `models/vehicles.py`, `models/rides.py`, `models/admin.py` | Użytkownicy, flota, rezerwacje, przejazdy i operacje administracyjne. |
| Kontrolery | `controllers/auth.py`, `controllers/vehicles.py`, `controllers/rides.py`, `controllers/admin.py` | Walidacja żądań, wywołania modeli, komunikaty i wybór odpowiedzi. |
| Widoki | `templates/*.html` | Strona główna, uwierzytelnianie, pojazdy, aktywność, historia i panel administratora. |
| Zasoby interfejsu | `static/css/style.css`, `static/js/app.js` | Style oraz zachowanie interfejsu po stronie przeglądarki. |

`app.py` zawiera rejestrację tras oraz elementy infrastrukturalne Flask; logika
poszczególnych funkcji jest delegowana do kontrolerów i modeli.

## Przepływ rezerwacji (F03)

1. Użytkownik wysyła formularz z widoku `templates/vehicle.html` do trasy
   rezerwacji w `app.py`.
2. Trasa wymaga zalogowania i przekazuje żądanie do
   `controllers/vehicles.py`.
3. Kontroler wywołuje `models/vehicles.py`.
4. Model w transakcji sprawdza, czy pojazd ma status `AVAILABLE`, zapisuje
   rezerwację i zmienia status pojazdu na `RESERVED`.
5. Kontroler pokazuje komunikat i przekierowuje użytkownika do właściwego
   widoku.

Operacje zmieniające stan używają transakcji SQLite, a wartości w zapytaniach
SQL są przekazywane jako parametry. Rezerwacja wygasa po 15 minutach; obsługa
wygaśnięcia przywraca pojazd do dostępnych, jeśli nie rozpoczęto przejazdu.

## Główne funkcje

| Funkcja | Model | Kontroler / widok |
|---|---|---|
| Konto, logowanie i wylogowanie (F01) | `models/auth.py` | `controllers/auth.py`, `templates/login.html` |
| Lista i szczegóły dostępnych pojazdów (F02) | `models/vehicles.py` | `controllers/vehicles.py`, `templates/vehicles.html`, `templates/vehicle.html` |
| Rezerwacja i anulowanie (F03) | `models/vehicles.py` | `controllers/vehicles.py` |
| Start, koniec i historia przejazdu (F04-F05) | `models/rides.py` | `controllers/rides.py`, `templates/history.html`, `templates/activity.html` |
| Zgłoszenie usterki (F06) | `models/vehicles.py` | `controllers/vehicles.py`, `templates/fault_report.html` |
| Monitoring i obsługa floty (F07) | `models/admin.py` | `controllers/admin.py`, `templates/admin.html` |
| Cennik i strona główna | Konfiguracja `app.py` | Trasy Flask, `templates/pricing.html`, `templates/home.html` |
| Szczegóły pojazdu w oknie modalnym | `models/vehicles.py` | `controllers/vehicles.py`, `templates/vehicle_modal.html`, lista i mapa pojazdów |

F08 (wirtualne strefy z ograniczeniami) pozostaje poza zakresem wersji 1.0.0.
System nie integruje się z rzeczywistymi urządzeniami IoT ani operatorem
płatności; statystyki i trasy przejazdów są symulowane.

## Dostęp i role

- `login_required` chroni funkcje użytkownika.
- `admin_required` ogranicza operacje administracyjne do roli `ADMIN`.
- Zwykły użytkownik ma rolę `USER`.
- Lista i mapa wypożyczeń pokazują wyłącznie pojazdy `AVAILABLE`.
- Status `RESERVED` i `IN_USE` wynika z aktywnych rezerwacji i przejazdów;
  status pojazdu nie jest zwalniany, gdy pozostają nierozwiązane zgłoszenia
  usterek.
- Cennik i rozliczenie przejazdu korzystają z tych samych ustawień opłaty
  startowej oraz stawki minutowej.
- Aktywny przejazd wyświetla aktualizowany czas, koszt oraz symulowany
  przebyty dystans.

## Weryfikacja

Automatyczny zestaw testów znajduje się w `tests/test_app.py` i korzysta
z osobnej, tymczasowej bazy SQLite ustawianej przez
`TURBOROWER_DATABASE`. Wyniki testów automatycznych i ręcznej kontroli
przeglądarkowej opisano w `docs/testy-v1.0.md`.
