import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒")

# --- CONFIGURAZIONE DATABASE ---
# Incolla qui l'URL esatto del tuo nuovo foglio
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    def carica_dati():
        # Leggiamo il foglio per NOME (es. "Foglio1") per evitare errori di indice
        df = conn.read(spreadsheet=URL_FOGLIO, worksheet="Foglio1") 
        df.columns = df.columns.str.strip() # Pulisce spazi nei nomi colonne
        if 'Codice a Barre' in df.columns:
            df['Codice a Barre'] = df['Codice a Barre'].astype(str).str.strip()
        return df
    df_inventario = carica_dati()
except Exception as e:
    st.error(f"⚠️ Errore di connessione: {e}")
    df_inventario = pd.DataFrame(columns=['Codice a Barre', 'PUNTO VENDITA', 'Nome Prodotto', 'Prezzo standard'])

if 'carrello' not in st.session_state:
    st.session_state.carrello = []

# --- INTERFACCIA ---
st.sidebar.header("⚙️ Impostazioni")
lista_negozi = ["Scegli il negozio...", "Conad", "Coop", "Esselunga", "Lidl", "Eurospin", "Carrefour", "Altro"]
negozio_sel = st.sidebar.selectbox("Punto Vendita attuale:", options=lista_negozi)

st.title("🛒 Vibe Smart Spesa")

if negozio_sel == "Scegli il negozio...":
    st.info("👈 Seleziona un negozio nella barra laterale per iniziare.")
    st.stop()

# --- SCANSIONE E LOGICA ---
barcode_input = st.text_input("📡 Scansiona prodotto", key="barcode_scanner")

prodotto_trovato = df_inventario[df_inventario['Codice a Barre'] == str(barcode_input).strip()]

with st.form("aggiunta_form", clear_on_submit=True):
    if not prodotto_trovato.empty and barcode_input:
        item = prodotto_trovato.iloc[-1]
        n_def = item['Nome Prodotto']
        p_def = float(item['Prezzo standard'])
        st.success(f"✅ Prodotto trovato: {n_def}")
        is_new = False
    else:
        n_def = ""
        p_def = 0.0
        is_new = True

    nome = st.text_input("Nome Prodotto", value=n_def)
    prezzo = st.number_input("Prezzo (€)", value=p_def, format="%.2f")
    qty = st.number_input("Quantità", min_value=1, value=1)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.form_submit_button("➕ AGGIUNGI"):
            st.session_state.carrello.append({
                "Negozio": negozio_sel, "Nome": nome, "Prezzo": prezzo, "Qty": qty, "Totale": round(prezzo * qty, 2)
            })
            st.rerun()
    with col2:
        if is_new and barcode_input:
            if st.form_submit_button("💾 MEMORIZZA"):
                nuovo = pd.DataFrame([[barcode_input, negozio_sel, nome, prezzo]], 
                                     columns=['Codice a Barre', 'PUNTO VENDITA', 'Nome Prodotto', 'Prezzo standard'])
                df_aggiornato = pd.concat([df_inventario, nuovo], ignore_index=True)
                conn.update(spreadsheet=URL_FOGLIO, data=df_aggiornato)
                st.cache_data.clear()
                st.success("Salvato!")

# --- CARRELLO ---
if st.session_state.carrello:
    st.divider()
    df_c = pd.DataFrame(st.session_state.carrello)
    st.table(df_c[['Nome', 'Qty', 'Totale']])
    st.subheader(f"Totale: € {df_c['Totale'].sum():.2f}")
