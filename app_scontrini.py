import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
from pyzbar.pyzbar import decode
import numpy as np

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

if 'carrello' not in st.session_state:
    st.session_state.carrello = []

# --- SCANSIONE FOTO ---
st.subheader("📸 Scansiona Codice a Barre")
foto = st.camera_input("Inquadra bene il codice e scatta")

barcode_rilevato = ""

if foto:
    # Trasforma la foto in un formato leggibile
    img = Image.open(foto)
    
    # --- POTENZIAMENTO IMMAGINE ---
    # Convertiamo in scala di grigi per aiutare il lettore
    img_gray = img.convert('L') 
    
    # Proviamo a leggere sia l'originale che quella migliorata
    risultati = decode(img_gray) or decode(img)
    
    if risultati:
        barcode_rilevato = risultati[0].data.decode('utf-8')
        st.success(f"✅ Codice rilevato: {barcode_rilevato}")
    else:
        st.warning("❌ Codice non trovato. Prova ad avvicinarti o a migliorare la luce.")

# --- INSERIMENTO DATI ---
st.divider()
barcode_finale = st.text_input("Codice a Barre attuale", value=barcode_rilevato)

prodotto_trovato = df_inventario[df_inventario['Barcode'] == str(barcode_finale)]

with st.form("form_spesa", clear_on_submit=True):
    if not prodotto_trovato.empty:
        n_def = prodotto_trovato.iloc[0]['Nome Prodotto']
        p_def = float(prodotto_trovato.iloc[0]['Prezzo'])
    else:
        n_def = ""
        p_def = 0.0

    nome = st.text_input("Nome Prodotto", value=n_def)
    prezzo = st.number_input("Prezzo (€)", value=p_def, format="%.2f")
    qty = st.number_input("Quantità", min_value=1, value=1)
    
    if st.form_submit_button("AGGIUNGI AL CARRELLO"):
        if nome != "" and prezzo > 0:
            st.session_state.carrello.append({
                "Nome": nome, "Prezzo": prezzo, "Qty": qty, "Totale": round(prezzo * qty, 2)
            })
            st.rerun()

# --- RIEPILOGO ---
if st.session_state.carrello:
    df_c = pd.DataFrame(st.session_state.carrello)
    st.dataframe(df_c, use_container_width=True, hide_index=True)
    
    totale = df_c['Totale'].sum()
    st.header(f"Totale: € {totale:.2f}")

    if st.button("📄 GENERA PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "SCONTRINO SPESA", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        for _, r in df_c.iterrows():
            pdf.cell(200, 10, f"{r['Nome']} x{r['Qty']} - €{r['Totale']:.2f}", ln=True)
        pdf.cell(200, 10, f"TOTALE: €{totale:.2f}", ln=True, align='R')
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button("⬇️ SCARICA PDF", data=pdf_bytes, file_name="spesa.pdf")

if st.button("🗑️ Svuota Carrello"):
    st.session_state.carrello = []
    st.rerun()
