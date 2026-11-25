# Przepływy funkcji

## F03 — Rezerwowanie pojazdu

### Wejście i wynik

- Użytkownik musi być zalogowany.
- Wejściem jest identyfikator wybranego pojazdu; czas rezerwacji i czas
  wygaśnięcia (15 minut później) ustala kontroler.
- Sukces tworzy aktywną rezerwację dla użytkownika i zmienia status pojazdu
  z `AVAILABLE` na `RESERVED`.
- Jeśli pojazdu nie ma albo nie jest dostępny, rezerwacja nie powstaje,
  a użytkownik otrzymuje komunikat o braku dostępności.

### Przepływ danych

1. Użytkownik wybiera pojazd w widoku listy lub mapy i wysyła formularz
   rezerwacji z `templates/vehicle_modal.html`.
2. `app.py` przyjmuje `POST /vehicles/<vehicle_id>/reserve`; dekorator
   `login_required` wymaga aktywnej sesji.
3. `controllers/vehicles.py::reserve_vehicle` pobiera identyfikator
   użytkownika z sesji i wywołuje `models/vehicles.py::reserve`.
4. Model sprawdza dostępność, warunkowo zmienia status pojazdu i zapisuje
   rezerwację. Kontroler pokazuje komunikat i przekierowuje do aktywności
   albo z powrotem do szczegółów pojazdu.

### Próby

Testy integracyjne używają tymczasowej bazy danych. Uruchomienie całego
zestawu:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

| Próba | Stan początkowy i dane | Oczekiwany wynik | Wynik faktyczny | Status |
|---|---|---|---|---|
| Poprawna | Pojazd `R-001` ma status `AVAILABLE`; pierwszy użytkownik go rezerwuje. | Powstaje jedna aktywna rezerwacja; pojazd ma status `RESERVED`. | Rezerwacja powstała, a pojazd otrzymał status `RESERVED`. | ZALICZONA |
| Odrzucona | Ten sam pojazd jest już zarezerwowany przez pierwszego użytkownika; drugi użytkownik próbuje go zarezerwować. | Druga próba jest odrzucona; pozostaje jedna aktywna rezerwacja należąca do pierwszego użytkownika, a pojazd pozostaje `RESERVED`. | Aplikacja odrzuciła próbę; pozostała jedna aktywna rezerwacja pierwszego użytkownika, a status pojazdu pozostał `RESERVED`. | ZALICZONA |

Obie próby są sprawdzane przez `test_second_user_cannot_reserve_already_reserved_vehicle`
w `tests/test_app.py`.

### Polecenie dla agenta i decyzja zespołu

- Polecenie: „Dla F03 prześledź trasę rezerwacji od `app.py` przez kontroler
  do modelu. Dodaj test, który potwierdza rezerwację dostępnego pojazdu oraz
  odmowę drugiemu użytkownikowi dla już zarezerwowanego pojazdu. Nie zmieniaj
  logiki produkcyjnej, jeśli obecna implementacja przechodzi te próby.
  Uruchom pełny zestaw testów i zapisz rzeczywiste wyniki.”
- Decyzja zespołu: zaakceptowano plan dodania testu bez zmiany logiki. Model
  już sprawdza status `AVAILABLE` i warunkowo aktualizuje pojazd; test ma
  zabezpieczyć to zachowanie przed regresją.
- Wynik pracy agenta: dodano test obu prób bez zmian w logice produkcyjnej;
  pełny zestaw 14 testów zakończył się powodzeniem.
