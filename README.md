# Omniscient Dashboard Viewer

Manifest‑driven oglednik nadzornih plošč, ki iz `manifest.json` nariše interaktivne Chart.js grafe (bar, line, pie). Deluje z GitHub Raw URL-ji, brez strežnika.

## Hiter začetek
- Lokalno: odpri `OMNIBOT13/OMNIBOT12/dashboard-preview/index.html` v brskalniku ali zaženi `python -m http.server` v korenu projekta in odpri `http://localhost:8080/`.
- Javno: stran v mapi `docs/` je pripravljena za GitHub Pages (Deploy from a branch → branch: `omni-clean` ali `main`, folder: `/docs`).

## GitHub Pages demo
- Po vklopu Pages bo demo dostopen na: `https://<username>.github.io/copy-of-copy-of-omniscient-ai-platform/`
- Privzeti manifest se samodejno naloži: `dashboards/manifest.json` iz GitHub Raw URL.
- Dodajte UTM: `?utm_source=thereisanaforthat&utm_medium=directory&utm_campaign=listing` za spremljanje prometa.

## Uporaba
- V polje “Manifest JSON URL (Raw)” prilepite vaš `dashboards/manifest.json` (public Raw URL) in kliknite “Naloži manifest”.
- Iz levega seznama izberite ploščo; graf se nariše desno.

## Integracija z Retool
- `source_url` naj kaže na JSON array; polja `x_field` in `y_field` definirata ključ za X/Y.
- V Retoolu uporabite `RESTQuery` → URL do `source_url` → mapirajte podatke v `Chart` komponento.

## Oddaja v AI imenike (npr. There’s An AI For That)
- Uporabite javni demo URL iz GitHub Pages + UTM.
- Dodajte 3–5 screenshotov (glej `docs/assets/`) in kratek video.
- Ključne besede: dashboards, chart.js, manifest, analytics, github raw, retool.

## Screenshoti (priporočila)
- `shot-01-list.png`: seznam nadzornih plošč (20 elementov).
- `shot-02-chart.png`: odprta plošča z grafom.
- `shot-03-load-manifest.png`: polje za vnos + gumb “Naloži manifest”.