# ================== LIBRERIE ==================
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Dashboard Performance Atletica", layout="wide")

st.title("Dashboard Performance Atletica U16")

# ================== 1. CARICAMENTO FILE ==================
PATH_FILE = "Dataset_combinato_GPS_finale.xlsx"

uploaded_file = st.file_uploader("Carica file Excel", type=["xlsx"])

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

mask_match_valid = (
    (df_raw['Competition'].isin(['League', 'Test Match'])) &
    (df_raw['Time'] == 'Full Match')
)

mask_training = df_raw['Competition'] == 'Full Training'

df = df_raw[mask_match_valid | mask_training].copy()
df = df.sort_values('Data')

# ================== AGGREGAZIONE GIORNALIERA ==================

numeric_cols = df.select_dtypes(include='number').columns.tolist()
numeric_cols = [col for col in numeric_cols if col != 'Vel Max']

df = df.groupby(['PLAYER', 'Data', 'Competition'], as_index=False).agg({
    **{col: 'sum' for col in numeric_cols},
    'Opponent': lambda x: ', '.join(sorted(set(x.dropna())))
})

# ================== TEAM AVERAGE ==================
df_team_avg = df[df['PLAYER'] == 'Team Average'].copy()

# ================== LISTE FILTRI ==================
players = [p for p in df['PLAYER'].dropna().unique().tolist() if p != 'Team Average']
players.insert(0, 'Team Average')

metriche = numeric_cols
competitions = df['Competition'].dropna().unique()

color_map = {
    'League': 'rgba(255,0,0,0.85)',
    'Full Training': 'rgba(0,180,0,0.85)',
    'Test Match': 'rgba(0,0,255,0.85)'
}

# ================== 3. SIDEBAR ==================
st.sidebar.header("Filtri")

giocatore = st.sidebar.selectbox("Giocatore", players)
metrica = st.sidebar.selectbox("Metrica", metriche)

# ================== 4. GRAFICO ==================
df_plot = df[df['PLAYER'] == giocatore].copy()

fig = go.Figure()

# ---- BARRE ----
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
        text=df_comp['Opponent'] if comp in ['League','Test Match'] else None,
        textposition='inside',
        insidetextanchor='middle',
        textfont=dict(color='white', size=11),
        hovertemplate=
            "<b>Data:</b> %{x}<br>" +
            "<b>Valore:</b> %{y}<br>" +
            "<b>Opponent:</b> %{text}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=df_comp['Data'],
        y=df_comp[metrica],
        mode='text',
        text=[f'{v:.0f}' for v in df_comp[metrica]],
        textposition='top center',
        showlegend=False
    ))

# ---- TEAM AVERAGE ----
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

# ---- LAYOUT ----
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
    margin=dict(l=40, r=40, t=80, b=40)
)

st.plotly_chart(fig, use_container_width=True)
