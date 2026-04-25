import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Setup della pagina
st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒", layout="centered")

# Titolo principale
st.title("🛒 Vibe Smart Spesa")

# URL del tuo foglio Google
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

# --- CONNESSIONE E LETTURA DATI ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_inventario = conn.read(spreadsheet=URL_FOGLIO, worksheet="Foglio1", ttl=0)
    df_inventario.columns = df_inventario.columns.str.strip()
    df_inventario['Codice a Barre'] = df_inventario['Codice a Barre'].astype(str).str.strip()
    st.success("✅ Database sincronizzato")
except Exception as e:
    st.error(f"Errore di lettura: {e}")
    df_inventario = pd.DataFrame(columns=['Codice a Barre', 'PUNTO VENDITA', 'Nome Prodotto', 'Prezzo standard'])

# --- GESTIONE CARRELLO ---
if 'carrello' not in st.session_state:
    st.session_state.carrello = []

# --- AREA DI SCANSIONE ---
st.divider()
barcode = st.text_input("📡 Scansiona o digita codice a barre", placeholder="Es. 800123...")

if barcode:
    barcode_clean = str(barcode).strip()
    # Cerchiamo il prodotto
    risultato = df_inventario[df_inventario['Codice a Barre'] == barcode_clean]

    if not risultato.empty:
        item = risultato.iloc[-1]
        
        # MOSTRA INFO PRODOTTO TROVATO
        with st.container(border=True):
            st.subheader(f"📦 {item['Nome Prodotto']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"🏪 **Negozio:** {item['PUNTO VENDITA']}")
                st.write(f"💰 **Prezzo:** € {item['Prezzo standard']}")
            with col2:
                quantita = st.number_input("Seleziona quantità", min_value=1, value=1, step=1)
            
            if st.button("➕ AGGIUNGI AL CARRELLO", use_container_width=True, type="primary"):
                st.session_state.carrello.append({
                    "Prodotto": item['Nome Prodotto'],
                    "Negozio": item['PUNTO VENDITA'],
                    "Prezzo Unit.": float(item['Prezzo standard']),
                    "Q.tà": quantita,
                    "Totale": float(item['Prezzo standard']) * quantita
                })
                st.toast(f"Aggiunto: {item['Nome Prodotto']}")
    else:
        st.warning("⚠️ Prodotto non trovato nel database.")

# --- VISUALIZZAZIONE RIEPILOGO ---
if st.session_state.carrello:
    st.divider()
    st.subheader("📋 Riepilogo Carrello")
    
    df_c = pd.DataFrame(st.session_state.carrello)
    
    # Mostriamo la tabella con i dati richiesti
    st.dataframe(df_c, use_container_width=True, hide_index=True)
    
    # Calcolo totale finale
    totale_spesa = df_c['Totale'].sum()
    st.metric(label="TOTALE GENERALE", value=f"€ {totale_spesa:.2f}")
    
    if st.button("🗑️ Svuota Carrello"):
        st.session_state.carrello = []
        st.rerun()
