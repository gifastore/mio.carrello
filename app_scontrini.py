import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒", layout="centered")

# URL del tuo foglio
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

# --- CONNESSIONE ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_inventario = conn.read(spreadsheet=URL_FOGLIO, worksheet="Foglio1", ttl=0)
    df_inventario.columns = df_inventario.columns.str.strip()
    # Pulizia codici a barre per confronto sicuro
    df_inventario['Codice a Barre'] = df_inventario['Codice a Barre'].astype(str).str.strip()
except Exception as e:
    st.error(f"Errore connessione: {e}")
    df_inventario = pd.DataFrame(columns=['Codice a Barre', 'PUNTO VENDITA', 'Nome Prodotto', 'Prezzo standard'])

st.title("🛒 Vibe Smart Spesa")

if 'carrello' not in st.session_state:
    st.session_state.carrello = []

# --- AREA DI SCANSIONE ---
st.subheader("📡 Scansione Prodotto")
barcode = st.text_input("Inquadra o digita il codice a barre", placeholder="Es. 800123456789...", key="barcode_input")

if barcode:
    barcode_clean = str(barcode).strip()
    # Cerca il prodotto
    risultato = df_inventario[df_inventario['Codice a Barre'] == barcode_clean]

    with st.expander("📝 Dettagli Prodotto", expanded=True):
        if not risultato.empty:
            item = risultato.iloc[-1]
            st.success(f"Prodotto riconosciuto!")
            
            # Mostra i dettagli correnti
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome Prodotto", value=item['Nome Prodotto'])
                negozio = st.text_input("Negozio/Punto Vendita", value=item['PUNTO VENDITA'])
            with col2:
                prezzo = st.number_input("Prezzo (€)", value=float(item['Prezzo standard']), step=0.01, format="%.2f")
                qty = st.number_input("Quantità da acquistare", min_value=1, value=1)
            
            if st.button("➕ AGGIUNGI AL CARRELLO", use_container_width=True):
                st.session_state.carrello.append({
                    "Prodotto": nome,
                    "Negozio": negozio,
                    "Prezzo Unit.": prezzo,
                    "Quantità": qty,
                    "Subtotale": prezzo * qty
                })
                st.toast(f"Aggiunto: {nome}")
        
        else:
            st.warning("⚠️ Prodotto non in database! Inserisci i dati per memorizzarlo:")
            col1, col2 = st.columns(2)
            with col1:
                nuovo_nome = st.text_input("Nome Prodotto")
                nuovo_negozio = st.text_input("Negozio")
            with col2:
                nuovo_prezzo = st.number_input("Prezzo (€)", min_value=0.0, step=0.01, format="%.2f")
                nuova_qty = st.number_input("Quantità", min_value=1, value=1)
            
            if st.button("💾 SALVA E AGGIUNGI", use_container_width=True):
                # Qui aggiungi la riga al foglio Google
                nuova_riga = pd.DataFrame([[barcode_clean, nuovo_negozio, nuovo_nome, nuovo_prezzo]], 
                                         columns=['Codice a Barre', 'PUNTO VENDITA', 'Nome Prodotto', 'Prezzo standard'])
                df_aggiornato = pd.concat([df_inventario, nuova_riga], ignore_index=True)
                conn.update(spreadsheet=URL_FOGLIO, data=df_aggiornato)
                
                # Aggiungi al carrello sessione
                st.session_state.carrello.append({
                    "Prodotto": nuovo_nome,
                    "Negozio": nuovo_negozio,
                    "Prezzo Unit.": nuovo_prezzo,
                    "Quantità": nuova_qty,
                    "Subtotale": nuovo_prezzo * nuova_qty
                })
                st.success("Dati salvati nel foglio Google!")
                st.rerun()

# --- VISUALIZZAZIONE CARRELLO ---
if st.session_state.carrello:
    st.divider()
    st.subheader("📋 Il tuo Carrello")
    df_c = pd.DataFrame(st.session_state.carrello)
    
    # Mostriamo la tabella con i dettagli richiesti
    st.dataframe(df_c, use_container_width=True, hide_index=True)
    
    totale = df_c['Subtotale'].sum()
    st.metric(label="TOTALE SPESA", value=f"€ {totale:.2f}")
    
    if st.button("🗑️ Svuota Carrello"):
        st.session_state.carrello = []
        st.rerun()
