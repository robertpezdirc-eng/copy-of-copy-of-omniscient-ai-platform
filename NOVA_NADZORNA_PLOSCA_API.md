# 📝 Načrt za Novo Centralizirano Nadzorno Ploščo: API Zdravje & KPI Vpliv

**Cilj:** Ustvariti enotno nadzorno ploščo v Grafani za 360-stopinjski pregled nad stanjem API-jev, njihovo učinkovitostjo in direktnim vplivom na ključne poslovne kazalnike (KPI-je).

---

## 1. Ključne Metrike za Spremljanje

Nadzorna plošča bo razdeljena na tri glavne sekcije:

### A. API Zdravje (Real-time)
Spremljali bomo ključne metrike, ki kažejo na tehnično stanje API-jev.

- **Odzivni čas (Latency):**
  - **p99 Latency:** 99% vseh klicev je hitrejših od te vrednosti. Kritično za odkrivanje "outlier" težav.
  - **p95 Latency:** Daje realno sliko uporabniške izkušnje.
  - **Povprečna Latency:** Splošen pregled hitrosti delovanja.

- **Stopnja Napak (Error Rate %):**
  - **HTTP 5xx napake:** Napake na strežniški strani (npr. zrušitev storitve). **To je kritičen alarm.**
  - **HTTP 4xx napake:** Napake na strani klienta (npr. napačni podatki), ki lahko kažejo na težave v frontend aplikacijah ali zlorabe.

- **Promet (Throughput):**
  - **Zahtevki na minuto (RPM):** Kaže na obremenitev sistema v realnem času.

### B. Vpliv na Poslovne KPI-je
Ta sekcija bo korelirala tehnične metrike z direktnimi poslovnimi rezultati.

- **Graf 1: Odzivni čas API-ja vs. Prihodki (€):**
  - Ali daljši odzivni čas plačilnega API-ja sovpada z upadom prihodkov?
  - Vizualna primerjava grafa latence in grafa prihodkov po urah.

- **Graf 2: Stopnja napak API-ja vs. Nove Registracije:**
  - Ali višja stopnja napak na registracijskem API-ju zmanjša število novih uporabnikov?

### C. Poraba Resursov
Spremljanje porabe resursov, da lahko predvidimo težave s skaliranjem.

- **CPU Uporaba (%)** za API storitve.
- **Poraba Pomnilnika (Memory Usage)** za API storitve.

---

## 2. Implementacijski Koraki

1.  **Definiranje Metrik v Prometheus:** V backend kodo (FastAPI) bomo dodali izvoz novih metrik, ki jih potrebuje ta nadzorna plošča (npr. `business_revenue_total`, `user_registration_count`).
2.  **Izdelava Grafana JSON Modela:** Na podlagi tega načrta bom ustvaril JSON datoteko, ki definira vse grafe in panele v Grafani.
3.  **Uvoz in Testiranje:** Uvozili bomo novo nadzorno ploščo v Grafano in preverili, ali se vsi podatki pravilno prikazujejo.

Naslednji korak je priprava dejanskega JSON modela za Grafano.
