# Testy wersji v1 - TurboRower

## Środowisko

- Windows
- Python 3.13.2
- Flask 3.1.3
- SQLite
- Testy wykonano przy użyciu klienta testowego Flask.
- Baza testowa: `instance/turborower.db`.

## Wyniki

| ID | Scenariusz | Oczekiwany wynik | Rzeczywisty wynik | Status |
|---|---|---|---|---|
| T01 | Otworzenie `/login` | Widok logowania odpowiada kodem 200. | Widok odpowiedział kodem 200. | działa |
| T02 | Logowanie kontem demo | Użytkownik trafia do listy pojazdów. | Użytkownik trafił do listy pojazdów. | działa |
| T03 | Wyświetlenie dostępnych pojazdów | Widoczne są pojazdy ze statusem `AVAILABLE`. | Widoczny był pojazd R-001. | działa |
| T04 | Rezerwacja R-001 | Powstaje aktywna rezerwacja w bazie. | Rezerwacja została zapisana, a pojazd otrzymał status `RESERVED`. | działa |
| T05 | Rozpoczęcie przejazdu | Powstaje aktywny przejazd. | Przejazd został zapisany ze statusem `ACTIVE`. | działa |
| T06 | Zakończenie przejazdu | Przejazd otrzymuje czas, koszt i status `COMPLETED`. | Przejazd otrzymał czas, dodatni koszt i status `COMPLETED`. | działa |
| T07 | Historia przejazdów | Użytkownik widzi własny zakończony przejazd. | Historia pokazała przejazd R-001. | działa |
| T08 | Zatrzymanie i ponowny start aplikacji | Zapisane dane pozostają w SQLite. | Dane są przechowywane w `instance/turborower.db`; inicjalizacja używa `CREATE TABLE IF NOT EXISTS`. | działa |
| T09 | Logowanie kontem administratora | Administrator może otworzyć `/admin`. | Konto `admin@turborower.local` ma rolę `ADMIN` i widzi panel. | działa |
| T10 | Próba otwarcia `/admin` zwykłym użytkownikiem | Użytkownik otrzymuje brak uprawnień i trafia do pojazdów. | Zwykły użytkownik jest przekierowany i nie widzi panelu. | działa |
| T11 | Anulowanie aktywnego przejazdu | Status przejazdu zmienia się na `CANCELLED`, a pojazd na `AVAILABLE`. | Przejazd ma status `CANCELLED`, pojazd wraca do listy dostępnych. | działa |
| T12 | Zmiana statusu pojazdu przez administratora | Panel administratora zmienia status pojazdu. | Status R-001 został zmieniony na `AVAILABLE` przez panel. | działa |
| T13 | Status ładowania i usterki pojazdu | Pojazdy mogą mieć status `CHARGING` lub `DAMAGED`. | W bazie istnieją pojazdy o obu nowych statusach. | działa |
| T14 | Zgłoszenie usterki przez użytkownika | Zwykły użytkownik zapisuje kategorię i opis usterki. | Rekord został zapisany ze statusem `OPEN`. | działa |
| T15 | Statystyki zakończonego przejazdu | Zapisane są czas, koszt i dystans, a historia zawiera mapkę trasy. | Statystyki i `route-map` są dostępne w historii. | działa |
| T16 | Większa liczba pojazdów | W obwodzie Olsztyna znajduje się co najmniej 12 pojazdów. | Baza zawiera co najmniej 12 pojazdów. | działa |
| T17 | Usterka zmienia status pojazdu | Zgłoszenie konkretnego pojazdu ustawia jego status na `DAMAGED`. | Po zgłoszeniu pojazd R-003 ma status `DAMAGED`. | działa |
| T18 | Uszkodzony pojazd nie jest dostępny | Pojazd `DAMAGED` nie znajduje się na liście wypożyczeń. | Pojazd uszkodzony jest filtrowany poza statusami `AVAILABLE`. | działa |
| T19 | Panel aktywności użytkownika | Zarezerwowany pojazd lub aktywny przejazd jest widoczny pod `Mój pojazd`. | Panel pokazuje rezerwację i panel aktywnego przejazdu. | działa |
| T20 | Szczegóły pojazdu z mapą | Widok szczegółów zawiera przybliżoną lokalizację pojazdu na mapie. | Mapa Leaflet jest inicjalizowana ze współrzędnymi pojazdu. | działa |
| T21 | Ręczne anulowanie rezerwacji przez admina | Administrator usuwa aktywną rezerwację i zwalnia pojazd. | Rezerwacja zmienia status na `CANCELLED`, pojazd wraca do `AVAILABLE`. | działa |
| T22 | Automatyczne wygasanie rezerwacji po 15 minutach | Przeterminowana rezerwacja jest anulowana przy kolejnym żądaniu, pojazd wraca do dostępnych. | Przeterminowana rezerwacja została anulowana i pojazd miał status `AVAILABLE`. | działa |
| T23 | Mapa w szczegółach pojazdu | Widok zawiera mapę Leaflet z lokalizacją konkretnego pojazdu. | Kontener mapy i współrzędne pojazdu są obecne, a skrypt jest inicjalizowany poza pętlami formularzy. | działa |
| T24 | Dostęp do panelu `/activity` | Zwykły użytkownik ma widoczny przycisk do panelu aktywności. | Link „Mój pojazd” prowadzi do `/activity`. | działa |
| T25 | Wiele rezerwacji | Dwie rezerwacje pozostają widoczne po starcie jednego przejazdu. | Panel pokazuje aktywny przejazd i drugą rezerwację. | działa |
| T26 | Logo TurboRower | Plik `assets/logo/rower2.png` jest dostępny przez aplikację. | HTTP `/assets/logo/rower2.png` zwraca obraz. | działa |

## Kontrole zakresu

- F01 - logowanie i rejestracja: zaimplementowane.
- F02 - lista dostępnych pojazdów: zaimplementowane.
- F03 - rezerwacja i anulowanie własnej rezerwacji: zaimplementowane.
- F04 - rozpoczęcie i zakończenie przejazdu: zaimplementowane.
- F05 - historia przejazdów i opłat: zaimplementowane.

## Scenariusze do dodatkowego sprawdzenia ręcznego

Poniższe przypadki są zaimplementowane, ale wymagają jeszcze ręcznego
potwierdzenia w przeglądarce:

1. Logowanie błędnym hasłem pokazuje komunikat i nie tworzy sesji.
2. Rejestracja istniejącym adresem e-mail jest odrzucona.
3. Próba rezerwacji pojazdu zajętego przez inną sesję jest odrzucona.
4. Użytkownik nie może anulować cudzej rezerwacji.
5. Użytkownik nie może rozpocząć przejazdu bez własnej rezerwacji.
6. Historia nie pokazuje przejazdów innego użytkownika.
