# Technologie projektu TurboRower

## Wybrany zestaw

| Obszar | Technologia | Rola |
|---|---|---|
| Widoki | HTML, CSS, JavaScript | Prezentacja ekranów W01-W04, formularze i komunikaty |
| Serwer | Python 3.13 + Flask 3.1 | Routing, sesje, walidacja i reguły biznesowe |
| Dane | SQLite + moduł `sqlite3` | Trwały lokalny zapis użytkowników, pojazdów, rezerwacji i przejazdów |
| Kontrola wersji | Git + GitHub | Współpraca, historia zmian i Pull Requesty |
| Edytor | Visual Studio Code | Wspólna praca nad kodem i obsługa Source Control |

Wybraliśmy Python 3 z Flaskiem, ponieważ pozwala szybko zbudować lokalną
aplikację webową bez dodatkowego serwera aplikacyjnego. HTML, CSS i JavaScript
wystarczają do odwzorowania widoków opisanych w roadmapie v1. SQLite nie wymaga
osobnej instalacji serwera bazy danych i przechowuje dane w jednym lokalnym
pliku. Moduł `sqlite3` jest częścią standardowej biblioteki Pythona, dlatego
warstwa danych pozostaje prosta i łatwa do uruchomienia na obu komputerach.
Flask obsługuje sesję użytkownika, walidację formularzy i przejścia między
widokami. GitHub i VS Code zapewniają wersjonowanie oraz wspólną pracę
zespołu. Wersja v1 działa lokalnie i nie wymaga płatnych usług, kluczy API ani
rzeczywistych urządzeń GPS/GSM.

## Wymagania

- Python 3.13 lub nowszy Python 3,
- Git,
- Visual Studio Code,
- przeglądarka internetowa.

## Uruchomienie

W PowerShellu, w katalogu projektu:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m database.init_db
.\.venv\Scripts\python.exe -m flask --app app run
```

Następnie otwórz `http://127.0.0.1:5000`.
