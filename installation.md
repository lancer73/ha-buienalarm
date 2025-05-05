# BuienAlarm Integratie voor Home Assistant

Deze integratie gebruikt de BuienAlarm API om een sensor te creëren die de tijd van de volgende regenbui weergeeft. Daarnaast bevat de sensor ook alle voorspellingsdata in de attributen.

## Installatie

### Methode 1: HACS (Custom repository)

1. Zorg ervoor dat [HACS](https://hacs.xyz/) is geïnstalleerd.
2. Ga naar HACS > Integraties > Menu (rechts bovenin) > Aangepaste repositories.
3. Voeg de URL van je repository toe en selecteer "Integratie" als categorie.
4. Klik op "Voeg toe".
5. Zoek naar "BuienAlarm" in de HACS store en installeer het.

### Methode 2: Handmatige installatie

1. Maak een map `custom_components/buienalarm` aan in je Home Assistant config directory.
2. Kopieer alle bestanden van deze repository naar de map `custom_components/buienalarm`.
3. Herstart Home Assistant.

## Configuratie

Na installatie kun je de integratie toevoegen via:

1. Ga naar Configuratie > Integraties > Voeg Integratie toe.
2. Zoek naar "BuienAlarm" en selecteer het.
3. Vul de benodigde informatie in:
   - **Breedtegraad**: De breedtegraad van je locatie
   - **Lengtegraad**: De lengtegraad van je locatie
   - **Scan interval**: Hoe vaak de data moet worden vernieuwd (in minuten)
   - **Taal / Language**: Kies Nederlands of Engels voor de weergave

## Gebruik

Na configuratie wordt een sensor aangemaakt met de naam `sensor.buienalarm_volgende_bui` (Nederlands) of `sensor.buienalarm_next_rain` (Engels). Deze sensor toont de tijd van de volgende regenbui, of "Geen regen verwacht" / "No rain expected" als er geen regen wordt voorspeld.

### Taalondersteuning

De integratie ondersteunt zowel Nederlands als Engels. De gekozen taal bepaalt:
- De benaming van de sensor
- De tekst "Geen regen verwacht" / "No rain expected"
- De weergave van de relatieve tijd ("over 30 minuten" / "in 30 minutes")

De sensor bevat de volgende attributen:
- `next_rain_forecast`: Tijd van de volgende regenbui
- `rain_forecast`: Een lijst met alle voorspellingsdata, waarbij elk item bevat:
  - `precip`: De verwachte neerslag in mm/u
  - `attime`: De timestamp voor deze voorspelling
- `raw_data`: De volledige ruwe data van de BuienAlarm API

## Lovelace voorbeeld

```yaml
type: entities
entities:
  - entity: sensor.buienalarm_volgende_bui
    name: Volgende regenbui
```

## Automatisering voorbeeld

```yaml
automation:
  - alias: "Waarschuwing voor regen"
    trigger:
      - platform: state
        entity_id: sensor.buienalarm_volgende_bui
    condition:
      - condition: template
        value_template: "{{ not is_state('sensor.buienalarm_volgende_bui', 'Geen regen verwacht') }}"
    action:
      - service: notify.mobile_app
        data:
          message: "Regen op komst: {{ states('sensor.buienalarm_volgende_bui') }}"
```

## Problemen oplossen

Als je problemen ondervindt met deze integratie:

1. Controleer je Home Assistant logs voor foutmeldingen
2. Controleer of je internetverbinding werkt
3. Verifieer of de ingevoerde coördinaten correct zijn
