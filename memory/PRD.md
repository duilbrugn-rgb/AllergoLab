# AllergoLab — PRD

## Problem statement (originale)
App web "AllergoLab" per selezionare allergeni e creare un promemoria/report da consegnare al paziente per il prelievo, con aggregazione automatica dei test in codici SISS corretti e relativa quantità (moltiplicatore) per l'emissione della ricetta. Login/registrazione (utente, password, nome, cognome → "Medico richiedente"). Tab con anagrafica paziente (Nome, Cognome, Data nascita), lista allergeni (Allegato 1) selezionabile con ricerca e selezione multipla, spostabile in seconda lista; aggregazione secondo Algoritmo (Allegato 2); report finale modificabile e stampabile.

## Architettura
- **Backend**: FastAPI + MongoDB (motor). Auth doppia: JWT email/password (cookie httpOnly) + Emergent Google Auth (session_token). Dataset allergeni caricato da `allergens.json` (282 voci) generato da `build_dataset.py` (Allegato 1). Algoritmo SISS in `algorithm.py` (Allegato 2).
- **Frontend**: React + Tailwind + shadcn/ui. AuthContext, dual-list transfer, pannello aggregazione live, modale report editabile con stampa A4 (`@media print`).

## User personas
- Medico/operatore di laboratorio che compone il pannello esami e genera il promemoria per il paziente.
- Admin/owner: duilbrugn@gmail.com.

## Core requirements (statici)
1. Registrazione/login (email, password, nome, cognome). Nome+Cognome = Medico richiedente.
2. Anagrafica paziente (Nome, Cognome, Data nascita).
3. Lista allergeni Allegato 1 con ricerca + filtro tipologia + selezione multipla, trasferimento in lista selezionati.
4. Aggregazione codici SISS secondo Allegato 2 (conteggio totale incl. molecolari; molecolari con codici dedicati 009068A/009068D; super-gruppi Inalanti+Alimenti→009068B, Farmaci+Veleni→009068C; QTA = ceil(n/12)).
5. Report finale modificabile e stampabile.

## Implementato (2026-06)
- [x] Auth JWT email/password + Google (Emergent) — seed admin duilbrugn@gmail.com.
- [x] Dataset 282 allergeni (Alimenti 126, Molecolari 74, Inalanti 60, Veleni 12, Farmaci 10).
- [x] Algoritmo SISS (Allegato 2) — 5 scenari verificati.
- [x] Dual-list con ricerca, filtri tipologia, selezione multipla, rimozione, svuota.
- [x] Pannello codici SISS live + copia ricetta.
- [x] Modale report editabile + stampa A4 + salvataggio storico.
- [x] Tab Storico (lista/carica/elimina report).
- [x] Testing agent: 100% backend (14/14) e frontend.

## Backlog (P1/P2)
- P1: Applicare logo/colori aziendali (l'utente li fornirà) in header e letterhead del report.
- P2: Export PDF del report (oltre a stampa browser).
- P2: Gestione impostazioni intestazione laboratorio persistente per utente.
- P2: Ruoli/permessi avanzati (admin vs operatore).

## Next tasks
- Ricevere il logo aziendale e integrarlo.
