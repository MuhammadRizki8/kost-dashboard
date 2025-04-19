import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from scipy.stats import gaussian_kde
import pydeck as pdk

# ------------------------------
# Page Configuration
# ------------------------------
st.set_page_config(
    page_title="Dashboard Kost",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------
# Data Loading
# ------------------------------
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)

    # Perbaikan nilai data yang diketahui salah
    df.loc[563, 'lebar'] = 3.5
    df.loc[677, ['lebar', 'panjang']] = [2.5, 2.8]
    df.loc[811, 'lebar'] = 4.5

    return df

df = load_data("dashboard_data.csv")

# ------------------------------
# Sidebar Filter
# ------------------------------
st.sidebar.header("🎛️ Filter Data")
# Kecamatan
kec_options = sorted(df['kecamatan'].unique())
selected_kecs = st.sidebar.multiselect("Pilih Kecamatan", kec_options, default=kec_options)

# Harga
min_price, max_price = int(df['harga'].min()), int(df['harga'].max())
selected_price = st.sidebar.slider("Rentang Harga (Rp)", min_price, max_price, (min_price, max_price), step=100_000)

# Gender
gender_options = df['gender'].unique().tolist()
selected_gender = st.sidebar.multiselect("Tipe Kos", gender_options, default=gender_options)

# Filter DataFrame
mask = (
    df['kecamatan'].isin(selected_kecs) &
    df['harga'].between(*selected_price) &
    df['gender'].isin(selected_gender)
)
df_filtered = df[mask]

# ------------------------------
# Header & Key Metrics
# ------------------------------
st.title("📊 Dashboard Market Analysis Kost")
st.markdown("Visualisasi interaktif data kost berdasarkan harga, luas, fasilitas, dan lokasi.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Listings", df_filtered.shape[0])
col2.metric("Harga Rata-rata (Rp)", f"{int(df_filtered['harga'].mean()):,}" if not df_filtered.empty else "0")
col3.metric("Luas Rata-rata (m²)", f"{round(df_filtered['luas_m2'].mean(), 2)}" if not df_filtered.empty else "0")
col4.metric("Kecamatan Terpilih", df_filtered['kecamatan'].nunique())

st.markdown("---")

# ------------------------------
# Row 1: KDE dan Kategori Harga
# ------------------------------
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("📈 Distribusi Harga (KDE)")
    if not df_filtered.empty:
        harga_values = df_filtered['harga'].values
        kde = gaussian_kde(harga_values)
        x = np.linspace(harga_values.min(), harga_values.max(), 200)
        y = kde(x)
        kde_df = pd.DataFrame({'Harga (Rp)': x, 'Density': y})

        c1 = alt.Chart(kde_df).mark_line().encode(
            x=alt.X('Harga (Rp):Q', axis=alt.Axis(format=',')),
            y='Density:Q'
        ).properties(height=300)
        st.altair_chart(c1, use_container_width=True)
    else:
        st.info("Tidak ada data untuk ditampilkan.")

with col_b:
    st.subheader("🏷️ Kategori Harga")
    if not df_filtered.empty:
        cat_df = df_filtered['kategori_harga'].value_counts().reset_index()
        cat_df.columns = ['Kategori', 'Jumlah']
        c2 = alt.Chart(cat_df).mark_bar().encode(
            x=alt.X('Kategori:N', sort='-y'),
            y='Jumlah:Q',
            color='Kategori:N'
        ).properties(height=300)
        st.altair_chart(c2, use_container_width=True)
    else:
        st.info("Tidak ada data untuk ditampilkan.")

st.markdown("---")

# ------------------------------
# Row 2: Histogram & Boxplot
# ------------------------------
col_c, col_d = st.columns(2)

