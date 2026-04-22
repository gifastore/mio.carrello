import streamlit as st
from streamlit_gsheets import GSheetsConnection
# Commentiamo la riga che dava errore per ora
# from streamlit_barcode_scanner import st_barcode_scanner 
import pandas as pd
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒")

# --- CONFIGURAZIONE DATABASE ---
# 1. INCOLLA QUI L'URL DEL TUO FOGLIO GOOGLE
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit?gid=571256712#gid=571256712"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 2. Assicurati che il tab del foglio si chiami "Inventario"
    df_inventario = conn.read(spreadsheet=URL_FOGLIO, worksheet="Inventario")
    df_inventario['Barcode'] = df_inventario['Barcode'].astype(str)
except Exception as e:
    st.error(f"Errore di connessione: {e}")
    df_inventario = pd.DataFrame(columns=['Barcode', 'Nome Prodotto', 'Prezzo'])

st.title("🛒 Spesa Intelligente")

# --- 1. DATI GENERALI ---
with st.expander("🏨 Dettagli Punto Vendita e Data", expanded=True):
    col_a, col_b = st.columns(2)
    with col_a:
        punto_vendita = st.text_input("🏪 Negozio", value="Supermercato")
    with col_b:
        data_acquisto = st.date_input("📅 Data Acquisto", datetime.now())

if 'carrello' not in st.session_state:
    st.session_state.carrello = []

# --- 2. AGGIUNTA PRODOTTI ---
st.subheader("🔍 Aggiungi Prodotto")

# Inserimento manuale del barcode (visto che lo scanner non si installa)
barcode_finale = st.text_input("Scrivi o incolla il codice a barre")

# Cerca nel database (Tab Inventario)
prodotto_trovato = df_inventario[df_inventario['Barcode'] == str(barcode_finale)]

with st.form("form_inserimento", clear_on_submit=True):
    if not prodotto_trovato.empty:
        nome_default = prodotto_trovato.iloc[0]['Nome Prodotto']
        prezzo_default = float(prodotto_trovato.iloc[0]['Prezzo'])
        st.success(f"✅ Prodotto riconosciuto: {nome_default}")
    else:
        nome_default = ""
        prezzo_default = 0.0
        if barcode_finale != "":
            st.warning("⚠️ Nuovo prodotto! Inserisci i dati per salvarli.")

    nome = st.text_input("Nome Prodotto", value=nome_default)
    prezzo = st.number_input("Prezzo Unitario (€)", value=prezzo_default, format="%.2f")
    qty = st.number_input("Quantità", min_value=1, value=1)
    
    btn_aggiungi = st.form_submit_button("AGGIUNGI AL CARRELLO")

    if btn_aggiungi:
        if nome != "" and barcode_finale != "":
            # Aggiunge alla lista temporanea
            st.session_state.carrello.append({
                "Barcode": barcode_finale,
                "Nome": nome,
                "Prezzo": prezzo,
                "Qty": qty,
                "Totale": prezzo * qty
            })
            
            # Se è nuovo, lo salva nel database Google Sheets (Tab Inventario)
            if prodotto_trovato.empty:
                nuova_riga = pd.DataFrame([{"Barcode": barcode_finale, "Nome Prodotto": nome, "Prezzo": prezzo}])
                df_aggiornato = pd.concat([df_inventario, nuova_riga], ignore_index=True)
                conn.update(spreadsheet=URL_FOGLIO, worksheet="Inventario", data=df_aggiornato)
                st.toast("Prodotto salvato in Inventario!")
        else:
            st.error("Dati mancanti!")

# --- 3. RIEPILOGO E PDF ---
if st.session_state.carrello:
    st.divider()
    df_c = pd.DataFrame(st.session_state.carrello)
    st.table(df_c[['Nome', 'Qty', 'Prezzo', 'Totale']])
    
    totale_spesa = df_c['Totale'].sum()
    st.metric("TOTALE DA PAGARE", f"€ {totale_spesa:.2f}")

    if st.button("📄 GENERA SCONTRINO PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, f"SCONTRINO: {punto_vendita.upper()}", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 7, f"Data: {data_acquisto}", ln=True, align='C')
        pdf.ln(10)
        
        # Intestazione Tabella PDF
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(100, 10, "Prodotto", 1)
        pdf.cell(30, 10, "Qty", 1)
        pdf.cell(30, 10, "Tot", 1, ln=True)
        
        # Righe Prodotti
        pdf.set_font("Arial", size=12)
        for _, row in df_c.iterrows():
            pdf.cell(100, 10, str(row['Nome']), 1)
            pdf.cell(30, 10, str(row['Qty']), 1)
            pdf.cell(30, 10, f"{row['Totale']:.2f}", 1, ln=True)
        
        pdf.ln(5)
        pdf.cell(200, 10, f"TOTALE: EUR {totale_spesa:.2f}", ln=True, align='R')
        
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button("⬇️ SCARICA PDF", data=pdf_bytes, file_name=f"spesa_{data_acquisto}.pdf")

if st.button("🗑️ Svuota Carrello"):
    st.session_state.carrello = []
    st.rerun()
