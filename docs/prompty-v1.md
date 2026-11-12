# Prompty i decyzje AI - TurboRower v1

## Cel dokumentu

Dokument zapisuje najważniejsze polecenia wykorzystane przy przygotowaniu
lokalnej wersji v1 oraz decyzje zespołu. Nie zawiera haseł, tokenów ani kluczy
dostępu.

## Wybrany czat AI

- Narzędzie: GitHub Copilot w VS Code.
- Cel: analiza instrukcji laboratoryjnych, przygotowanie dokumentacji,
  implementacja i weryfikacja lokalnej aplikacji.
- Zakres: projekt działa lokalnie i nie wymaga płatnych usług ani kluczy API.

## Decyzja technologiczna

Wybraliśmy HTML, CSS i JavaScript dla widoków, Python 3.13 z Flaskiem dla
serwera oraz SQLite z modułem `sqlite3` dla danych. Zestaw jest prosty do
uruchomienia na obu komputerach, nie wymaga osobnego serwera bazy danych
i odpowiada zakresowi v1 z roadmapy.

## Ważne prompty i rezultaty

### P1 - wybór technologii

> Na podstawie roadmapy v1 zaproponuj dwa proste zestawy technologii do
> lokalnego uruchomienia aplikacji TurboRower bez płatnych usług. Uwzględnij
> widoki W01-W04, tabele users, vehicles, reservations i rides oraz funkcje
> F01-F05. Wybierz prostszy wariant i uzasadnij decyzję.

**Rezultat:** wybrano Flask, HTML/CSS/JavaScript i SQLite.

### P2 - szkielet aplikacji

> Przygotuj lokalny szkielet TurboRower v1 w Pythonie 3 i Flasku z bazą
> SQLite. Dodaj strukturę katalogów, requirements.txt, .gitignore, widoki W01-W04,
> dane demonstracyjne i instrukcję uruchomienia. Zachowaj zakres v1.

**Rezultat:** utworzono `app.py`, moduł `database`, szablony Jinja, style,
JavaScript i konfigurację zależności.

### P3 - trwała baza danych

> Dodaj SQLite przez sqlite3 zgodnie z mapą v1. Utwórz tabele users, vehicles,
> reservations i rides, klucze PK/FK, kontrolę kluczy obcych, zapytania
> parametryzowane oraz polecenie inicjalizacji z fikcyjnym użytkownikiem
> i pojazdami. Dane mają przetrwać restart aplikacji.

**Rezultat:** baza jest inicjalizowana poleceniem
`python -m database.init_db`, a dane są zapisywane w `instance/turborower.db`.

### P4 - implementacja funkcji MVP

> Zaimplementuj kolejno F01-F05 dla TurboRower. Użytkownik ma móc się
> zarejestrować i zalogować, zobaczyć dostępne pojazdy, zarezerwować i
> anulować własną rezerwację, rozpocząć i zakończyć przejazd oraz zobaczyć
> historię. Sprawdzaj dane na serwerze i nie pozwalaj na rezerwację pojazdu,
> który nie jest dostępny.

**Rezultat:** funkcje zostały połączone w przepływ W01 -> W02 -> W03 -> W04.

## Własne poprawki i decyzje

- Zmieniono polecenie inicjalizacji bazy na `python -m database.init_db`,
  ponieważ moduł `database` musi być uruchamiany z katalogu głównego projektu.
- Dodano hashowanie haseł zamiast przechowywania haseł w tekście jawnym.
- Dodano sprawdzanie właściciela rezerwacji, przejazdu i historii po `user_id`.
- Dodano transakcje SQLite dla operacji rezerwacji, rozpoczęcia i zakończenia
  przejazdu.
- Zastosowano dane demonstracyjne, ponieważ rzeczywiste GPS, IoT i płatności
  są poza zakresem v1.

