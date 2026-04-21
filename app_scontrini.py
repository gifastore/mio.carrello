import streamlit as st
import pandas as pd
from fpdf import FPDF

st.set_page_config(page_title="Vibe Scontrino", layout="centered")
st.title("📄 Generatore Scontrini")

# Database temporaneo per la sessione attuale
if 'prodotti' not in st.session_state:
    st.session_state.prodotti = []

st.subheader("1. Aggiungi Prodotto")
foto = st.camera_input("Inquadra prodotto (opzionale)")

with st.form("dati_prodotto"):
    desc = st.text_input("Nome Prodotto")
    qty = st.number_input("Quantità", min_value=1, value=1)
    prezzo = st.number_input("Prezzo (€)", min_value=0.0, format="%.2f")
    
    if st.form_submit_button("Aggiungi alla lista"):
        st.session_state.prodotti.append({
            "desc": desc, "qty": qty, "prezzo": prezzo, "sub": qty * prezzo
        })
        st.success(f"{desc} aggiunto!")

if st.session_state.prodotti:
    df = pd.DataFrame(st.session_state.prodotti)
    st.table(df[['desc', 'qty', 'prezzo', 'sub']])
    totale = df['sub'].sum()
    st.header(f"Totale: €{totale:.2f}")

    if st.button("Genera PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "SCONTRINO DIGITALE", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.ln(10)
        for p in st.session_state.prodotti:
            pdf.cell(200, 10, f"{p['desc']} (x{p['qty']}) - €{p['sub']:.2f}", ln=True)
        pdf.ln(5)
        pdf.cell(200, 10, f"TOTALE: €{totale:.2f}", ln=True)
        
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button("⬇️ Scarica PDF", data=pdf_bytes, file_name="scontrino.pdf")

if st.button("Nuovo Scontrino"):
    st.session_state.prodotti = []
    st.rerun()
