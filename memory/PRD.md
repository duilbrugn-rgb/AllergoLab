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

## Aggiornamento (2026-06 · iterazione 3)
- [x] Catalogo allergeni spostato in MongoDB (seed 282 all'avvio da allergens.json).
- [x] Tab "Configurazione" admin-only (RBAC): CRUD allergeni (aggiungi/modifica/elimina) con ricerca; il catalogo del "Nuovo Report" si ricarica dopo le modifiche.
- [x] Endpoint /api/admin/allergens protetti da get_admin_user (403 per non-admin).
- [x] Confermato isolamento report per utente (ownership su user_id: list/get/delete). Ogni utente vede solo i propri report/storico.
- [x] Testing agent: 100% (backend 13/13, frontend).


## Aggiornamento (2026-06 · iterazione 5)
- [x] Registro modifiche (audit) allergeni: ogni create/update/delete registra in db.allergen_audit action, allergene, autore (nome+email) e timestamp; per gli update elenca i campi modificati. Endpoint GET /api/admin/audit (admin-only).
- [x] Gestione ruoli: GET /api/admin/users e PUT /api/admin/users/{id}/role (admin-only). L'admin promuove/rimuove admin; blocco self-role (400), ruolo invalido (400), utente inesistente (404).
- [x] UI: tab "Configurazione" con sotto-tab Catalogo / Utenti / Registro modifiche; stati di caricamento.
- [x] Testing agent: 100% (backend 41/41, frontend).


## Aggiornamento (2026-06 · iterazione 7)
- [x] Profili di allergeni (bundle): collezione db.profiles; GET /api/profiles (tutti gli utenti autenticati), POST/PUT/DELETE /api/admin/profiles (admin-only).
- [x] UI admin: sotto-tab "Profili" in Configurazione (AdminProfiles) con picker allergeni + chip; crea/modifica/elimina.
- [x] UI utente: pannello "Profili di allergeni" (ProfileSelector) nel tab Nuovo Report; "Vedi" mostra gli allergeni contenuti, "Aggiungi" li sposta tutti a destra (senza duplicati); l'utente può poi deselezionare i singoli. Aggregazione SISS invariata.
- [x] Cancellazione automatica report >10 giorni: cron giornaliero (.emergent/crons.yml, 03:00 UTC) -> POST /api/cron/purge-old-reports (Bearer WEBHOOK_CRON_SECRET, hmac.compare_digest, BackgroundTasks); elimina report con created_at < now-10gg.
- [x] Testing agent: 100% (backend 14/14, frontend).


## Aggiornamento (2026-06 · iterazione 8) — Intestazione stampa report
- [x] Nuova intestazione report conforme al modulo aziendale: griglia a 3 colonne SENZA righe verticali (solo linee orizzontali).
  - Sinistra: logo Regione Lombardia (/frontend/public/logo-regione.jpg).
  - Centro: titolo "ALLERGENI / PER DETERMINAZIONE / IgE SPECIFICHE (RAST)" + "MODULO".
  - Destra: Mod-LABCENT13.08.01.01, PAGINA: X DI X (dinamico), REVISIONE: 00, DATA: 04/09/2026 (fissa).
- [x] Stampa impaginata A4 (JS pagination in ReportModal.jsx): contenuto suddiviso in blocchi misurati e distribuito su piu' pagine; l'intestazione si ripete su OGNI pagina con numero pagina corretto.
- [x] File: /app/frontend/src/components/ReportModal.jsx (ReportHeader + #print-document/#print-measure via portal), /app/frontend/src/App.css (stili .ph-* / .pb-* + @media print @page A4).
- [x] Verificato via screenshot (media screen + print): header identico al modello, pagine "1 DI 6", "2 DI 6"... corrette.
- Note: valori codice modulo/revisione/data fissi nel codice (richiesta utente). Logo caricato dall'utente.
