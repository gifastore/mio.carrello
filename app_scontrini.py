import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒")

# URL del tuo foglio
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Usiamo il nome esatto della linguetta: Foglio1
    # ttl=0 serve per forzare l'aggiornamento dei dati ogni volta che ricarichi
    df_inventario = conn.read(spreadsheet=URL_FOGLIO, worksheet="Foglio1", ttl=0) 
    
    # Pulizia automatica delle colonne (toglie spazi extra)
    df_inventario.columns = df_inventario.columns.str.strip()
    
    st.success("✅ Database collegato con successo!")
except Exception as e:
    st.error(f"❌ Errore di connessione: {e}")
    # Creiamo un dataframe di emergenza se la connessione fallisce
    df_inventario = pd.DataFrame(columns=['Codice a Barre', 'PUNTO VENDITA', 'Nome Prodotto', 'Prezzo standard'])

st.title("🛒 Vibe Smart Spesa")

# --- LOGICA DEL CARRELLO ---
if 'carrello' not in st.session_state:
    st.session_state.carrello = []

barcode = st.text_input("📡 Scansiona o inserisci Codice a Barre", key="barcode_input")

if barcode:
    barcode_clean = str(barcode).strip()
    # Cerchiamo il prodotto nel database
    risultato = df_inventario[df_inventario['Codice a Barre'].astype(str).str.strip() == barcode_clean]
    
    if not risultato.empty:
        item = risultato.iloc[-1]
        st.info(f"Prodotto trovato: **{item['Nome Prodotto']}**")
        
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Prezzo", f"€ {item['Prezzo standard']}")
            with col2:
                qty = st.number_input("Quantità", min_value=1, value=1)
            
            if st.button("➕ AGGIUNGI AL CARRELLO"):
                st.session_state.carrello.append({
                    "Nome": item['Nome Prodotto'],
                    "Prezzo": float(item['Prezzo standard']),
                    "Quantità": qty,
                    "Subtotale": float(item['Prezzo standard']) * qty
                })
                st.success(f"Aggiunto: {item['Nome Prodotto']}")
                st.rerun()
    else:
        st.warning(f"Il codice {barcode_clean} non è in archivio.")
        st.info("Puoi aggiungerlo manualmente dal Foglio Google e ricaricare l'app.")

# --- VISUALIZZAZIONE CARRELLO ---
if st.session_state.carrello:
    st.divider()
    st.subheader("🛒 Il tuo Carrello")
    df_c = pd.DataFrame(st.session_state.carrello)
    st.table(df_c)
    
    totale_spesa = df_c['Subtotale'].sum()
    st.header(f"Totale: € {totale_spesa:.2f}")
    
    if st.button("🗑️ Svuota Carrello"):
        st.session_state.carrello = []
        st.rerun()
