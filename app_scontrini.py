import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Setup estetico
st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒", layout="centered")

st.title("🛒 Vibe Smart Spesa")

# URL del tuo foglio Google
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

# --- CONNESSIONE ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_inventario = conn.read(spreadsheet=URL_FOGLIO, worksheet="Foglio1", ttl=0)
    df_inventario.columns = df_inventario.columns.str.strip()
    df_inventario['Codice a Barre'] = df_inventario['Codice a Barre'].astype(str).str.strip()
    st.success("✅ Database sincronizzato")
except Exception as e:
    st.error(f"Errore: {e}")
    df_inventario = pd.DataFrame(columns=['Codice a Barre', 'PUNTO VENDITA', 'Nome Prodotto', 'Prezzo standard'])

# Inizializza carrello
if 'carrello' not in st.session_state:
    st.session_state.carrello = []

# --- AREA DI SCANSIONE ---
st.subheader("📡 Inserimento Prodotto")
barcode = st.text_input("Digita o scansiona il codice a barre", key="barcode_input")

if barcode:
    barcode_clean = str(barcode).strip()
    # Cerca il prodotto nel tuo Foglio1
    risultato = df_inventario[df_inventario['Codice a Barre'] == barcode_clean]

    if not risultato.empty:
        item = risultato.iloc[-1]
        
        # MOSTRA DETTAGLI IN UN RIQUADRO
        with st.container(border=True):
            st.markdown(f"### 📦 {item['Nome Prodotto']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"🏪 **Negozio**\n{item['PUNTO VENDITA']}")
            with col2:
                st.write(f"💰 **Prezzo**\n€ {item['Prezzo standard']}")
            with col3:
                qta = st.number_input("Quantità", min_value=1, value=1, step=1)
            
            if st.button("➕ AGGIUNGI AL CARRELLO", use_container_width=True, type="primary"):
                st.session_state.carrello.append({
                    "Prodotto": item['Nome Prodotto'],
                    "Negozio": item['PUNTO VENDITA'],
                    "Prezzo": float(item['Prezzo standard']),
                    "Q.tà": qta,
                    "Totale": float(item['Prezzo standard']) * qta
                })
                st.toast(f"Aggiunto: {item['Nome Prodotto']}")
    else:
        st.warning("⚠️ Prodotto non trovato nel database.")

# --- VISUALIZZAZIONE CARRELLO ---
if st.session_state.carrello:
    st.divider()
    st.subheader("📋 Il tuo Carrello")
    df_c = pd.DataFrame(st.session_state.carrello)
    
    # Mostra la tabella con i dettagli richiesti
    st.dataframe(df_c, use_container_width=True, hide_index=True)
    
    totale_generale = df_c['Totale'].sum()
    st.metric("TOTALE SPESA", f"€ {totale_generale:.2f}")
    
    if st.button("🗑️ Svuota Carrello"):
        st.session_state.carrello = []
        st.rerun()
