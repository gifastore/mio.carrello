import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒", layout="centered")

# --- CONNESSIONE GOOGLE SHEETS ---
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    def carica_dati():
        # Legge il foglio e pulisce i dati
        df = conn.read(spreadsheet=URL_FOGLIO, worksheet="0")
        df['Barcode'] = df['Barcode'].astype(str).str.strip()
        return df
    df_inventario = carica_dati()
except Exception as e:
    st.error(f"Errore database: {e}")
    df_inventario = pd.DataFrame(columns=['Barcode', 'Nome Prodotto', 'Prezzo', 'Punto Vendita'])

# Inizializzazione Carrello
if 'carrello' not in st.session_state:
    st.session_state.carrello = []

# --- SIDEBAR: SETTINGS ---
st.sidebar.header("⚙️ Impostazioni")
negozio = st.sidebar.selectbox(
    "Punto Vendita:",
    ["Conad", "Coop", "Esselunga", "Carrefour", "Lidl", "Eurospin", "Despar", "Altro"]
)

if st.sidebar.button("🗑️ Svuota Carrello"):
    st.session_state.carrello = []
    st.rerun()

# --- INTERFACCIA PRINCIPALE ---
st.title("🛒 Vibe Smart Spesa")
st.info(f"📍 Negozio: **{negozio}**")

# Campo input ottimizzato per la tastiera scanner
barcode_input = st.text_input("📡 Scansiona ora", placeholder="Usa il tasto scanner della tastiera...", help="Tocca qui e attiva lo scanner di Nikola Antonov")

# Ricerca nel database
prodotto_trovato = df_inventario[df_inventario['Barcode'] == str(barcode_input).strip()]

with st.form("aggiunta_form", clear_on_submit=True):
    if not prodotto_trovato.empty and barcode_input:
        # Se esistono più prezzi, prende l'ultimo inserito
        item = prodotto_trovato.iloc[-1]
        n_def = item['Nome Prodotto']
        p_def = float(item['Prezzo'])
        st.success(f"✅ Prodotto riconosciuto: **{n_def}**")
        is_new = False
    else:
        n_def = ""
        p_def = 0.0
        is_new = True
        if barcode_input:
            st.warning("🆕 Prodotto non trovato nel database.")

    nome = st.text_input("Nome Prodotto", value=n_def)
    prezzo = st.number_input("Prezzo (€)", value=p_def, format="%.2f", step=0.01)
    qty = st.number_input("Quantità", min_value=1, value=1, step=1)
    
    col1, col2 = st.columns(2)
    with col1:
        add_btn = st.form_submit_button("➕ AGGIUNGI AL CARRELLO")
    with col2:
        save_btn = st.form_submit_button("💾 SALVA NEL DATABASE") if is_new and barcode_input else False

    # Logica Aggiunta
    if add_btn and nome and prezzo > 0:
        st.session_state.carrello.append({
            "Data": datetime.now().strftime("%d/%m/%Y"),
            "Negozio": negozio,
            "Nome": nome,
            "Prezzo": prezzo,
            "Qty": qty,
            "Totale": round(prezzo * qty, 2)
        })
        st.toast(f"Aggiunto: {nome}")
        st.rerun()

    # Logica Salvataggio Database
    if save_btn and barcode_input and nome and prezzo > 0:
        nuovo_prodotto = pd.DataFrame([[barcode_input, nome, prezzo, negozio]], 
                                      columns=['Barcode', 'Nome Prodotto', 'Prezzo', 'Punto Vendita'])
        df_aggiornato = pd.concat([df_inventario, nuovo_prodotto], ignore_index=True)
        conn.update(spreadsheet=URL_FOGLIO, data=df_aggiornato)
        st.cache_data.clear()
        st.success(f"Memorizzato nel database! 🎉")

# --- VISUALIZZAZIONE SPESA ---
if st.session_state.carrello:
    st.divider()
    st.subheader("📝 Lista Spesa Corrente")
    df_c = pd.DataFrame(st.session_state.carrello)
    
    # Tabella riassuntiva
    st.dataframe(df_c[['Nome', 'Qty', 'Totale']], use_container_width=True, hide_index=True)
    
    totale_euro = df_c['Totale'].sum()
    st.metric("TOTALE DA PAGARE", f"€ {totale_euro:.2f}")

    # Esportazione PDF
    if st.button("📄 GENERA SCONTRINO PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(200, 10, "VIBE SMART SPESA", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
        pdf.cell(200, 10, f"Negozio: {negozio}", ln=True, align='C')
        pdf.ln(10)
        
        # Intestazione Tabella
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(100, 10, "Prodotto", 1)
        pdf.cell(30, 10, "Prezzo", 1)
        pdf.cell(20, 10, "Qty", 1)
        pdf.cell(40, 10, "Totale", 1, ln=True)
        
        # Righe
        pdf.set_font("Arial", size=12)
        for _, r in df_c.iterrows():
            pdf.cell(100, 10, str(r['Nome']), 1)
            pdf.cell(30, 10, f"{r['Prezzo']:.2f}", 1)
            pdf.cell(20, 10, str(r['Qty']), 1)
            pdf.cell(40, 10, f"{r['Totale']:.2f}", 1, ln=True)
            
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, f"TOTALE: Euro {totale_euro:.2f}", ln=True, align='R')
        
        pdf_out = pdf.output(dest='S').encode('latin-1')
        st.download_button("⬇️ Scarica Scontrino", data=pdf_out, file_name=f"spesa_{negozio}.pdf", mime="application/pdf")
