import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒")

URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

try:
    # Qui l'app cercherà automaticamente nei "Secrets" di Streamlit Cloud
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_inventario = conn.read(spreadsheet=URL_FOGLIO, worksheet="0")
    st.success("✅ Database collegato!")
except Exception as e:
    st.error(f"❌ Errore di connessione: {e}")
    df_inventario = pd.DataFrame(columns=['Codice a Barre', 'PUNTO VENDITA', 'Nome Prodotto', 'Prezzo standard'])

st.title("🛒 Vibe Smart Spesa")
# ... resto del codice ...
