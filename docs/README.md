# GitHub Pages Demo

Ta mapa vsebuje javni demo oglednika nadzornih plošč. Odpri `index.html` na GitHub Pages.

## Uporaba
- V polje “Manifest JSON URL (Raw)” prilepite URL do vašega `dashboards/manifest.json`.
- Kliknite “Naloži manifest”.
- Iz levega seznama izberite ploščo; desno se nariše graf (Chart.js).

### Vgradnja zunanjih nadzornih plošč (iframe)
- Viewer podpira vgradnjo zunanjih dashboardov prek `viz_type: "iframe"`.
- Primer (MGX deljeni dashboard):

```json
{
  "dashboards": [
    {
      "title": "MGX Main Dashboard (embed)",
      "viz_type": "iframe",
      "embed_url": "https://mgx.dev/share/3ce36d1c3b0c4703b4478de320dedd99/v5"
    }
  ]
}
```

- Če zunanji vir blokira vgradnjo (`X-Frame-Options`), uporabite gumb “Odpri demo” ali “Repo” zgoraj.

## Demo URL
- `https://robertpezdirc-eng.github.io/copy-of-copy-of-omniscient-ai-platform/?utm_source=thereisanaforthat&utm_medium=directory&utm_campaign=listing`

## Privzeti manifest
- Prednastavljen: `https://raw.githubusercontent.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/feat/20-dashboards/dashboards/manifest.json`
- Če ta URL ni dostopen, viewer samodejno poskusi `main` vejo.

## Screenshoti (za imenike)
- `assets/shot-01-list.png` – seznam plošč
- `assets/shot-02-chart.png` – odprta plošča z grafom
- `assets/shot-03-load-manifest.png` – vnos URL + gumb

Screenshote dodajte v `docs/assets/` in jih uporabite v oddajah (There’s An AI For That, Product Hunt, itd.).