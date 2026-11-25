# 001 — Reguła rezerwacji dostępnego pojazdu

## Kontekst

F03 pozwala użytkownikowi zarezerwować pojazd tylko wtedy, gdy jest on
dostępny. Ta reguła dotyczy stanu floty i utworzenia rezerwacji, więc musi być
spójna niezależnie od widoku, z którego użytkownik rozpoczął działanie.

## Rozważane opcje

1. Sprawdzać dostępność wyłącznie w kontrolerze przed wywołaniem modelu.
2. Egzekwować dostępność w modelu, który aktualizuje pojazd i zapisuje
   rezerwację.

## Decyzja

Reguła pozostaje w `models/vehicles.py::reserve`. Model sprawdza, czy pojazd
istnieje i ma status `AVAILABLE`, a następnie aktualizuje go warunkowo,
zachowując warunek statusu w zapytaniu SQL. Dopiero po udanej aktualizacji
zapisuje aktywną rezerwację. Kontroler odpowiada za komunikat i przekierowanie.

## Skutek

Reguła jest niezależna od interfejsu i może być sprawdzana przez test
integracyjny. Test F03 obejmuje poprawną rezerwację oraz odrzucenie próby
drugiego użytkownika bez tworzenia kolejnej aktywnej rezerwacji.
