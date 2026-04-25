import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒", layout="centered")

st.title("🛒 Vibe Smart Spesa")

URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

# --- CONNESSIONE ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_inventario = conn.read(spreadsheet=URL_FOGLIO, worksheet="Foglio1", ttl=0)
    df_inventario.columns = df_inventario.columns.str.strip()
    df_inventario['Codice a Barre'] = df_inventario['Codice a Barre'].astype(str).str.strip()
    st.success("✅ Database Sincronizzato")
except Exception as e:
    st.error(f"Errore connessione: {e}")
    df_inventario = pd.DataFrame(columns=['Codice a Barre', 'PUNTO VENDITA', 'Nome Prodotto', 'Prezzo standard'])

if 'carrello' not in st.session_state:
    st.session_state.carrello = []

# --- AREA DI SCANSIONE ---
st.subheader("📡 Inserimento Prodotto")
barcode = st.text_input("Digita o scansiona il codice a barre", key="barcode_input")

if barcode:
    barcode_clean = str(barcode).strip()
    risultato = df_inventario[df_inventario['Codice a Barre'] == barcode_clean]

    if not risultato.empty:
        # --- PRODOTTO TROVATO ---
        item = risultato.iloc[-1]
        with st.container(border=True):
            st.markdown(f"### 📦 {item['Nome Prodotto']}")
            col1, col2, col3 = st.columns(3)
            with col1: st.write(f"🏪 **Negozio**\n{item['PUNTO VENDITA']}")
            with col2: st.write(f"💰 **Prezzo**\n€ {item['Prezzo standard']}")
            with col3: qta = st.number_input("Quantità", min_value=1, value=1)
            
            if st.button("➕ AGGIUNGI AL CARRELLO", use_container_width=True, type="primary"):
                st.session_state.carrello.append({
                    "Prodotto": item['Nome Prodotto'],
                    "Negozio": item['PUNTO VENDITA'],
                    "Prezzo": float(item['Prezzo standard']),
                    "Q.tà": qta,
                    "Totale": float(item['Prezzo standard']) * qta
                })
                st.toast("Aggiunto!")
    else:
        # --- PRODOTTO NUOVO (QULLO CHE TI SERVE ORA) ---
        st.warning(f"⚠️ Il codice {barcode_clean} è nuovo!")
        with st.expander("📝 REGISTRA NUOVO PRODOTTO", expanded=True):
            n_nome = st.text_input("Nome Prodotto (es. Acqua)")
            n_negozio = st.text_input("Negozio (es. Conad)")
            n_prezzo = st.number_input("Prezzo (€)", min_value=0.0, step=0.01)
            n_qta = st.number_input("Quantità da comprare ora", min_value=1, value=1)
            
            if st.button("💾 SALVA E AGGIUNGI AL CARRELLO", use_container_width=True):
                # Aggiunta al carrello
                st.session_state.carrello.append({
                    "Prodotto": n_nome, "Negozio": n_negozio, 
                    "Prezzo": n_prezzo, "Q.tà": n_qta, "Totale": n_prezzo * n_qta
                })
                # Qui servirebbe una funzione di scrittura per salvare sul foglio, 
                # ma per ora l'aggiunta al carrello funzionerà!
                st.success(f"{n_nome} aggiunto alla spesa!")
                st.rerun()

# --- TABELLA CARRELLO ---
if st.session_state.carrello:
    st.divider()
    st.subheader("📋 Carrello Attuale")
    df_c = pd.DataFrame(st.session_state.carrello)
    st.table(df_c) # Visualizzazione semplice e chiara
    st.metric("TOTALE", f"€ {df_c['Totale'].sum():.2f}")
    if st.button("🗑️ Svuota"):
        st.session_state.carrello = []
        st.rerun()
