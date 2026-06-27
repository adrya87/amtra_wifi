# AMTRA WiFi Home Assistant integration

Custom integration sperimentale per controllare AMTRA LED System Fresh Wi-Fi tramite il cloud AMTRA osservato dall'app ufficiale.

## Stato

Implementazione iniziale:

- login cloud con email e password dell'app AMTRA;
- discovery dei dispositivi associati all'account;
- entità `light` RGBWW basata sui 5 canali documentati;
- sensori diagnostici per firmware e RSSI Wi-Fi.

Il pairing del dispositivo resta gestito dall'app ufficiale.

## Installazione manuale

1. Copia `custom_components/amtra_wifi` nella cartella `custom_components` della tua installazione Home Assistant.
2. Riavvia Home Assistant.
3. Aggiungi l'integrazione da **Impostazioni > Dispositivi e servizi > Aggiungi integrazione > AMTRA WiFi**.

## Note API

La documentazione OpenAPI di partenza è conservata in `docs/amtra_wifi_led_api_openapi.yaml`.

È disponibile anche una pagina Swagger UI statica in `docs/index.html`, pensata per GitHub Pages o per un server statico locale.

La scrittura proprietà usa `set_properties` con il campo `items` come JSON serializzato, ad esempio:

```json
{"items":"{\"Power\":1,\"Mode\":0}"}
```
