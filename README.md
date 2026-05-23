## PV-Potenzial Schweiz (BINA Case Study)

Dieses Repository enthält die Anwendung und Datenvorbereitung für ein interaktives Analysetool zur Bestimmung des Photovoltaik-Potenzials und der wirtschaftlichen Attraktivität von Hausanlagen in der Schweiz. Das Projekt wurde im Rahmen einer Case Study für das Modul BINA entwickelt.

## Live-Anwendung
Die App ist live auf Streamlit Cloud verfügbar:  
**[binapvanlagen.streamlit.app](https://binapvanlagen.streamlit.app)**

---

## Data-Driven Decision-Making (DDDM)
Das Projekt folgt konsequent dem Ansatz der **datenbasierten Entscheidungsfindung (DDDM)**. Anstatt Investitionsentscheidungen für Photovoltaikanlagen auf vagen Schätzungen oder globalen Durchschnittswerten aufzubauen, aggregiert und analysiert diese App primäre, hochaufgelöste Geodaten und Tarife:

1. **Standortbestimmung:** Über räumliche Schnittbeprobungen (Spatial Joins) wird ermittelt, ob sich eine Adresse innerhalb der Schweizer Landesgrenzen befindet.
2. **Ertragsrechnung:** Es werden reale Einstrahlungswerte aus Satellitendaten herangezogen.
3. **Lokale Wirtschaftlichkeit:** Da Stromtarife in der Schweiz auf Gemeindeebene fragmentiert sind, zieht das System die exakten Tarife des lokalen Netzbetreibers heran, um eine verlässliche Amortisationsrechnung aufzustellen.

*Hinweis zur Datenintegrität:* Liegt eine abgefragte Adresse ausserhalb des vordefinierten Schweizer Datenraums, wird die Berechnung zum Schutz der Modell-Validität blockiert, da keine validen Entscheidungsgrundlagen vorliegen.

---

## Projektstruktur & Dateitabelle

Das Repository gliedert sich in folgende Kernkomponenten:

| Datei / Ordner | Beschreibung |
| :--- | :--- |
| `Data/` | Ordner mit den Roh- und vorbereiteten Geodaten (`PVOUT.tif`, Tarife als CSV, Gemeinde-Grenzdaten als Geopackage). |
| `01_PVOUT_Preparation.ipynb` | Jupyter Notebook (Google Colab) zur Vorbereitung, Filterung und Transformation der Rasterdaten für das Solarpotenzial. |
| `02_Stromdaten_Preparation.ipynb` | Jupyter Notebook zur Bereinigung, Filterung (Fokus auf Kategorie H4) und Zuordnung der Schweizer Stromtarifdaten. |
| `03_PV_Potenzial_Vergleich.ipynb` | Jupyter Notebook für statistische Analysen, Validierungen und Vergleiche der berechneten Potenziale. |
| `main_BINA.py` | Das Hauptskript der interaktiven Streamlit-Webanwendung (GUI, Geocoding-Logik und Datenvisualisierung). |
| `ergebnis.csv` | Automatisch exportierte Zwischenergebnisse und Kennzahlen der Datenanalyse-Pipelines. |
| `requirements.txt` | Liste der benötigten Python-Bibliotheken zur Ausführung der Anwendung (z. B. `streamlit`, `geopandas`, `rasterio`). |

---

## Technische Umsetzung & Datenquellen

### Datenquellen
* **Solarertrag (PVOUT):** Global Solar Atlas / Geo-optimierte Rasterdaten für die Schweiz.
* **Stromtarife:** Offizielle Schweizer Stromtarif-Rohdaten für das Standard-Produkt (Fokus auf Haushaltstyp H4).
* **Gemeindegrenzen:** `swissBOUNDARIES3D` des Bundesamtes für Landestopografie (swisstopo).

### Verwendete Technologien
* **Frontend/GUI:** Streamlit (Python) mit benutzerdefiniertem CSS-Styling für KPI-Karten.
* **Geodatenverarbeitung:** `geopandas` für räumliche Joins (`sjoin`), `rasterio` zur Beprobung von TIF-Rasterdaten und `shapely` zur Punktgenerierung.
* **Geocoding:** Integration der offiziellen Swisstopo Search API (`api3.geo.admin.ch`) mit Fallback auf `geopy` (Nominatim).

---
