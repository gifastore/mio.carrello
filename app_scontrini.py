import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Setup estetico
st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒", layout="centered")

# Stile CSS personalizzato per rendere l'app più "mobile-friendly"
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

# --- CONNESSIONE ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_inventario = conn.read(spreadsheet=URL_FOGLIO, worksheet="Foglio1", ttl=0)
    df_inventario.columns = df_inventario.columns.str.strip()
    df_inventario['Codice a Barre'] = df_inventario['Codice a Barre'].astype(str).str.strip()
except Exception as e:
    st.error("Connessione al database fallita.")
    df_inventario = pd.DataFrame(columns=['Codice a Barre', 'PUNTO VENDITA', 'Nome Prodotto', 'Prezzo standard'])

if 'carrello' not in st.session_state:
    st.session_state.carrello = []

# --- HEADER ---
st.title("🛒 Vibe Smart Spesa")
st.write("Gestisci la tua spesa in tempo reale con scansione database.")

# --- SEZIONE SCANSIONE ---
with st.container():
    st.subheader("📡 Scansione Prodotto")
    barcode = st.text_input("Inquadra il codice a barre o inseriscilo manualmente", placeholder="Es. 800123...", key="barcode_input")

if barcode:
    barcode_clean = str(barcode).strip()
    risultato = df_inventario[df_inventario['Codice a Barre'] == barcode_clean]

    if not risultato.empty:
        item = risultato.iloc[-1]
        
        # --- SCHEDA PRODOTTO TROVATO ---
        with st.expander("✨ Prodotto Riconosciuto", expanded=True):
            st.markdown(f"### {item['Nome Prodotto']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Prezzo Unitario", f"€ {item['Prezzo standard']}")
            with col2:
                st.metric("Negozio", item['PUNTO VENDITA'])
            with col3:
                qta = st.number_input("Quantità", min_value=1, value=1, step=1)
            
            subtotale = float(item['Prezzo standard']) * qta
            
            if st.button("➕ AGGIUNGI AL CARRELLO", use_container_width=True, type="primary"):
                st.session_state.carrello.append({
                    "Prodotto": item['Nome Prodotto'],
                    "Negozio": item['PUNTO VENDITA'],
                    "Prezzo Unit.": float(item['Prezzo standard']),
                    "Q.tà": qta,
                    "Subtotale": subtotale
                })
                st.toast(f"Aggiunto: {item['Nome Prodotto']} (x{qta})")
    else:
        st.warning("⚠️ Prodotto non trovato nel database.")
        with st.expander("🆕 Aggiungi nuovo prodotto al database"):
            n_nome = st.text_input("Nome Prodotto")
            n_negozio = st.text_input("Punto Vendita")
            n_prezzo = st.number_input("Prezzo Standard", min_value=0.0, format="%.2f")
            if st.button("💾 Salva nel Foglio Google"):
                # Qui andrebbe la logica di update che abbiamo visto prima
                st.info("Funzione di salvataggio pronta per l'attivazione!")

# --- VISUALIZZAZIONE CARRELLO ---
if st.session_state.carrello:
    st.divider()
    st.subheader("📋 Il tuo Carrello")
    df_c = pd.DataFrame(st.session_state.carrello)
    
    # Mostriamo la tabella con stile
    st.dataframe(df_c, use_container_width=True, hide_index=True)
    
    totale_generale = df_c['Subtotale'].sum()
    
    c1, c2 = st.columns([2, 1])
    with c2:
        st.metric("TOTALE SPESA", f"€ {totale_generale:.2f}")
    
    if st.button("🗑️ Svuota tutto", type="secondary"):
        st.session_state.carrello = []
        st.rerun()
