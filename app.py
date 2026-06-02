import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# =========================================================
# CONFIG PAGINA
# =========================================================

st.set_page_config(
    page_title="Dashboard Performance Atletica",
    layout="wide"
)

st.title("Dashboard Performance Atletica U16")

# =========================================================
# CARICAMENTO FILE
# =========================================================

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

# =========================================================
# PREPARAZIONE DATI
# =========================================================

df_raw['Data'] = pd.to_datetime(df_raw['Data'])

# =========================================================
# =========================================================
# FILTRO MATCH
# =========================================================

# Caso in cui esiste MatchDay
if 'MatchDay' in df_raw.columns:

    mask_match_valid = (

        (df_raw['Competition'].isin([
            'League',
            'Test Match'
        ])) &

        (df_raw['Time'] == 'Full Match') &

        (df_raw['MatchDay'] == 'Full Match')
    )

# Caso in cui MatchDay NON esiste
else:

    mask_match_valid = (

        (df_raw['Competition'].isin([
            'League',
            'Test Match'
        ])) &

        (df_raw['Time'] == 'Full Match')
    )


# =========================================================
# FILTRO TRAINING
# =========================================================

mask_training = (
    df_raw['Competition'] == 'Full Training'
)

# =========================================================
# DATASET FINALE
# =========================================================

df = df_raw[
    mask_match_valid | mask_training
].copy()

# =========================================================
# TIPO SESSIONE
# =========================================================

df['Tipo Sessione'] = df['Competition'].apply(

    lambda x:
    'Full Match'

    if x in ['League', 'Test Match']

    else 'Full Training'
)

# =========================================================
# COLONNE NUMERICHE
# =========================================================

numeric_cols = df.select_dtypes(
    include='number'
).columns.tolist()

# Rimuove Vel Max
numeric_cols = [
    col for col in numeric_cols
    if col != 'Vel Max'
]

# =========================================================
# AGGREGAZIONE
# ATTENZIONE:
# NON SOMMA
# MEDIA GIORNALIERA
# =========================================================

df = df.groupby(
    [
        'PLAYER',
        'Data',
        'Competition',
        'Tipo Sessione'
    ],
    as_index=False
).agg({

    **{
        col: 'mean'
        for col in numeric_cols
    },

    'Opponent': lambda x:
        ', '.join(sorted(set(x.dropna())))
})

# =========================================================
# LISTA GIOCATORI
# =========================================================

players = [
    p for p in df['PLAYER']
    .dropna()
    .unique()
    .tolist()
]

players = [
    p for p in players
    if p != 'Team Average'
]

players = sorted(players)

# =========================================================
# LISTA METRICHE
# =========================================================

metriche = numeric_cols

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("Filtri Dashboard")

# =========================================================
# TIPO MEDIA
# =========================================================

tipo_media = st.sidebar.selectbox(

    "Tipo Media",

    [
        "All",
        "Media Full Match",
        "Media Full Training"
    ]
)

# =========================================================
# FILTRO TIPO
# =========================================================

if tipo_media == "Media Full Match":

    df_filtered = df[
        df['Tipo Sessione'] == 'Full Match'
    ]

elif tipo_media == "Media Full Training":

    df_filtered = df[
        df['Tipo Sessione'] == 'Full Training'
    ]

else:

    df_filtered = df.copy()

# =========================================================
# GIOCATORI
# =========================================================

giocatori_scatter = st.sidebar.multiselect(

    "Giocatori da visualizzare",

    players,

    default=players
)

# =========================================================
# METRICA X
# =========================================================

metrica_x = st.sidebar.selectbox(

    "Metrica asse X",

    metriche,

    index=0
)

# =========================================================
# METRICA Y
# =========================================================

metrica_y = st.sidebar.selectbox(

    "Metrica asse Y",

    metriche,

    index=1
)

# =========================================================
# CONTROLLO
# =========================================================

if len(giocatori_scatter) == 0:

    st.warning("Seleziona almeno un giocatore.")
    st.stop()

# =========================================================
# MEDIA GIOCATORI
# =========================================================

df_scatter = (

    df_filtered

    .groupby('PLAYER')[metriche]

    .mean()

    .reset_index()
)

# =========================================================
# RIMUOVE TEAM AVERAGE
# =========================================================

df_scatter = df_scatter[
    df_scatter['PLAYER'] != 'Team Average'
]

# =========================================================
# FILTRO GIOCATORI
# =========================================================

df_scatter = df_scatter[
    df_scatter['PLAYER']
    .isin(giocatori_scatter)
]

# =========================================================
# TITOLO
# =========================================================

st.subheader("Profilo Prestativo Giocatori")

# =========================================================
# FIGURA SCATTER
# =========================================================

fig_scatter = go.Figure()

fig_scatter.add_trace(go.Scatter(

    x=df_scatter[metrica_x],

    y=df_scatter[metrica_y],

    mode='markers+text',

    text=df_scatter['PLAYER'],

    textposition='top center',

    marker=dict(

        size=18,

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

# =========================================================
# QUADRANTI
# =========================================================

x_mean = df_scatter[metrica_x].mean()

y_mean = df_scatter[metrica_y].mean()

fig_scatter.add_vline(

    x=x_mean,

    line_dash="dash",

    line_color="gray"
)

fig_scatter.add_hline(

    y=y_mean,

    line_dash="dash",

    line_color="gray"
)

# =========================================================
# LAYOUT
# =========================================================

fig_scatter.update_layout(

    title=f"{metrica_x} vs {metrica_y}",

    template='plotly_white',

    xaxis_title=metrica_x,

    yaxis_title=metrica_y,

    height=850
)

# =========================================================
# VISUALIZZA GRAFICO
# =========================================================

st.plotly_chart(
    fig_scatter,
    use_container_width=True
)

# =========================================================
# TABELLA MEDIE
# =========================================================

st.subheader("Tabella Medie Giocatori")

tabella = df_scatter[
    ['PLAYER', metrica_x, metrica_y]
].sort_values(
    by=metrica_y,
    ascending=False
)

st.dataframe(
    tabella,
    use_container_width=True
)