with col_c:
    st.subheader("🏗️ Histogram Total Fasilitas")
    chart = alt.Chart(df_filtered).mark_bar().encode(
        x=alt.X('total_facilities:Q', bin=alt.Bin(maxbins=20)),
        y='count():Q'
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

with col_d:
    st.subheader("📦 Distribusi Fasilitas per Tipe")
    melted_df = df_filtered.melt(
        value_vars=[
            'jumlah_fasilitas_premium',
            'jumlah_fasilitas_non_premium',
            'jumlah_fasilitas_netral'
        ],
        var_name='Tipe', value_name='Jumlah'
    )

    c4 = alt.Chart(melted_df).mark_boxplot(extent='min-max').encode(
        x='Tipe:N', y='Jumlah:Q', color='Tipe:N'
    ).properties(height=300)
    st.altair_chart(c4, use_container_width=True)

st.markdown("---")

# ------------------------------
# Scatter Chart: Harga vs Luas
# ------------------------------
st.subheader("📐 Harga vs Luas (m²) & Jumlah Fasilitas")

scatter = alt.Chart(df_filtered).mark_circle(opacity=0.6).encode(
    x='luas_m2:Q',
    y='harga:Q',
    color='kategori_harga:N',
    tooltip=['harga:Q', 'luas_m2:Q', 'total_facilities:Q', 'kecamatan:N']
).properties(height=300)

st.altair_chart(scatter, use_container_width=True)

st.markdown("---")

# ------------------------------
# Trend Harga vs Fasilitas
# ------------------------------
st.subheader("📊 Trend Harga Berdasarkan Jumlah Fasilitas")

trend_cols = st.columns(3)

with trend_cols[0]:
    st.markdown("**Premium**")
    df_trend = df_filtered.groupby('jumlah_fasilitas_premium')['harga'].mean().reset_index()
    c = alt.Chart(df_trend).mark_line(point=True).encode(
        x='jumlah_fasilitas_premium:Q',
        y='harga:Q'
    ).properties(height=250)
    st.altair_chart(c, use_container_width=True)

with trend_cols[1]:
    st.markdown("**Non-Premium**")
    df_trend = df_filtered.groupby('jumlah_fasilitas_non_premium')['harga'].mean().reset_index()
    c = alt.Chart(df_trend).mark_line(point=True).encode(
        x='jumlah_fasilitas_non_premium:Q',
        y='harga:Q'
    ).properties(height=250)
    st.altair_chart(c, use_container_width=True)

with trend_cols[2]:
    st.markdown("**Netral**")
    df_trend = df_filtered.groupby('jumlah_fasilitas_netral')['harga'].mean().reset_index()
    c = alt.Chart(df_trend).mark_line(point=True).encode(
        x='jumlah_fasilitas_netral:Q',
        y='harga:Q'
    ).properties(height=250)
    st.altair_chart(c, use_container_width=True)

st.markdown("---")

# ------------------------------
# Map & Data Table
# ------------------------------
map_col, table_col = st.columns([2, 1])

with map_col:
    st.subheader("🗺️ Peta Persebaran Kost")
    if not df_filtered.empty:
        center_lat, center_lon = df_filtered['latitude'].mean(), df_filtered['longitude'].mean()
        layer_type = st.radio("Tipe Layer", ["Scatter", "Hexagon"], horizontal=True)

        if layer_type == "Scatter":
            layer = pdk.Layer(
                "ScatterplotLayer",
                df_filtered,
                get_position='[longitude, latitude]',
                get_color='[255,99,71,140]',
                get_radius='luas_m2 * 10',
                pickable=True
            )
        else:
            layer = pdk.Layer(
                "HexagonLayer",
                df_filtered,
                get_position='[longitude, latitude]',
                radius=50,
                extruded=True,
                pickable=True
            )

        view_state = pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=11,
            pitch=45
        )

        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"html": "<b>Harga:</b> {harga}<br/><b>Luas:</b> {luas_m2}m²"}
        ))
    else:
        st.info("Tidak ada data untuk peta.")

with table_col:
    st.subheader("📋 Data Listing")
    st.dataframe(df_filtered.reset_index(drop=True), use_container_width=True)

# ------------------------------
# Footer Sidebar
# ------------------------------
st.sidebar.markdown("---")
st.sidebar.write("KostHub 2025")
