# ================== LIBRERIE ==================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# ================== CONFIG PAGINA ==================

st.set_page_config(
    page_title="Dashboard Performance Atletica",
    layout="wide"
)

st.title("Dashboard Performance Atletica U16")

# ================== 1. CARICAMENTO FILE ==================

PATH_FILE = "Dataset_combinato_GPS_finale.xlsx"

uploaded_file = st.file_uploader(
    "Carica file Excel",
    type=["xlsx"]
)

if uploaded_file is not None:
    df_raw = pd.read_excel(uploaded_file)

elif os.path.exists(PATH_FILE):
    df_raw = pd.read_excel(PATH_FILE)

else:
    st.warning("Carica un file Excel per iniziare.")
    st.stop()

st.success("File caricato con successo!")

# ================== 2. PREPARAZIONE DATI ==================

df_raw['Data'] = pd.to_datetime(df_raw['Data'])

# Match validi
mask_match_valid = (
    (df_raw['Competition'].isin(['League', 'Test Match'])) &
    (df_raw['Time'] == 'Full Match')
)

# Allenamenti
mask_training = (
    df_raw['Competition'] == 'Full Training'
)

# Dataset finale
df = df_raw[mask_match_valid | mask_training].copy()

# Ordina per data
df = df.sort_values('Data')

# ================== AGGREGAZIONE GIORNALIERA ==================

numeric_cols = df.select_dtypes(include='number').columns.tolist()

# Esclude Vel Max se necessario
numeric_cols = [col for col in numeric_cols if col != 'Vel Max']

# Aggregazione giornaliera
df = df.groupby(
    ['PLAYER', 'Data', 'Competition'],
    as_index=False
).agg({
    **{col: 'sum' for col in numeric_cols},
    'Opponent': lambda x: ', '.join(sorted(set(x.dropna())))
})

# ================== TEAM AVERAGE ==================

df_team_avg = df[df['PLAYER'] == 'Team Average'].copy()

# ================== MEDIA ANNUALE ==================

df['Anno'] = df['Data'].dt.year

df_media_annuale = (
    df.groupby(['PLAYER', 'Anno'])[numeric_cols]
    .mean()
    .reset_index()
)

# ================== LISTE FILTRI ==================

players = [
    p for p in df['PLAYER'].dropna().unique().tolist()
    if p != 'Team Average'
]

players.insert(0, 'Team Average')

metriche = numeric_cols

competitions = df['Competition'].dropna().unique()

# ================== COLORI ==================

color_map = {
    'League': 'rgba(255,0,0,0.85)',
    'Full Training': 'rgba(0,180,0,0.85)',
    'Test Match': 'rgba(0,0,255,0.85)'
}

# ================== SIDEBAR ==================

st.sidebar.header("Filtri")

# Giocatore
giocatore = st.sidebar.selectbox(
    "Giocatore",
    players
)

# Metrica principale
metrica = st.sidebar.selectbox(
    "Metrica",
    metriche
)

# ================== SCATTER FILTRI ==================

st.sidebar.subheader("Scatter Performance")

metrica_x = st.sidebar.selectbox(
    "Metrica asse X",
    metriche,
    index=0
)

metrica_y = st.sidebar.selectbox(
    "Metrica asse Y",
    metriche,
    index=1
)

# ================== 3. GRAFICO PRINCIPALE ==================

df_plot = df[df['PLAYER'] == giocatore].copy()

fig = go.Figure()

# ================== BARRE ==================

for comp in competitions:

    df_comp = df_plot[df_plot['Competition'] == comp]

    if df_comp.empty:
        continue

    fig.add_trace(go.Bar(
        x=df_comp['Data'],
        y=df_comp[metrica],
        name=comp,
        marker_color=color_map.get(comp, 'gray'),
        width=24*60*60*1000,

        text=df_comp['Opponent']
        if comp in ['League', 'Test Match']
        else None,

        textposition='inside',
        insidetextanchor='middle',

        textfont=dict(
            color='white',
            size=11
        ),

        hovertemplate=
            "<b>Data:</b> %{x}<br>" +
            "<b>Valore:</b> %{y}<br>" +
            "<b>Opponent:</b> %{text}<extra></extra>"
    ))

    # Valore sopra la barra
    fig.add_trace(go.Scatter(
        x=df_comp['Data'],
        y=df_comp[metrica],
        mode='text',

        text=[
            f'{v:.0f}'
            for v in df_comp[metrica]
        ],

        textposition='top center',
        showlegend=False
    ))

# ================== TEAM AVERAGE ==================

if not df_team_avg.empty and giocatore != 'Team Average':

    fig.add_trace(go.Scatter(
        x=df_team_avg['Data'],
        y=df_team_avg[metrica],

        mode='markers',

        name='Team Average (Ref)',

        marker=dict(
            symbol='asterisk',
            size=10,
            color='black',
            line=dict(width=1.5)
        )
    ))

# ================== LAYOUT GRAFICO PRINCIPALE ==================

fig.update_layout(
    title=f"{metrica} - {giocatore}",

    barmode='overlay',

    hovermode='x unified',

    template='plotly_white',

    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),

    xaxis=dict(
        type="date",
        rangeslider=dict(visible=True)
    ),

    margin=dict(
        l=40,
        r=40,
        t=80,
        b=40
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ================== TABELLA MEDIA ANNUALE ==================

st.subheader("Media Annuale")

df_media_player = df_media_annuale[
    df_media_annuale['PLAYER'] == giocatore
][['Anno', metrica]]

df_media_player = df_media_player.rename(
    columns={
        metrica: 'Media Annuale'
    }
)

st.dataframe(
    df_media_player,
    use_container_width=True
)

# ================== GRAFICO MEDIA ANNUALE ==================

fig_media = go.Figure()

fig_media.add_trace(go.Bar(
    x=df_media_player['Anno'],
    y=df_media_player['Media Annuale'],

    text=[
        f'{v:.1f}'
        for v in df_media_player['Media Annuale']
    ],

    textposition='outside'
))

fig_media.update_layout(
    title=f"Media Annuale {metrica} - {giocatore}",
    template='plotly_white',
    xaxis_title='Anno',
    yaxis_title='Media'
)

st.plotly_chart(
    fig_media,
    use_container_width=True
)

# ================== SCATTER PERFORMANCE ==================

st.subheader("Profilo Prestativo Giocatori")

# Media per giocatore
df_scatter = (
    df.groupby('PLAYER')[metriche]
    .mean()
    .reset_index()
)

# Rimuove Team Average
df_scatter = df_scatter[
    df_scatter['PLAYER'] != 'Team Average'
]

# ================== FIGURA SCATTER ==================

fig_scatter = go.Figure()

fig_scatter.add_trace(go.Scatter(

    x=df_scatter[metrica_x],

    y=df_scatter[metrica_y],

    mode='markers+text',

    text=df_scatter['PLAYER'],

    textposition='top center',

    marker=dict(
        size=14,
        color='royalblue',

        line=dict(
            width=1,
            color='black'
        )
    ),

    hovertemplate=
        "<b>%{text}</b><br>" +
        f"{metrica_x}: %{{x:.2f}}<br>" +
        f"{metrica_y}: %{{y:.2f}}<extra></extra>"
))

# ================== LAYOUT SCATTER ==================

fig_scatter.update_layout(

    title=f"{metrica_x} vs {metrica_y}",

    template='plotly_white',

    xaxis_title=metrica_x,

    yaxis_title=metrica_y,

    height=700
)

st.plotly_chart(
    fig_scatter,
    use_container_width=True
)
