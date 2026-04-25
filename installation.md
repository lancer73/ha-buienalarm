# BuienAlarm-integratie voor Home Assistant

Een Home Assistant-integratie die de BuienAlarm-API gebruikt voor
regenvoorspellingen op een opgegeven locatie.

> **Disclaimer.** Dit is een onofficiële community-integratie die niet
> gelieerd is aan BuienAlarm. De brand-iconen in
> `custom_components/buienalarm/brand/` zijn generieke regenwolk-illustraties,
> niet het BuienAlarm-handelsmerk.

## Vereisten

- Home Assistant 2024.12 of nieuwer

## Installatie

### Methode 1 — HACS (aanbevolen)

1. Zorg dat [HACS](https://hacs.xyz/) geïnstalleerd is.
2. Open in HACS het menu (rechtsboven) → *Aangepaste repositories*.
3. Voeg `https://github.com/lancer73/ha-buienalarm` toe met categorie
   *Integratie*.
4. Zoek naar *BuienAlarm* in de HACS-store en installeer.
5. Herstart Home Assistant.

### Methode 2 — Handmatig

1. Kopieer de map `custom_components/buienalarm/` uit deze repository naar
   `config/custom_components/` van je Home Assistant.
2. Herstart Home Assistant.

## Configuratie

Na installatie:

1. Ga naar *Instellingen → Apparaten en services → Integratie toevoegen*.
2. Zoek naar *BuienAlarm* en selecteer het.
3. Vul in:
   - **Breedtegraad** en **Lengtegraad** van de te voorspellen locatie
   - **Verversinterval** — frequentie waarmee data wordt opgehaald
     (3–60 minuten, standaard 5)
   - **Taal** — Nederlands of Engels

De integratie controleert de API-aanroep voordat de entry wordt aangemaakt,
dus een fout in coördinaten of verbinding wordt direct gemeld.

Het verversinterval en de taal kunnen achteraf worden aangepast via de knop
*Configureren* op de integratiekaart. Wijzigingen worden direct doorgevoerd,
zonder herstart van Home Assistant.

## Sensoren

Per geconfigureerde locatie wordt één apparaat aangemaakt met zes sensoren:

| Sensor (Nederlands)  | Type      | Beschrijving                                                    |
|----------------------|-----------|-----------------------------------------------------------------|
| Volgende bui         | tekst     | Leesbare status, bv. "14:25 (over 30 minuten)"                  |
| Start volgende bui   | timestamp | Wanneer de volgende bui start; `unknown` als er geen komt       |
| Einde huidige bui    | timestamp | Wanneer de huidige/volgende bui stopt; `unknown` als geen einde |
| Drempel licht        | mm/u      | Drempelwaarde voor lichte regen, geleverd door de API           |
| Drempel gemiddeld    | mm/u      | Drempelwaarde voor gemiddelde regen                             |
| Drempel zwaar        | mm/u      | Drempelwaarde voor zware regen                                  |

De `Volgende bui`-sensor heeft daarnaast deze attributen:

- `next_rain_forecast` — zelfde waarde als de status, handig voor templates
- `rain_forecast` — lijst met `{precip: mm/u, attime: unix_ts}`
- `period_type` — `wet` (volgende bui komt eraan), `dry` (huidige bui stopt),
  of `nan` (geen overgang in zicht)
- `period_start` — kloktijd (`HH:MM`) van de aankomende overgang

> Het attribuut `raw_data` uit eerdere versies is **verwijderd in 1.0.0**.
> De volledige API-respons is nu opvraagbaar via *Diagnostische gegevens
> downloaden* op de integratiekaart.

## Engelstalige documentatie

De volledige documentatie inclusief Lovelace-voorbeelden, automatiseringen
en het Apex Charts-dashboard staat in [`README.md`](README.md). Houd er
rekening mee dat entity-ID's afhankelijk zijn van de gekozen taal:
Nederlandstalige gebruikers zien bijvoorbeeld `sensor.buienalarm_volgende_bui`
in plaats van `sensor.buienalarm_next_shower`. Bekijk
*Instellingen → Apparaten en services → BuienAlarm* om de daadwerkelijk
aangemaakte entity-ID's te zien.

## Voorbeeldautomatisering

```yaml
automation:
  - alias: "Waarschuwing voor regen"
    trigger:
      - platform: state
        entity_id: sensor.buienalarm_start_volgende_bui
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state not in ['unknown', 'unavailable'] }}"
    action:
      - service: notify.mobile_app
        data:
          title: "Regen op komst"
          message: >
            Volgende bui begint om
            {{ as_timestamp(states('sensor.buienalarm_start_volgende_bui'))
               | timestamp_custom('%H:%M') }}.
```

## Problemen oplossen

1. Open *Instellingen → Apparaten en services → BuienAlarm → ⋮ →
   Diagnostische gegevens downloaden* en bekijk de JSON. Breedte- en
   lengtegraad worden automatisch geredigeerd.
2. Schakel debug-logging in via *Instellingen → Apparaten en services →
   BuienAlarm → ⋮ → Foutopsporingsregistratie inschakelen*, reproduceer het
   probleem en schakel daarna debug-logging weer uit — Home Assistant biedt
   het logbestand dan aan om te downloaden.
3. Controleer of de internetverbinding werkt en of de coördinaten binnen
   het BuienAlarm-dekkingsgebied vallen.
4. Bekijk de Home Assistant-log voor meldingen van de `buienalarm` logger.

## Upgraden van 0.1.x

Upgrade gewoon via HACS. Bij de volgende herstart migreert de integratie:

1. De oude `buienalarm_next_rain_<lat>_<lon>`-sensor wordt hernoemd naar
   het nieuwe schema — **historie blijft behouden**.
2. De `unique_id` van de entry wordt afgerond zodat coördinaten niet meer
   in het registry-export staan.
3. De entry-versie wordt opgehoogd van 1 naar 2.

Pas dashboards die verwijzen naar het `raw_data`-attribuut aan: de drie
drempelwaarden zitten nu in eigen sensoren (`Drempel licht`,
`Drempel gemiddeld`, `Drempel zwaar`). Zie [`README.md`](README.md) voor het
bijgewerkte Apex Charts-voorbeeld.

Zie [`CHANGES.md`](CHANGES.md) voor de volledige changelog.

## Licentie

Dit project valt onder de MIT-licentie — zie [`LICENSE`](LICENSE).
