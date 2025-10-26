# Ultimate Omni Package

Komplet pripravljenih vsebin in predlog za splet, učenje, kodo, dokumente, video in audio. Struktura je modularna in pripravljena za takojšnjo uporabo.

## Kako začeti

1) Odpri lokalni strežnik (že teče v tem IDE: http://127.0.0.1:8093/).
2) Odpri spletni del paketa: http://127.0.0.1:8093/UltimateOmniPackage/web/index.html
3) Preberi konfiguracijo v `config/brand_config.json` in prilagodi znamčenje (ime, barve, logotip).

## Struktura map

- web/ – responsive, SEO optimizirane HTML/CSS/JS strani (landing page, blog, e-commerce)
- video/ – podnapisi, mape za animacije in promo videe
- slike/ – infografike (SVG), mape za social, ilustracije, stock-style
- code/ – primeri kode (Python, JS), API, baze podatkov, AI funkcije
- docs/ – priročniki, predloge, planerji, obrazci, e-knjige (Markdown)
- audio/ – mape za glasbo in voiceover (placeholders)
- automation/ – osnovni PowerShell skripti za backup in sinhronizacijo
- white-label/ – navodila za distribucijo pod lastno blagovno znamko
- config/ – konfiguracija znamke (barve, ime, logotip)

## Hiter pregled vsebin

- Splet:
  - `web/index.html` – landing page z osnovnim SEO, JSON-LD in CTA
  - `web/blog.html` – blog predloga, nalaga `docs/blog_posts.json`
  - `web/shop.html` – e-commerce predloga, nalaga `code/javascript/data/products.json`

- Koda:
  - `code/python/scripts/automation_sample.py` – primer skripta za varnostne kopije
  - `code/databases/schema.sql` – vzorčna shema baze
  - `code/api/sample_api_spec.json` – OpenAPI skeleton

- Dokumenti:
  - `docs/manuals/getting_started.md` – uvod
  - `docs/planners/weekly_planner.md` – planer
  - `docs/forms/invoice_template.md` – predloga računa

## Prilagoditev znamke (white-label)

- Uredi `config/brand_config.json`
- Uporabi `white-label/README.md` za korake distribucije in prilagoditev

## License

Ta paket je primer in predloga. Uporabite po potrebi, prilagodite za komercialno rabo.