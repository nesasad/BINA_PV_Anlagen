import streamlit as st
import pandas as pd
import geopandas as gpd
import rasterio
import requests
import random  # Neu importiert für das Zufallsprinzip
from geopy.geocoders import Nominatim
from shapely.geometry import Point

# --- KONFIGURATION & STYLING ---
st.set_page_config(page_title="PV-Potenzial Schweiz", layout="wide")

st.markdown("""
<style>
.main { background-color: #f5f7f9; }
.pvd-card {
    background-color: #262730;
    padding: 20px;
    border-radius: 10px;
    color: white;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.pvd-kpi-val { font-size: 32px; font-weight: bold; color: #ffcc00; }
.pvd-kpi-lbl { font-size: 14px; color: #bcbcbc; }
</style>
""", unsafe_allow_html=True)

# --- DATEN-LADEFUNKTIONEN ---
@st.cache_resource(show_spinner="Lade Solardaten…")
def load_solar_data():
    url = "https://raw.githubusercontent.com/nesasad/BINA_PV_Anlagen/main/Data/PVOUT.tif"
    return rasterio.open(url)

@st.cache_data(show_spinner="Lade Stromtarife…")
def load_tariffs():
    url = "https://raw.githubusercontent.com/nesasad/BINA_PV_Anlagen/main/Data/Rohdaten-Tarife-Standard-Produkt.csv"
    df = pd.read_csv(url)
    if 'kategorieName' in df.columns:
        df = df[df['kategorieName'] == 'H4']
    return df

@st.cache_resource(show_spinner="Lade Gemeindedaten…")
def load_boundaries():
    url = "https://raw.githubusercontent.com/nesasad/BINA_PV_Anlagen/main/Data/swissBOUNDARIES3D_1_5_LV95_LN02.gpkg"
    return gpd.read_file(url, layer='tlm_hoheitsgebiet')

# --- LOGIK ---
def geocode_address(address):
    try:
        url = (
            "https://api3.geo.admin.ch/rest/services/api/SearchServer"
            f"?searchText={address}&type=locations&origins=address"
        )
        res = requests.get(url).json()
        if res.get("results"):
            attrs = res["results"][0]["attrs"]
            return attrs["lat"], attrs["lon"], attrs["label"]
    except:
        pass

    try:
        geolocator = Nominatim(user_agent="pv_app")
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude, location.address
    except:
        pass

    return None, None, None

def get_pv_value(tif, lat, lon):
    try:
        for val in tif.sample([(lon, lat)]):
            return float(val[0])
    except:
        pass
    return 0.0

# --- UI ---
st.title("☀️ PV-Potenzial-Check Schweiz")
st.markdown(
    "Ermitteln Sie die Attraktivität einer Solaranlage basierend auf "
    "Wetterdaten und lokalen Stromtarifen."
)

st.markdown("## 🔍 Standortanalyse starten")
st.markdown(
    "Geben Sie Ihre Adresse ein und erhalten Sie eine Einschätzung "
    "zur Wirtschaftlichkeit einer Photovoltaikanlage an diesem Standort."
)

st.markdown("### 📍 Adresse eingeben")

address_input = st.text_input(
    "Strasse und Ort",
    placeholder="Zollstrasse 17, 8005 Zürich"
)

check_button = st.button("Analyse starten", type="primary")

# --- ANALYSE-TRIGGER ---
analysis_started = check_button and address_input.strip() != ""

if check_button and address_input.strip() == "":
    st.warning("Bitte geben Sie eine Adresse ein.")

