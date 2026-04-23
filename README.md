# EVI Backend Add-on

## Installatie

1. Ga in HA naar **Instellingen → Add-ons → Add-on Store**
2. Klik op de **3 puntjes** rechtsboven → **Repositories**
3. Voeg toe: `https://github.com/favorcool/evi-ha`
4. Zoek **EVI Backend** en installeer

## Lokale installatie (zonder GitHub)

1. Kopieer de `evi-addon` map via Samba naar:
   `\\homeassistant\share\evi-addon`

2. Ga in HA naar **Instellingen → Add-ons → Add-on Store**
3. Klik **3 puntjes** → **Repositories** → voeg toe:
   `/share/evi-addon`

4. Zoek **EVI Backend** → Installeren → Starten

## Configuratie

```yaml
port: 5001
log_level: info
```

## Na installatie

De backend draait automatisch op:
`http://homeassistant.local:5001`

In `custom_components/evi/const.py`:
```python
EVI_BACKEND_URL = "http://homeassistant.local:5001"
```

## API Docs
`http://homeassistant.local:5001/docs`
