import streamlit as st
import folium
from streamlit_folium import st_folium
import branca.colormap as cm
from datetime import datetime, timedelta, timezone
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from huggingface_hub import hf_hub_download
import os

# Access the Hugging Face token from the environment variable
hf_token = os.getenv("HF_TOKEN")
st.set_page_config(layout="wide")
st.title("Interactive Flood Risk Map")

def update_data(geojson_data):
    from update_geo_data import update_geo_data
    if update_geo_data(geojson_data) :
        st.success("Data updated successfully!")
    else :
        st.error("Failed to update data!")

@st.cache_data
def load_geojson(current_date):

    geojson_path = hf_hub_download(
        repo_id="AdrienD-Skep/geo_flood_data",  # Repository name
        filename="europe_admin.geojson",    # File name in the repository
        repo_type="dataset",                # Type of repository
        token=hf_token,                        
    )
    gdf = gpd.read_file(geojson_path)
    gdf["last_update"] = pd.to_datetime(gdf["last_update"])
    if (gdf['last_update'].dt.date != current_date).any():
        with st.spinner("Updating data... Please wait."):
            gdf = update_data(gdf)

    return gdf

if "selected_region_data" not in st.session_state:
    st.session_state["selected_region_data"] = None
# Get today's date in GMT+0 (UTC)
today = datetime.now(timezone.utc).date()
gdf = load_geojson(today)
gdf["last_update"] = gdf["last_update"].dt.strftime('%Y-%m-%d')
def create_folium_map(option):
    m = folium.Map(location=[54.5260, 15.2551], zoom_start=3)


    colormap_prob = cm.LinearColormap(
        colors=["#000000","#505025", "#808000", "#AEAC00", "#DEFC00", "#FC6E00", "#ff0000"],
        vmin=0,
        vmax=100,
        caption="Probabilité d'inondation (%)"
    )
    
    mode_colormap = cm.StepColormap(
        colors=["#0415FA", "#FFEC11", "#04FAF6", "#0494FA"],
        index=[0, 1, 2, 3, 4], 
        vmin=0,
        vmax=4, 
        caption="Types d'inondation prévus",
        tick_labels=[0, 1, 2, 3])

    def get_style_function(property_name, colormap, is_float=True):
        def style_function(feature):
            raw_value = feature["properties"].get(property_name, 0)
            try:
                value = float(raw_value) if is_float else int(raw_value)
            except (ValueError, TypeError):
                value = 0.0 if is_float else 0
            return {
                "fillColor": colormap(value),
                "color": "black",
                "weight": 0.2,
                "fillOpacity": 0.5,
            }
        return style_function

    highlight_style = {'fillOpacity': 0.7}

    layers_config = [
        ("Probabilité d'inondation (Max)", 'max_flood_proba', colormap_prob, True),
        ("Type d'inondation", 'mode_flood_type',  mode_colormap, False),
        ("Probabilité d'inondation (Moyenne)", 'mean_flood_proba', colormap_prob, True),
        ("Probabilité d'inondation (Médiane)", 'median_flood_proba', colormap_prob, True)
    ]

    layer_name, property_name, cmap, is_float = layers_config[option]

    if is_float :
        tooltip = folium.GeoJsonTooltip(
            fields=["COUNTRY", "NAME_2", property_name],
            aliases=["Pays", "Région", layer_name],
        )
        popup = folium.GeoJsonPopup(
            fields=["COUNTRY", "NAME_2", property_name],
            aliases=["Pays", "Région", layer_name],
        )
    else : 
        tooltip = folium.GeoJsonTooltip(
            fields=["COUNTRY", "NAME_2", property_name+"_name"],
            aliases=["Pays", "Région", layer_name],
        )
        popup = folium.GeoJsonPopup(
            fields=["COUNTRY", "NAME_2", property_name+"_name"],
            aliases=["Pays", "Région", layer_name],
        )
    
    folium.GeoJson(
            gdf,
            style_function=get_style_function(property_name, cmap, is_float),
            tooltip=tooltip,
            popup=popup,
            popup_keep_highlighted=True,
            highlight_function=lambda x: highlight_style,
            smooth_factor=0,
            name = layer_name
        ).add_to(m)
    
    # Ajout des légendes
    if is_float :
        colormap_prob.add_to(m)
    else :
        legend_html = """
                    <style>
                .map-legend {
                    position: absolute;
                    top: 20px;
                    right: 20px;
                    z-index: 9999;
                    background-color: rgba(10,10,10,0.7);
                    border: 2px solid grey;
                    border-radius: 6px;
                    padding: 10px;
                    font-size: 14px;
                    line-height: 18px;
                }
                .map-legend .legend-item {
                    display: flex;
                    align-items: center;
                    margin-top: 8px;
                }
                .map-legend .legend-item span {
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    margin-right: 8px;
                    opacity: 0.7;
                }
            </style>
            <div class="map-legend">
            <b>Types d'inondation prévus</b>
            <div class="legend-item">
                <span style="background:#0415FA;"></span>Côtière
            </div>
            <div class="legend-item">
                <span style="background:#FFEC11;"></span>Éclair
            </div>
            <div class="legend-item">
                <span style="background:#04FAF6;"></span>Fluviale
            </div>
            <div class="legend-item">
                <span style="background:#0494FA;"></span>Fluviale/Côtière
            </div>
            </div>
            """
        st.markdown(legend_html, unsafe_allow_html=True)

    return m

