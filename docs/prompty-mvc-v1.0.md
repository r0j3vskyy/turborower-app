# Prompty MVC - TurboRower v1.0

Data opracowania: 2026-11-16. Narzędzie: GitHub Copilot w VS Code.

## P1 - plan MVP i mapa MVC

**Kontekst:** TurboRower to lokalna aplikacja Flask, HTML/CSS/JavaScript i
SQLite. Celem użytkownika jest znalezienie pojazdu, rezerwacja, przejazd i
sprawdzenie opłaty. Zakres MVP to F01-F05. Istnieją `app.py`, moduł
`database`, szablony Jinja i statyczne zasoby.

**Zadanie:** Zaplanuj prosty podział na model, widok i kontroler. Wskaż pliki
dla każdej funkcji oraz kryterium poprawności. Zachowaj istniejące trasy,
schemat bazy i działanie demonstracyjne.

**Wynik:** Model został podzielony na `models/auth.py`, `models/vehicles.py`
i `models/rides.py`; kontrolery na `controllers/auth.py`,
`controllers/vehicles.py` i `controllers/rides.py`; `app.py` rejestruje
trasy, a `templates/` pozostaje warstwą widoku.

## P2 - uporządkowanie MVC

**Kontekst:** Dotychczas `app.py` zawierał jednocześnie trasy i operacje SQL.

**Zadanie:** Wydziel model i kontrolery bez zmiany adresów URL, nazw endpointów,
statusów bazy ani przepływu F01-F05. Kontroler ma odbierać żądanie, wywołać
model i wybrać widok lub przekierowanie.

**Sprawdzenie:** `python -m compileall app.py controllers models database` oraz
test klienta Flask: `/login` odpowiada 200, a lista pojazdów po zalogowaniu
zawiera dane z SQLite.

## P3 - funkcje MVP

Wykonano osobno F01-F05: dane formularzy są walidowane w kontrolerze, reguły
statusów i zapis są w modelu, a zapytania używają parametrów. Przypadek
poprawny: konto demo loguje się, rezerwuje dostępny pojazd, rozpoczyna i kończy
przejazd. Przypadek błędny: rezerwacja pojazdu o statusie innym niż
`AVAILABLE` jest odrzucona komunikatem. Dane są zapisywane w
`instance/turborower.db`.

## P4 - przegląd i poprawka

**Niezgodność wykryta podczas przeglądu:** nieużywany, stary
`templates/reservation.html` odwoływał się do nieistniejących endpointów
(`start_ride`, `finish_ride` bez parametrów). Główny przepływ korzysta jednak
z `vehicle.html` i poprawnych endpointów parametryzowanych.

**Poprawka:** zachowano jeden aktualny przepływ MVC, usunięto zależność tras od
nieużywanego szablonu i potwierdzono nazwy endpointów testem klienta Flask.
Nie zmieniono zakresu funkcjonalnego ani schematu danych.

## Rzeczywisty rezultat

Kod został rozdzielony, aplikacja zachowuje istniejące adresy URL i dane
SQLite, a testy opisane w `docs/testy-v1.0.md` potwierdzają ścieżkę poprawną
oraz przypadki błędne.

## Punkt 6 - wykonanie zadań projektu

| Zadanie z instrukcji | Realizacja w TurboRower |
|---|---|
| 1. Doprecyzowanie | Przygotowano P1, mapę MVC i kryteria F01-F05. |
| 2. Szkielet i funkcje | Wykonano P2, a następnie wydzielono modele i kontrolery dla F01-F05. |
| 3. Próba i poprawka | Wykonano testy poprawne i błędne oraz przegląd P4; wynik zapisano w `docs/testy-v1.0.md`. |
| 4. Wersja 1.0 | README zawiera instalację, inicjalizację bazy i start aplikacji; projekt jest gotowy do oznaczenia `v1.0.0`. |

## Punkt 7 - potwierdzenie gotowości

- [x] Działa pięć funkcji MVP i pełna ścieżka od widoku do zapisu danych.
- [x] Model, widok i kontroler są rozdzielone i opisane w `docs/architektura-mvc.md`.
- [x] Sprawdzono przypadki poprawne i błędne, a dane są trwałe po restarcie.
- [x] README pozwala uruchomić projekt od początku, a wyniki mają status
  `działa` lub `niewykonany` zgodnie z rzeczywistym sposobem testu.

Do oddania przygotowano: README, `docs/architektura-mvc.md`,
`docs/prompty-mvc-v1.0.md` i `docs/testy-v1.0.md`.