# --- ANALYSE ---
if analysis_started:
    lat, lon, full_address = geocode_address(address_input)

    if lat:
        tif = load_solar_data()
        df_tarife = load_tariffs()
        gdf_gemeinden = load_boundaries()

        pv_wert = get_pv_value(tif, lat, lon)

        point = Point(lon, lat)
        point_gdf = gpd.GeoDataFrame(
            geometry=[point],
            crs="EPSG:4326"
        ).to_crs(gdf_gemeinden.crs)

        match = gpd.sjoin(point_gdf, gdf_gemeinden, how="left", predicate="within")

        # Verhindert den Absturz bei Adressen ausserhalb der Schweiz
        if not match.empty and "bfs_nummer" in match.columns and pd.notna(match["bfs_nummer"].iloc[0]):
            bfs_nr = int(match["bfs_nummer"].iloc[0])
            g_name = match["name"].iloc[0]

            tarif_row = df_tarife[df_tarife["gemeindeNummer"] == bfs_nr]
            tarif_val = (
                tarif_row["total"].iloc[0]
                if not tarif_row.empty
                else 25.0
            )

            score = pv_wert * tarif_val
            potential_saving = pv_wert * 5 * (tarif_val / 100)

            st.success(f"Gefunden: {full_address} (Gemeinde: {g_name})".replace("<b>", "").replace("</b>", ""))

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div class="pvd-card">
                    <div class="pvd-kpi-lbl">Sonnenertrag (PVOUT)</div>
                    <div class="pvd-kpi-val">{pv_wert:,.0f}</div>
                    <div class="pvd-kpi-lbl">kWh / kWp / Jahr</div>
                </div>
                """.replace(",", "'"), unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="pvd-card">
                    <div class="pvd-kpi-lbl">Stromtarif (H4)</div>
                    <div class="pvd-kpi-val">{tarif_val:.2f}</div>
                    <div class="pvd-kpi-lbl">Rp. / kWh</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="pvd-card">
                    <div class="pvd-kpi-lbl">PV-Attraktivitätsscore</div>
                    <div class="pvd-kpi-val">{score:,.0f}</div>
                    <div class="pvd-kpi-lbl">Punkte (höher = besser)</div>
                </div>
                """.replace(",", "'"), unsafe_allow_html=True)

            c_left, c_right = st.columns([2, 1])

            with c_left:
                st.subheader("🗺️ Landkarte")
                st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))

            with c_right:
                st.subheader("💡 Einschätzung")
                st.write(f"Eine typische 5‑kWp‑Hausanlage spart in **{g_name}** ca.")
                st.metric("Ersparnis pro Jahr", f"CHF {potential_saving:,.2f}".replace(",", "'"))
                
                st.info(
                    "Der Score kombiniert lokale Sonneneinstrahlung "
                    "und Strompreis. Höhere Werte bedeuten schnellere Amortisation."
                )
        else:
            # Liste deiner Zitate + das Wittgenstein-Zitat von vorhin
            quotes = [
                "Wow, die Sonne scheint zwar überall, aber unser Schweizer PV-Check hat gerade die Landkarte hochgehalten und gemeint: «Hoi, das ist ja gar kein Schweizer Boden!»",
                "Da wir uns rein auf die Eidgenossenschaft konzentrieren, können wir das Potenzial für Adressen im Ausland leider nicht berechnen. Die Solarmodule würden sonst vermutlich auch das Gefühl haben, sie wären im falschen Land.",
                "Falls Sie einen Standort in der Schweiz haben, schauen wir gerne wieder vorbei mit dem typischen Schweizer Pünktchen: Wir rechnen erst, wenn alles passt.",
                "«*Die Grenzen meiner Sprache bedeuten die Grenzen meiner Welt.*» Ludwig Wittgenstein ...und die Grenze dieser App ist leider die Schweizer Landesgrenze! 😉"
            ]
            
            # Wählt bei jedem Klick zufällig eines der Zitate aus
            selected_quote = random.choice(quotes)
            
            st.info("### 🏔️ Huch, ein Blick über den Tellerrand!")
            st.warning(selected_quote)
            
    else:
        st.warning("Adresse konnte überhaupt nicht gefunden werden. Bitte präziser eingeben.")

# --- PLATZHALTER ---
if not analysis_started:
    st.markdown("---")
    st.markdown("## 🌱 Warum lohnt sich eine PV‑Analyse?")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("### ☀️ Sonne")
        st.write(
            "Die Sonneneinstrahlung unterscheidet sich lokal stärker, "
            "als viele vermuten – selbst innerhalb eines Kantons."
        )

    with col_b:
        st.markdown("### 💸 Strompreise")
        st.write(
            "Lokale Stromtarife beeinflussen die Rentabilität massiv "
            "und werden oft unterschätzt."
        )

    with col_c:
        st.markdown("### 🏡 Ihr Standort")
        st.write(
            "Schon geringe Lageunterschiede können messbare Effekte "
            "auf den PV‑Ertrag haben."
        )

    st.info(
        "👉 Geben Sie oben Ihre Adresse ein, um eine standortbasierte "
        "Bewertung zu erhalten."
    )
