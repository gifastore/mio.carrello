import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF

# Configurazione base
st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒")

# --- CONNESSIONE GOOGLE SHEETS ---
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Funzione per caricare i dati fresca
    def get_data():
        df = conn.read(spreadsheet=URL_FOGLIO, worksheet="0")
        df['Barcode'] = df['Barcode'].astype(str).str.strip()
        return df
    
    df_inventario = get_data()
except:
    st.error("Connessione al database fallita. Controlla l'URL del foglio.")
    df_inventario = pd.DataFrame(columns=['Barcode', 'Nome Prodotto', 'Prezzo'])

# Inizializzazione sessione
if 'carrello' not in st.session_state:
    st.session_state.carrello = []

st.title("🛒 Vibe Smart Spesa")

# --- INPUT PRINCIPALE ---
# Qui è dove la tastiera di Antonov scriverà il codice
barcode_input = st.text_input("📡 Scansiona ora", placeholder="Tocca qui e usa lo scanner della tastiera...")

# Ricerca nel database
prodotto_trovato = df_inventario[df_inventario['Barcode'] == str(barcode_input).strip()]

with st.form("aggiunta_prodotto", clear_on_submit=True):
    if not prodotto_trovato.empty and barcode_input:
        n_def = prodotto_trovato.iloc[0]['Nome Prodotto']
        p_def = float(prodotto_trovato.iloc[0]['Prezzo'])
        st.success(f"✅ Prodotto: **{n_def}**")
        is_new = False
    else:
        n_def = ""
        p_def = 0.0
        is_new = True
        if barcode_input:
            st.warning("🆕 Prodotto non trovato. Inserisci i dettagli per aggiungerlo.")

    nome = st.text_input("Nome Prodotto", value=n_def)
    prezzo = st.number_input("Prezzo (€)", value=p_def, format="%.2f", step=0.01)
    qty = st.number_input("Quantità", min_value=1, value=1)
    
    col1, col2 = st.columns(2)
    with col1:
        add_btn = st.form_submit_button("➕ AGGIUNGI")
    with col2:
        # Appare solo se il prodotto non è nel database
        save_btn = st.form_submit_button("💾 SALVA NEL DB") if is_new and barcode_input else False

    if add_btn and nome and prezzo > 0:
        st.session_state.carrello.append({
            "Nome": nome, "Prezzo": prezzo, "Qty": qty, "Totale": round(prezzo * qty, 2)
        })
        st.rerun()

    if save_btn and barcode_input and nome and prezzo > 0:
        nuovo_dato = pd.DataFrame([[barcode_input, nome, prezzo]], columns=['Barcode', 'Nome Prodotto', 'Prezzo'])
        df_aggiornato = pd.concat([df_inventario, nuovo_dato], ignore_index=True)
        conn.update(spreadsheet=URL_FOGLIO, data=df_aggiornato)
        st.success("Database aggiornato! 🚀")
        st.cache_data.clear()

# --- TABELLA CARRELLO ---
if st.session_state.carrello:
    st.divider()
    df_carrello = pd.DataFrame(st.session_state.carrello)
    st.dataframe(df_carrello[['Nome', 'Qty', 'Totale']], use_container_width=True, hide_index=True)
    
    totale = df_carrello['Totale'].sum()
    st.subheader(f"Totale: € {totale:.2f}")

    if st.button("🗑️ SVUOTA TUTTO"):
        st.session_state.carrello = []
        st.rerun()
