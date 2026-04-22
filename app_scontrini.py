import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒")

# --- DATABASE ---
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Leggiamo il foglio Inventario (gid=0)
    df_inventario = conn.read(spreadsheet=URL_FOGLIO, worksheet="0")
    df_inventario['Barcode'] = df_inventario['Barcode'].astype(str)
except Exception as e:
    st.error(f"Errore caricamento dati: {e}")
    df_inventario = pd.DataFrame(columns=['Barcode', 'Nome Prodotto', 'Prezzo'])

st.title("🛒 Spesa Intelligente")

# --- DATI GENERALI ---
with st.expander("🏨 Negozio e Data", expanded=True):
    col_a, col_b = st.columns(2)
    punto_vendita = col_a.text_input("🏪 Negozio", value="Supermercato")
    data_acquisto = col_b.date_input("📅 Data", datetime.now())

if 'carrello' not in st.session_state:
    st.session_state.carrello = []

# --- AGGIUNTA ---
st.subheader("🔍 Aggiungi Prodotto")
barcode_inserito = st.text_input("Inserisci Codice a Barre")

# Cerca se il prodotto esiste già nell'inventario
prodotto_trovato = df_inventario[df_inventario['Barcode'] == str(barcode_inserito)]

with st.form("form_spesa", clear_on_submit=True):
    if not prodotto_trovato.empty:
        n_def = prodotto_trovato.iloc[0]['Nome Prodotto']
        p_def = float(prodotto_trovato.iloc[0]['Prezzo'])
        st.success(f"Trovato: {n_def} (€{p_def})")
    else:
        n_def = ""
        p_def = 0.0
        if barcode_inserito:
            st.info("Codice nuovo: inserisci nome e prezzo manualmente")

    nome = st.text_input("Nome Prodotto", value=n_def)
    prezzo = st.number_input("Prezzo (€)", value=p_def, format="%.2f")
    qty = st.number_input("Quantità", min_value=1, value=1)
    
    if st.form_submit_button("AGGIUNGI AL CARRELLO"):
        if nome:
            st.session_state.carrello.append({
                "Nome": nome, 
                "Prezzo": prezzo, 
                "Qty": qty, 
                "Totale": prezzo * qty
            })
            st.toast(f"{nome} aggiunto!")
        else:
            st.error("Inserisci il nome del prodotto")

# --- RIEPILOGO E PDF ---
if st.session_state.carrello:
    st.divider()
    df_c = pd.DataFrame(st.session_state.carrello)
    st.table(df_c[['Nome', 'Qty', 'Prezzo', 'Totale']])
    
    totale_spesa = df_c['Totale'].sum()
    st.header(f"Totale: € {totale_spesa:.2f}")

    if st.button("📄 GENERA SCONTRINO PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, f"SCONTRINO: {punto_vendita.upper()}", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 7, f"Data: {data_acquisto}", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(100, 10, "Prodotto", 1)
        pdf.cell(30, 10, "Qty", 1)
        pdf.cell(40, 10, "Totale", 1, ln=True)
        
        pdf.set_font("Arial", size=12)
        for _, row in df_c.iterrows():
            pdf.cell(100, 10, str(row['Nome']), 1)
            pdf.cell(30, 10, str(row['Qty']), 1)
            pdf.cell(40, 10, f"EUR {row['Totale']:.2f}", 1, ln=True)
        
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(170, 10, f"TOTALE GENERALE: EUR {totale_spesa:.2f}", ln=True, align='R')
        
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button("⬇️ SCARICA PDF", data=pdf_bytes, file_name=f"spesa_{data_acquisto}.pdf")

if st.button("🗑️ Svuota Carrello"):
    st.session_state.carrello = []
    st.rerun()
