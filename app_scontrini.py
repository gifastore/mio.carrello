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

# Ricerca automatica nell'inventario
prodotto_trovato = df_inventario[df_inventario['Barcode'] == str(barcode_inserito)]

with st.form("form_spesa", clear_on_submit=True):
    if not prodotto_trovato.empty:
        n_def = prodotto_trovato.iloc[0]['Nome Prodotto']
        p_def = float(prodotto_trovato.iloc[0]['Prezzo'])
        st.success(f"Trovato: {n_def} (€{p_def})")
    else:
        n_def = ""
        p_def = 0.0

    nome = st.text_input("Nome Prodotto", value=n_def)
    prezzo = st.number_input("Prezzo (€)", value=p_def, format="%.2f")
    qty = st.number_input("Quantità", min_value=1, value=1)
    
    submit = st.form_submit_button("AGGIUNGI AL CARRELLO")
    
    if submit:
        if nome != "" and prezzo > 0:
            st.session_state.carrello.append({
                "Nome": nome, 
                "Prezzo": prezzo, 
                "Qty": qty, 
                "Totale": round(prezzo * qty, 2)
            })
            st.rerun() # Ricarica l'app per aggiornare subito la tabella
        else:
            st.error("Inserisci un nome e un prezzo valido!")

# --- RIEPILOGO ---
if st.session_state.carrello:
    st.divider()
    df_c = pd.DataFrame(st.session_state.carrello)
    
    # Tabella formattata bene
    st.dataframe(df_c, use_container_width=True, hide_index=True)
    
    totale_spesa = df_c['Totale'].sum()
    st.header(f"Totale: € {totale_spesa:.2f}")

    # Bottone PDF
    if st.button("📄 GENERA SCONTRINO PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, f"SCONTRINO: {punto_vendita.upper()}", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 7, f"Data: {data_acquisto}", ln=True, align='C')
        pdf.ln(10)
        
        # Righe Prodotti nel PDF
        pdf.set_font("Arial", size=12)
        for _, row in df_c.iterrows():
            pdf.cell(100, 10, f"{row['Nome']} (x{row['Qty']})", 1)
            pdf.cell(50, 10, f"EUR {row['Totale']:.2f}", 1, ln=True)
        
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(150, 10, f"TOTALE: EUR {totale_spesa:.2f}", ln=True, align='R')
        
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button("⬇️ SCARICA PDF", data=pdf_bytes, file_name="scontrino.pdf")

if st.button("🗑️ Svuota Carrello"):
    st.session_state.carrello = []
    st.rerun()
