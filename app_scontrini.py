import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_barcode_reader import barcode_reader # La nuova libreria
import pandas as pd
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒")

# --- DATABASE ---
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_inventario = conn.read(spreadsheet=URL_FOGLIO, worksheet="0")
    df_inventario['Barcode'] = df_inventario['Barcode'].astype(str)
except Exception as e:
    st.error(f"Errore database: {e}")
    df_inventario = pd.DataFrame(columns=['Barcode', 'Nome Prodotto', 'Prezzo'])

st.title("🛒 Spesa Intelligente")

# --- NUOVO LETTORE BARCODE ---
st.subheader("📸 Scansione Rapida")
# Questo apre la camera e legge in tempo reale
barcode_rilevato = barcode_reader(label="Inquadra il codice")

if barcode_rilevato:
    st.success(f"✅ Codice letto: {barcode_rilevato}")

# --- FORM INSERIMENTO ---
st.divider()
barcode_finale = st.text_input("Codice a Barre", value=barcode_rilevato if barcode_rilevato else "")

prodotto_trovato = df_inventario[df_inventario['Barcode'] == str(barcode_finale)]

with st.form("form_spesa", clear_on_submit=True):
    n_def = prodotto_trovato.iloc[0]['Nome Prodotto'] if not prodotto_trovato.empty else ""
    p_def = float(prodotto_trovato.iloc[0]['Prezzo']) if not prodotto_trovato.empty else 0.0

    nome = st.text_input("Nome Prodotto", value=n_def)
    prezzo = st.number_input("Prezzo (€)", value=p_def, format="%.2f")
    qty = st.number_input("Quantità", min_value=1, value=1)
    
    if st.form_submit_button("AGGIUNGI AL CARRELLO"):
        if nome != "" and prezzo > 0:
            if 'carrello' not in st.session_state: st.session_state.carrello = []
            st.session_state.carrello.append({
                "Nome": nome, "Prezzo": prezzo, "Qty": qty, "Totale": round(prezzo * qty, 2)
            })
            st.rerun()

# --- TABELLA E PDF (Come prima) ---
if 'carrello' in st.session_state and st.session_state.carrello:
    df_c = pd.DataFrame(st.session_state.carrello)
    st.table(df_c[['Nome', 'Qty', 'Totale']])
    if st.button("🗑️ Svuota"):
        st.session_state.carrello = []; st.rerun()
