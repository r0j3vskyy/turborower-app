# Instrukcje dla agentów

## Projekt i granice zmian

- TurboRower: Python, Flask, Jinja i SQLite. Zachowuj podział MVC.
- Przed zmianami przeczytaj `README.md`, `docs/architektura-mvc.md` oraz
  `docs/przeplywy.md`.
- Reguły biznesowe utrzymuj w modelach; `app.py` rejestruje trasy, kontrolery
  obsługują żądania, a szablony prezentują dane.
- Zmiany tras, schematu bazy, zależności i zachowania istniejących funkcji
  uzgadniaj z zespołem.
- Używaj testowej bazy tymczasowej. Nie ujawniaj haseł ani danych dostępowych.
- Nie wykonuj commitów, pushy ani wdrożeń bez wyraźnej prośby.

## Komendy z katalogu głównego

Uruchamiaj w PowerShell:

- Testy: `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v`
- Aplikacja: `.\.venv\Scripts\python.exe -m flask --app app run`
- Przegląd zmian: `git status --short` oraz `git diff --check`

Testy używają osobnej bazy SQLite wskazanej przez `TURBOROWER_DATABASE`.

## Sposób pracy

- Najpierw przedstaw plan i pliki, których dotyczy zmiana. Poczekaj na
  akceptację przed edycją.
- Jeśli kod różni się od dokumentacji albo planu, opisz rozbieżność przed
  zmianą.
- Po zmianie uruchom właściwe testy, podaj faktyczne wyniki i wymień pliki.
- Nie przedstawiaj nieuruchomionych prób jako zaliczonych.
