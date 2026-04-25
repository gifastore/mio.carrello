import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒")

# --- CONNESSIONE GOOGLE SHEETS ---
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    def carica_dati():
        # Legge il foglio e pulisce i dati
        df = conn.read(spreadsheet=URL_FOGLIO, worksheet="0")
        # Forza il barcode a essere trattato come testo senza spazi
        df['Codice a Barre'] = df['Codice a Barre'].astype(str).str.strip()
        return df
    df_inventario = carica_dati()
except Exception as e:
    st.error("Errore di connessione al Foglio Google.")
    df_inventario = pd.DataFrame(columns=['Codice a Barre', 'PUNTO VENDITA', 'Nome Prodotto', 'Prezzo standard'])

if 'carrello' not in st.session_state:
    st.session_state.carrello = []

# --- SIDEBAR: SCELTA NEGOZIO ---
st.sidebar.header("⚙️ Impostazioni")
lista_negozi = ["Scegli il negozio...", "Conad", "Coop", "Esselunga", "Lidl", "Eurospin", "Carrefour", "Altro"]
negozio_sel = st.sidebar.selectbox("Punto Vendita attuale:", options=lista_negozi, index=0)

if st.sidebar.button("🗑️ Svuota Carrello"):
    st.session_state.carrello = []
    st.rerun()

st.title("🛒 Vibe Smart Spesa")

if negozio_sel == "Scegli il negozio...":
    st.warning("👈 Seleziona il negozio nella barra laterale per iniziare.")
    st.stop()

# --- INPUT E ASSOCIAZIONE AUTOMATICA ---
barcode_input = st.text_input("📡 Scansiona ora", placeholder="Inquadra il codice con la tastiera...")

# Cerca il prodotto usando il TUO nome colonna: 'Codice a Barre'
prodotto_trovato = df_inventario[df_inventario['Codice a Barre'] == str(barcode_input).strip()]

with st.form("aggiunta_form", clear_on_submit=True):
    if not prodotto_trovato.empty and barcode_input:
        item = prodotto_trovato.iloc[-1]
        n_def = item['Nome Prodotto']
        p_def = float(item['Prezzo standard'])
        st.success(f"✅ Riconosciuto: **{n_def}**")
        is_new = False
    else:
        n_def = ""
        p_def = 0.0
        is_new = True
        if barcode_input:
            st.info("🆕 Prodotto non a sistema. Inserisci i dettagli.")

    nome = st.text_input("Nome Prodotto", value=n_def)
    prezzo = st.number_input("Prezzo (€)", value=p_def, format="%.2f")
    qty = st.number_input("Quantità", min_value=1, value=1)
    
    col1, col2 = st.columns(2)
    with col1:
        add_btn = st.form_submit_button("➕ AGGIUNGI AL CARRELLO")
    with col2:
        # Salva nel DB usando i tuoi nomi colonne
        save_btn = st.form_submit_button("💾 MEMORIZZA PRODOTTO") if is_new and barcode_input else False

    if add_btn and nome and prezzo > 0:
        st.session_state.carrello.append({
            "Negozio": negozio_sel,
            "Nome": nome, 
            "Prezzo": prezzo, 
            "Qty": qty, 
            "Totale": round(prezzo * qty, 2)
        })
        st.rerun()

    if save_btn and barcode_input and nome and prezzo > 0:
        nuovo = pd.DataFrame([[barcode_input, negozio_sel, nome, prezzo]], 
                             columns=['Codice a Barre', 'PUNTO VENDITA', 'Nome Prodotto', 'Prezzo standard'])
        df_aggiornato = pd.concat([df_inventario, nuovo], ignore_index=True)
        conn.update(spreadsheet=URL_FOGLIO, data=df_aggiornato)
        st.cache_data.clear()
        st.success("Dati salvati! Ora l'associazione sarà automatica. 🎉")

# --- VISUALIZZAZIONE E PDF ---
if st.session_state.carrello:
    st.divider()
    df_c = pd.DataFrame(st.session_state.carrello)
    st.table(df_c[['Nome', 'Qty', 'Totale']])
    
    totale_spesa = df_c['Totale'].sum()
    st.subheader(f"Totale: € {totale_spesa:.2f}")

    if st.button("📄 GENERA SCONTRINO PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "SCONTRINO VIBE SMART", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, f"Negozio: {negozio_sel} - Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
        pdf.ln(10)
        
        for _, r in df_c.iterrows():
            linea = f"{r['Nome']} (x{r['Qty']}) - € {r['Totale']:.2f}"
            pdf.cell(200, 10, linea, ln=True)
        
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, f"TOTALE: Euro {totale_spesa:.2f}", ln=True, align='R')
        
        pdf_out = pdf.output(dest='S').encode('latin-1')
        st.download_button("⬇️ Scarica PDF", data=pdf_out, file_name="scontrino.pdf", mime="application/pdf")