flood_types = ["Côtière", "Éclair", "Fluviale", "Fluviale/Côtière"]
options = [
        "Probabilité d'inondation (Max)",
        "Type d'inondation",
        "Probabilité d'inondation (Moyenne)",
        "Probabilité d'inondation (Médiane)",  
    ]
        
option = st.selectbox(
    "Choisissez le type d'analyse à afficher :",
    options 
)
map_data = st_folium(
    create_folium_map(options.index(option)),
    height=600,
    width="100%",
    key="map",
    use_container_width=True,
    returned_objects=["last_active_drawing"]
)

if map_data.get("last_active_drawing"):
    selected_region_data = map_data["last_active_drawing"]["properties"]
    if selected_region_data == st.session_state.selected_region_data:
        st.session_state.selected_region_data = None
    else:
        st.session_state.selected_region_data = selected_region_data


with st.sidebar:
    if st.session_state.selected_region_data:
        region_name = st.session_state.selected_region_data["NAME_2"] 
        st.title(f"{region_name}")
        df = pd.DataFrame({"date" : [today + timedelta(days=i) for i in range(8)], "flood_proba" : [st.session_state.selected_region_data[f"flood_proba_{i}"]  for i in range(8)]})
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["flood_proba"],
            mode="lines+markers", 
            name="Flood Probability",
            line=dict(color="white"),  
            marker=dict(color="white", size=10) 
        ))

        fig.add_shape(
            type="line",
            x0=df["date"].min(), 
            x1=df["date"].max(),  
            y0=30,
            y1=30,
            line=dict(color="orange", dash="dash"),  
            name="Threshold (30)"
        )

        fig.add_shape(
            type="line",
            x0=df["date"].min(), 
            x1=df["date"].max(),  
            y0=70,
            y1=70,
            line=dict(color="red", dash="dash"), 
            name="Threshold (70)"
        )

        fig.update_layout(
            title="Prévision des risques d'inondation",
            xaxis_title="Date",
            yaxis_title="Probabilité d'inondation en %",
            showlegend=False,
            yaxis=dict(
                range=[0, 100],
                showgrid=False, 
            ),
        )
        st.plotly_chart(fig)

# Add credits section
with st.expander("Source", expanded=False):
    st.markdown("""
    - **Europe Historical Floods Data**: [HANZE_events.csv](https://zenodo.org/records/11259233)
    - **Maps and Spatial Data**: [GADM](https://gadm.org/download_world.html)
    - **Weather Data**: [Open-Meteo](https://open-meteo.com/)
    - **Global Extreme Sea Level Analysis**: [GESLA](https://gesla787883612.wordpress.com/downloads/)
    """)
# - **Global Historical Floods Data (Social Media)**: [flood_events.xlsx](https://www.nature.com/articles/s41597-019-0326-9) (not used)
# - **World's Coastline**: [cartographyvectors](https://cartographyvectors.com/map/808-worlds-coastline) (Plus accessible) Meilleure alternative ? :(https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-coastline/)
