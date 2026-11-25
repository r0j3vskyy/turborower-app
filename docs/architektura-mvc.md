# Architektura MVC - TurboRower v1.0.0

TurboRower jest aplikacją Flask z widokami Jinja i bazą SQLite. Warstwa
kontrolerów obsługuje żądania HTTP, modele realizują dostęp do danych i reguły
biznesowe, a szablony prezentują dane użytkownikowi.

## Podział odpowiedzialności

| Warstwa | Pliki | Odpowiedzialność |
|---|---|---|
| Punkt wejścia i trasy | [`app.py`](../app.py) | Konfiguracja Flask, inicjalizacja bazy, endpointy, sesja oraz dekoratory dostępu. |
| Baza danych | [`database/db.py`](../database/db.py), [`database/init_db.py`](../database/init_db.py) | Połączenia i zapytania SQLite, schemat oraz dane demonstracyjne. |
| Modele | [`models/auth.py`](../models/auth.py), [`models/vehicles.py`](../models/vehicles.py), [`models/rides.py`](../models/rides.py), [`models/admin.py`](../models/admin.py), [`models/vehicle_state.py`](../models/vehicle_state.py) | Użytkownicy, flota, rezerwacje, przejazdy, synchronizacja stanu pojazdów i operacje administracyjne. |
| Kontrolery | [`controllers/auth.py`](../controllers/auth.py), [`controllers/vehicles.py`](../controllers/vehicles.py), [`controllers/rides.py`](../controllers/rides.py), [`controllers/admin.py`](../controllers/admin.py) | Walidacja żądań, wywołania modeli, komunikaty i wybór odpowiedzi. |
| Widoki | [`templates/`](../templates/) | Strona główna, uwierzytelnianie, pojazdy, aktywność, historia i panel administratora. |
| Zasoby interfejsu | [`static/css/style.css`](../static/css/style.css), [`static/js/app.js`](../static/js/app.js) | Style oraz zachowanie interfejsu po stronie przeglądarki. |

`app.py` zawiera rejestrację tras oraz elementy infrastrukturalne Flask; logika
poszczególnych funkcji jest delegowana do kontrolerów i modeli.

## Zależności między modułami

- `app.py` rejestruje trasy i wywołuje kontrolery uwierzytelniania, pojazdów,
  przejazdów oraz administracji. Przy starcie inicjalizuje bazę; cyklicznie
  wywoływane przy żądaniach porządkowanie wygasłych rezerwacji korzysta
  z modelu pojazdów.
- Kontrolery wywołują modele i renderują szablony. `controllers/vehicles.py`
  korzysta z modeli pojazdów i przejazdów; pozostałe kontrolery korzystają
  z modeli odpowiadających ich funkcjom.
- Modele odczytują i zapisują dane przez `database/db.py`. Modele pojazdów,
  przejazdów i administracji korzystają też z
  `models/vehicle_state.py`, aby synchronizować stan floty.
- `database/init_db.py` używa połączeń z `database/db.py` do przygotowania
  schematu oraz danych demonstracyjnych.
- Szablony są renderowane przez kontrolery; `static/css/style.css` i
  `static/js/app.js` dostarczają interfejsowi style i zachowanie w przeglądarce.

## Przepływ rezerwacji (F03)

1. Zalogowany użytkownik wybiera dostępny pojazd z listy lub mapy
   (`templates/vehicles.html`) i używa formularza w
   `templates/vehicle_modal.html`.
2. Formularz wysyła żądanie `POST /vehicles/<vehicle_id>/reserve`.
   Zarejestrowana w `app.py` trasa wymaga zalogowania.
3. `controllers/vehicles.py::reserve_vehicle` przekazuje identyfikator
   zalogowanego użytkownika i pojazdu do `models/vehicles.py::reserve`.
4. Model odrzuca brakujący pojazd lub pojazd o statusie innym niż
   `AVAILABLE`. Warunkowo zmienia status na `RESERVED`, sprawdza wynik
   aktualizacji i zapisuje aktywną rezerwację.
5. Po sukcesie kontroler pokazuje komunikat i przekierowuje do aktywności.
   Jeśli pojazd nie jest już dostępny, informuje użytkownika i wraca do
   szczegółów pojazdu.

Operacje zmieniające stan używają transakcji SQLite, a wartości w zapytaniach
SQL są przekazywane jako parametry. Rezerwacja wygasa po 15 minutach; obsługa
wygaśnięcia przywraca pojazd do dostępnych, jeśli nie rozpoczęto przejazdu.

## Główne funkcje i ich stan

| Funkcja | Model | Kontroler / widok | Stan |
|---|---|---|---|
| Konto, logowanie i wylogowanie (F01) | `models/auth.py` | `controllers/auth.py`, `templates/login.html` | Zaimplementowano |
| Lista i szczegóły dostępnych pojazdów (F02) | `models/vehicles.py` | `controllers/vehicles.py`, `templates/vehicles.html`, `templates/vehicle.html` | Zaimplementowano |
| Rezerwacja i anulowanie (F03) | [`models/vehicles.py`](../models/vehicles.py) | [`app.py`](../app.py), [`controllers/vehicles.py`](../controllers/vehicles.py), [`templates/vehicle_modal.html`](../templates/vehicle_modal.html), [`templates/activity.html`](../templates/activity.html) | Zaimplementowano |
| Start, koniec i historia przejazdu (F04-F05) | `models/rides.py` | `controllers/rides.py`, `templates/history.html`, `templates/activity.html` | Zaimplementowano |
| Zgłoszenie usterki (F06) | `models/vehicles.py` | `controllers/vehicles.py`, `templates/fault_report.html` | Zaimplementowano |
| Monitoring i obsługa floty (F07) | `models/admin.py` | `controllers/admin.py`, `templates/admin.html` | Zaimplementowano |
| Cennik i strona główna | Konfiguracja `app.py` | Trasy Flask, `templates/pricing.html`, `templates/home.html` | Zaimplementowano |
| Szczegóły pojazdu w oknie modalnym | `models/vehicles.py` | `controllers/vehicles.py`, `templates/vehicle_modal.html`, lista i mapa pojazdów | Zaimplementowano |
| Wirtualne strefy z ograniczeniami (F08) | — | — | Planowane; poza zakresem v1.0.0 |

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
przeglądarkowej opisano w `docs/testy-v1.0.md`. Scenariusze F03 wraz z
wynikami prób są w [przepływach funkcji](przeplywy.md).
