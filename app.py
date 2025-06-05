import streamlit as st
import pandas as pd
import os

# Configurazione della pagina
st.set_page_config(
    page_title="Visualizzatore BF",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inizializzazione dello stato della sessione
if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = False

# Sidebar
with st.sidebar:
    st.title("Visualizzatore BF")
    
    # Tema chiaro/scuro
    if st.button("🌓 Cambia Tema"):
        st.session_state['dark_mode'] = not st.session_state['dark_mode']
        st.experimental_rerun()
    
    # Mostra il tema corrente
    current_theme = "Scuro" if st.session_state['dark_mode'] else "Chiaro"
    st.info(f"Tema attuale: {current_theme}")
    
    st.markdown("---")
    
    # Upload del file
    uploaded_file = st.file_uploader("Carica file Excel", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        # Leggi il file Excel
        try:
            df = pd.read_excel(uploaded_file)
            # Salva i dati in sessione
            st.session_state['data'] = df
            st.session_state['filename'] = uploaded_file.name
            st.success(f"File caricato: {uploaded_file.name}")
        except Exception as e:
            st.error(f"Errore nel caricamento del file: {e}")
    
    st.markdown("---")
    
    # Pulsante per cancellare la tabella
    if st.button("🗑️ Cancella Tabella", key="clear_table"):
        if 'data' in st.session_state:
            del st.session_state['data']
            del st.session_state['filename']
            st.success("Tabella cancellata")
            st.experimental_rerun()

# Contenuto principale
st.title("Visualizzazione Dati BF")

# Carica i dati dalla sessione se disponibili
if 'data' in st.session_state:
    df = st.session_state['data']
    filename = st.session_state.get('filename', 'File Excel')
    
    st.info(f"Dati caricati: {filename}")
    
    # Visualizza la tabella
    st.dataframe(df, use_container_width=True, height=600)
    
    # Mostra informazioni sulla tabella
    st.markdown(f"**Righe totali:** {len(df)}")
else:
    st.info("Carica un file Excel dalla barra laterale per visualizzare i dati.")
    st.markdown("""
    ### Istruzioni:
    1. Utilizza il pulsante "Carica file Excel" nella barra laterale per caricare il tuo file
    2. La tabella verrà visualizzata qui
    3. Utilizza il pulsante "Cambia Tema" per passare tra tema chiaro e scuro
    4. I dati rimarranno disponibili anche dopo aver chiuso e riaperto la pagina
    5. Per caricare un nuovo file, usa prima il pulsante "Cancella Tabella"
    """)

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>Visualizzatore BF - Sviluppato con Streamlit</div>", unsafe_allow_html=True)
