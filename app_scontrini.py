import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒")

# --- DATABASE ---
# INCOLLA QUI IL TUO URL DI GOOGLE SHEETS
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Usiamo "0" che è il codice del tuo foglio Inventario
    df_inventario = conn.read(spreadsheet=URL_FOGLIO, worksheet="0")
    df_inventario['Barcode'] = df_inventario['Barcode'].astype(str)
except Exception as e:
    st.error(f"Connessione fallita: {e}")
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
barcode_finale = st.text_input("Inserisci Codice a Barre")

prodotto_trovato = df_inventario[df_inventario['Barcode'] == str(barcode_finale)]

with st.form("form_spesa", clear_on_submit=True):
    if not prodotto_trovato.empty:
        n_def = prodotto_trovato.iloc[0]['Nome Prodotto']
        p_def = float(prodotto_trovato.iloc[0]['Prezzo'])
        st.success(f"Trovato: {n_def}")
    else:
        n_def = ""
        p_def = 0.0

    nome = st.text_input("Nome Prodotto", value=n_def)
    prezzo = st.number_input("Prezzo (€)", value=p_def, format="%.2f")
    qty = st.number_input("Quantità", min_value=1, value=1)
    
    if st.form_submit_button("AGGIUNGI"):
        if nome:
            st.session_state.carrello.append({
                "Nome": nome, "Prezzo": prezzo, "Qty": qty, "Totale": prezzo * qty
            })
            if prodotto_trovato.empty and barcode_finale:
                nuovo = pd.DataFrame([{"Barcode": barcode_finale, "Nome Prodotto": nome, "Prezzo": prezzo}])
                df_up = pd.concat([df_inventario, nuovo], ignore_index=True)
                # Anche qui mettiamo "0"
                conn.update(spreadsheet=URL_FOGLIO, worksheet="0", data=df_up)
                st.toast("Salvato in database!")
        else:
            st.error("Manca il nome!")

# --- RIEPILOGO ---
if st.session_state.carrello:
    df_c = pd.DataFrame(st.session_state.carrello)
    st.table(df_c)
    totale = df_c['Totale'].sum()
    st.header(f"Totale: €{totale:.2f}")

    if st.button("📄 Genera PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, f"SCONTRINO: {punto_vendita.upper()}", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        for _, r in df_c.iterrows():
            pdf.cell(200, 10, f"{r['Nome']} x{r['Qty']} - €{r['Totale']:.2f}", ln=True)
        pdf.cell(200, 10, f"TOTALE: €{totale:.2f}", ln=True, align='R')
        
        pdf_out = pdf.output(dest='S').encode('latin-1')
        st.download_button("⬇️ Scarica PDF", data=pdf_out, file_name="spesa.pdf")

if st.button("🗑️ Svuota"):
    st.session_state.carrello = []
    st.rerun()
