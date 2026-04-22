import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_barcode_scanner import st_barcode_scanner
import pandas as pd
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒")

# --- CONFIGURAZIONE DATABASE ---
# INCOLLA QUI L'URL DEL TUO FOGLIO GOOGLE
URL_FOGLIO = "INSERISCI_QUI_IL_TUO_URL"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_inventario = conn.read(spreadsheet=URL_FOGLIO, worksheet="Inventario")
    # Pulizia dati: trasformiamo i barcode in stringhe per il confronto
    df_inventario['Barcode'] = df_inventario['Barcode'].astype(str)
except:
    st.error("Errore di connessione al Foglio Google. Verifica l'URL e i permessi di condivisione.")
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

# --- 2. SCANSIONE E RICERCA ---
st.subheader("🔍 Aggiungi Prodotto")
st.write("Inquadra il codice a barre con la camera:")

# Attiva lo scanner
barcode_rilevato = st_barcode_scanner()

# Se non rileva nulla o vuoi scrivere a mano
barcode_manuale = st.text_input("Oppure scrivi il codice a barre manualmente")
barcode_finale = str(barcode_rilevato) if barcode_rilevato else barcode_manuale

# Cerca nel database
prodotto_trovato = df_inventario[df_inventario['Barcode'] == barcode_finale]

with st.form("form_inserimento"):
    if not prodotto_trovato.empty:
        nome_default = prodotto_trovato.iloc[0]['Nome Prodotto']
        prezzo_default = float(prodotto_trovato.iloc[0]['Prezzo'])
        st.success(f"✅ Prodotto riconosciuto: {nome_default}")
    else:
        nome_default = ""
        prezzo_default = 0.0
        if barcode_finale != "":
            st.warning("⚠️ Nuovo prodotto! Inserisci i dati per memorizzarli.")

    nome = st.text_input("Nome Prodotto", value=nome_default)
    prezzo = st.number_input("Prezzo Unitario (€)", value=prezzo_default, format="%.2f")
    qty = st.number_input("Quantità", min_value=1, value=1)
    
    btn_aggiungi = st.form_submit_button("AGGIUNGI AL CARRELLO")

    if btn_aggiungi:
        if nome != "" and barcode_finale != "":
            # Aggiungi al carrello della sessione
            st.session_state.carrello.append({
                "Barcode": barcode_finale,
                "Nome": nome,
                "Prezzo": prezzo,
                "Qty": qty,
                "Totale": prezzo * qty
            })
            
            # Se è nuovo, salva nel Foglio Google
            if prodotto_trovato.empty:
                nuova_riga = pd.DataFrame([{"Barcode": barcode_finale, "Nome Prodotto": nome, "Prezzo": prezzo}])
                df_aggiornato = pd.concat([df_inventario, nuova_riga], ignore_index=True)
                conn.update(spreadsheet=URL_FOGLIO, worksheet="Inventario", data=df_aggiornato)
                st.toast("Dati salvati nel database!")
        else:
            st.error("Inserisci almeno il nome del prodotto.")

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
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(100, 10, "Prodotto", 1)
        pdf.cell(30, 10, "Qty", 1)
        pdf.cell(30, 10, "Prezzo", 1)
        pdf.cell(30, 10, "Tot", 1, ln=True)
        
        pdf.set_font("Arial", size=12)
        for _, row in df_c.iterrows():
            pdf.cell(100, 10, str(row['Nome']), 1)
            pdf.cell(30, 10, str(row['Qty']), 1)
            pdf.cell(30, 10, f"{row['Prezzo']:.2f}", 1)
            pdf.cell(30, 10, f"{row['Totale']:.2f}", 1, ln=True)
        
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, f"TOTALE GENERALE: EUR {totale_spesa:.2f}", ln=True, align='R')
        
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button("⬇️ SCARICA PDF", data=pdf_bytes, file_name=f"spesa_{data_acquisto}.pdf")

if st.button("🗑️ Svuota Carrello"):
    st.session_state.carrello = []
    st.rerun()
