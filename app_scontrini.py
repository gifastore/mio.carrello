import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from PIL import Image

# Configurazione Pagina
st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒", layout="centered")

# --- CONNESSIONE GOOGLE SHEETS ---
# Sostituisci con l'URL del tuo foglio se diverso
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_inventario = conn.read(spreadsheet=URL_FOGLIO, worksheet="0")
    # Convertiamo i barcode in stringhe per evitare problemi con numeri grandi
    df_inventario['Barcode'] = df_inventario['Barcode'].astype(str).str.strip()
except Exception as e:
    st.error(f"Errore di connessione al database: {e}")
    df_inventario = pd.DataFrame(columns=['Barcode', 'Nome Prodotto', 'Prezzo'])

# Inizializzazione Carrello
if 'carrello' not in st.session_state:
    st.session_state.carrello = []

st.title("🛒 Vibe Smart Spesa")

# --- SEZIONE SCANSIONE ---
st.subheader("📸 Scansione Codice")
with st.expander("Apri Fotocamera", expanded=False):
    foto = st.camera_input("Inquadra il codice a barre e scatta")
    if foto:
        st.image(foto, caption="Foto scattata")
        st.info("💡 **Trucco Smart:** Tieni premuto sul numero del codice a barre nella foto qui sopra, clicca 'Copia' e incollalo nel campo sotto!")

# --- SEZIONE INSERIMENTO ---
st.divider()
barcode_input = st.text_input("Codice a Barre", placeholder="Incolla o scrivi il codice...")

# Ricerca automatica nel database
prodotto_trovato = df_inventario[df_inventario['Barcode'] == str(barcode_input).strip()]

with st.form("form_aggiunta", clear_on_submit=True):
    # Se il prodotto esiste, pre-compiliamo i campi
    if not prodotto_trovato.empty and barcode_input != "":
        n_def = prodotto_trovato.iloc[0]['Nome Prodotto']
        p_def = float(prodotto_trovato.iloc[0]['Prezzo'])
        st.success(f"Prodotto riconosciuto: **{n_def}**")
    else:
        n_def = ""
        p_def = 0.0
        if barcode_input:
            st.warning("Prodotto non in archivio. Inserisci nome e prezzo per aggiungerlo.")

    nome = st.text_input("Nome Prodotto", value=n_def)
    prezzo = st.number_input("Prezzo (€)", value=p_def, format="%.2f", step=0.01)
    qty = st.number_input("Quantità", min_value=1, value=1, step=1)
    
    submit = st.form_submit_button("➕ AGGIUNGI AL CARRELLO")
    
    if submit:
        if nome != "" and prezzo > 0:
            st.session_state.carrello.append({
                "Nome": nome, 
                "Prezzo": prezzo, 
                "Qty": qty, 
                "Totale": round(prezzo * qty, 2)
            })
            st.toast(f"{nome} aggiunto!")
            st.rerun()
        else:
            st.error("Inserisci un nome e un prezzo validi.")

# --- VISUALIZZAZIONE CARRELLO ---
if st.session_state.carrello:
    st.divider()
    st.subheader("📝 Il tuo Carrello")
    df_c = pd.DataFrame(st.session_state.carrello)
    
    # Tabella pulita
    st.dataframe(df_c[['Nome', 'Qty', 'Totale']], use_container_width=True, hide_index=True)
    
    totale_spesa = df_c['Totale'].sum()
    st.metric(label="TOTALE", value=f"€ {totale_spesa:.2f}")

    # Azioni Scontrino
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 CREA PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, "SCONTRINO VIBE SMART", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            for _, row in df_c.iterrows():
                pdf.cell(140, 10, f"{row['Nome']} x{row['Qty']}", 1)
                pdf.cell(50, 10, f"Euro {row['Totale']:.2f}", 1, ln=True)
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(190, 10, f"TOTALE: Euro {totale_spesa:.2f}", ln=True, align='R')
            
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button("⬇️ Scarica PDF", data=pdf_output, file_name="scontrino.pdf", mime="application/pdf")
            
    with col2:
        if st.button("🗑️ SVUOTA", help="Cancella tutto il carrello"):
            st.session_state.carrello = []
            st.rerun()
