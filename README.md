# TurboRower

System zarządzania siecią hulajnóg i rowerów miejskich.

## Zespół

- **Nazwa zespołu:** TurboRower
- **Damian Elsner** - indeks 180587, GitHub: [r0j3vskyy](https://github.com/r0j3vskyy)
- **Adrian Dunal** - indeks 180585, GitHub: [frothuwer](https://github.com/frothuwer)
- **Grupa laboratoryjna:** Grupa 1

Obie osoby odpowiadają za znajomość koncepcji, aktualność dokumentacji oraz
weryfikację zmian w repozytorium.

## Idea i problem

TurboRower jest systemem do zarządzania siecią miejskich hulajnóg i rowerów.
Rozwiązanie odpowiada na problem rozproszonej floty, której stan, lokalizacja i
dostępność muszą być na bieżąco kontrolowane. Z aplikacji korzystają przede
wszystkim osoby wypożyczające pojazdy oraz operatorzy odpowiedzialni za flotę.
Użytkownik powinien móc szybko znaleźć dostępny pojazd, zarezerwować go i
rozpocząć przejazd. Operator potrzebuje natomiast informacji o położeniu
pojazdów, poziomie baterii i ich stanie technicznym. W obecnym modelu takie
czynności mogą wymagać korzystania z kilku niespójnych narzędzi lub ręcznej
weryfikacji danych. TurboRower centralizuje informacje o pojazdach i obsługuje
najważniejsze etapy wypożyczenia w jednym systemie. Dzięki temu użytkownik
otrzymuje prostą ścieżkę od znalezienia pojazdu do zakończenia przejazdu, a
operator zyskuje uporządkowany podgląd floty. W pierwszej wersji system
skupia się na podstawowym procesie wypożyczenia, historii przejazdów i
rozliczeniu, bez uzależniania działania od rzeczywistego sprzętu IoT.

### Przykładowy scenariusz użycia

Użytkownik loguje się do aplikacji i otwiera mapę dostępnych pojazdów.
Wybiera pojazd znajdujący się w pobliżu, sprawdza jego podstawowe dane i
rezerwuje go. Następnie rozpoczyna przejazd, a system zapisuje czas oraz
wybrany pojazd. Po zakończeniu użytkownik kończy przejazd, a system nalicza
opłatę według taryfy i zapisuje przejazd w historii.

## Zakres funkcjonalny

| ID | Funkcjonalność | Zakres |
|---|---|---|
| F01 | Użytkownik może utworzyć konto i zalogować się do aplikacji. | MVP |
| F02 | Użytkownik może wyświetlić mapę oraz listę dostępnych pojazdów wraz z ich podstawowym stanem. | MVP |
| F03 | Użytkownik może zarezerwować dostępny pojazd i anulować własną rezerwację. | MVP |
| F04 | Użytkownik może rozpocząć i zakończyć przejazd, a system zapisuje jego podstawowe dane. | MVP |
| F05 | Użytkownik może zobaczyć historię przejazdów i naliczoną opłatę. | MVP |
| F06 | Użytkownik może zgłosić usterkę pojazdu. | Rozszerzenie |
| F07 | Operator może monitorować stan floty w panelu administracyjnym. | Rozszerzenie |
| F08 | Operator może definiować wirtualne strefy z ograniczeniami. | Rozszerzenie |

## Poza zakresem pierwszej wersji

- Integracja z rzeczywistymi modułami GPS/GSM i urządzeniami IoT w pojazdach.
- Integracja z prawdziwym operatorem płatności i pobieranie rzeczywistych środków.
- Automatyczne generowanie i obsługa zleceń przez ekipę terenową.

## Organizacja współpracy

Podział obowiązków jest równy i elastyczny. Każda osoba może realizować
aktualnie potrzebne zadania z zakresu interfejsu, logiki aplikacji, bazy
danych, integracji i testów. Przed rozpoczęciem większego zadania ustalamy
osobę odpowiedzialną, a gotową zmianę druga osoba sprawdza przed scaleniem.

- **Sposób kontaktu:** Discord/Messenger
- **Repozytorium GitHub:** [turborower-project](https://github.com/r0j3vskyy/turborower-project)
- **Przestrzeń LaboChat.com:** [LaboChat.com](https://turborower.labochat.com/)
- Ustalenia projektowe, zadania i ważne decyzje zapisujemy w repozytorium
  oraz w przestrzeni zespołu, a zmiany opisujemy merytorycznymi commitami.

## Dokumentacja

- [ProjectDocumentation.pdf](docs/ProjectDocumentation.pdf)
- [Presentation.pptx](docs/Presentation.pptx)
- [Roadmap-v1.md](docs/roadmap-v1.md)
- [Technologie](docs/technologie.md)
- [Prompty v1](docs/prompty-v1.md)
- [Testy v1](docs/testy-v1.md)

## Uruchomienie aplikacji v1

Wymagany jest Python 3.13 lub nowszy Python 3.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m database.init_db
.\.venv\Scripts\python.exe -m flask --app app run
```

Otwórz następnie `http://127.0.0.1:5000`. Zatrzymanie serwera: `Ctrl+C`.

### Konto demonstracyjne

- **E-mail:** `demo@turborower.local`
- **Hasło:** `demo1234`

Można również utworzyć własne konto przez formularz rejestracji. Baza SQLite
jest zapisywana lokalnie w `instance/turborower.db` i nie jest dodawana do Git.