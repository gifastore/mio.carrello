import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# Configurazione
st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒")

# --- CONNESSIONE GOOGLE SHEETS ---
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_inventario = conn.read(spreadsheet=URL_FOGLIO, worksheet="0")
    df_inventario['Barcode'] = df_inventario['Barcode'].astype(str)
except Exception:
    df_inventario = pd.DataFrame(columns=['Barcode', 'Nome Prodotto', 'Prezzo'])

st.title("🛒 Vibe Smart Spesa")

if 'carrello' not in st.session_state:
    st.session_state.carrello = []

# --- AREA AGGIUNTA ---
st.subheader("🔍 Cerca o Aggiungi")
barcode_input = st.text_input("Scansiona o digita il codice a barre", placeholder="Usa la tastiera o scansiona...")

# Ricerca nel database
prodotto_trovato = df_inventario[df_inventario['Barcode'] == str(barcode_input)]

with st.form("form_aggiunta", clear_on_submit=True):
    if not prodotto_trovato.empty:
        n_def = prodotto_trovato.iloc[0]['Nome Prodotto']
        p_def = float(prodotto_trovato.iloc[0]['Prezzo'])
        st.success(f"Trovato: {n_def}")
    else:
        n_def = ""
        p_def = 0.0
        if barcode_input: st.info("Prodotto nuovo! Inserisci i dati sotto.")

    nome = st.text_input("Nome Prodotto", value=n_def)
    prezzo = st.number_input("Prezzo (€)", value=p_def, format="%.2f")
    qty = st.number_input("Quantità", min_value=1, value=1)
    
    if st.form_submit_button("➕ AGGIUNGI AL CARRELLO"):
        if nome and prezzo > 0:
            st.session_state.carrello.append({
                "Nome": nome, "Prezzo": prezzo, "Qty": qty, "Totale": round(prezzo * qty, 2)
            })
            st.rerun()

# --- CARRELLO ---
if st.session_state.carrello:
    st.divider()
    df_c = pd.DataFrame(st.session_state.carrello)
    st.dataframe(df_c[['Nome', 'Qty', 'Totale']], use_container_width=True, hide_index=True)
    
    totale_generale = df_c['Totale'].sum()
    st.subheader(f"Totale: € {totale_generale:.2f}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 GENERA PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, "VIBE SMART SPESA", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.ln(10)
            for _, row in df_c.iterrows():
                pdf.cell(150, 10, f"{row['Nome']} x{row['Qty']}", 1)
                pdf.cell(40, 10, f"E {row['Totale']:.2f}", 1, ln=True)
            pdf.ln(5)
            pdf.cell(190, 10, f"TOTALE: E {totale_generale:.2f}", ln=True, align='R')
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button("⬇️ Scarica Scontrino", data=pdf_bytes, file_name="spesa.pdf")
    
    with col2:
        if st.button("🗑️ SVUOTA"):
            st.session_state.carrello = []
            st.rerun()
