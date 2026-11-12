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
