import streamlit as st
import pandas as pd
import numpy as np
import base64
from io import BytesIO
import os
import pickle
import tempfile
import re

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Visualizzatore Palinsesto BF",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Funzione per salvare i dati in memoria
def save_data(df, color_df, file_name):
    """
    Salva i dati in un file pickle per la persistenza
    """
    # Crea una directory temporanea se non esiste
    if not os.path.exists(".streamlit"):
        os.makedirs(".streamlit")
    
    # Salva il DataFrame e il nome del file
    with open(".streamlit/data.pkl", "wb") as f:
        pickle.dump({"df": df, "color_df": color_df, "file_name": file_name}, f)

# Funzione per caricare i dati dalla memoria
def load_data():
    """
    Carica i dati dal file pickle se esiste
    """
    if os.path.exists(".streamlit/data.pkl"):
        try:
            with open(".streamlit/data.pkl", "rb") as f:
                data = pickle.load(f)
            return data["df"], data["color_df"], data["file_name"]
        except Exception as e:
            st.error(f"Errore durante il caricamento dei dati salvati: {e}")
    return None, None, None

# Funzione per generare un link di download per un DataFrame
def get_table_download_link(df, filename, text):
    """Genera un link per scaricare il dataframe come file CSV"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 {text}</a>'
    return href

# Funzione per caricare il file Excel
def load_excel_file(uploaded_file):
    try:
        # Crea un file temporaneo per salvare il file caricato
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        # Leggi il file Excel con openpyxl per preservare i colori delle celle
        import openpyxl
        from openpyxl.utils.dataframe import dataframe_to_rows
        
        wb = openpyxl.load_workbook(tmp_path, data_only=True)
        sheet = wb.active
        
        # Estrai i dati e le informazioni sui colori
        data = []
        colors = []
        
        for row in sheet.iter_rows():
            row_data = []
            row_colors = []
            for cell in row:
                row_data.append(cell.value)
                # Estrai il colore di sfondo della cella
                fill_color = cell.fill.start_color.index
                row_colors.append(fill_color)
            data.append(row_data)
            colors.append(row_colors)
        
        # Crea un DataFrame dai dati
        if data:
            # Usa la prima riga come intestazioni
            headers = data[0]
            df = pd.DataFrame(data[1:], columns=headers)
            
            # Salva le informazioni sui colori nel DataFrame
            color_df = pd.DataFrame(colors[1:], columns=headers)
            
            # Pulisci il file temporaneo
            os.unlink(tmp_path)
            
            return df, color_df
        else:
            st.error("Il file Excel è vuoto")
            os.unlink(tmp_path)
            return None, None
            
    except Exception as e:
        st.error(f"Errore durante il caricamento del file: {e}")
        return None, None

# Funzione per formattare la colonna ORA in formato hh:mm
def format_time_column(df):
    """
    Formatta la colonna ORA in formato hh:mm
    """
    if 'ORA' in df.columns:
        # Crea una copia per evitare SettingWithCopyWarning
        df_copy = df.copy()
        
        # Applica la formattazione a tutte le celle della colonna ORA
        for i in df_copy.index:
            value = df_copy.at[i, 'ORA']
            if pd.notna(value):  # Verifica che il valore non sia NaN
                # Converti il valore in stringa
                value_str = str(value)
                
                # Cerca un pattern di orario nel formato hh:mm:ss
                time_match = re.search(r'(\d{1,2}):(\d{2}):(\d{2})', value_str)
                if time_match:
                    # Estrai ore e minuti
                    hours, minutes = time_match.group(1), time_match.group(2)
                    # Formatta come hh:mm
                    df_copy.at[i, 'ORA'] = f"{hours}:{minutes}"
        
        return df_copy
    return df

# Funzione per formattare i numeri con virgole e un decimale
def format_numeric_columns(df):
    """
    Formatta le colonne numeriche da F a Q con virgole e un decimale
    """
    # Identifica le colonne numeriche da F a Q (indici 5-16)
    numeric_cols = df.columns[5:17] if len(df.columns) >= 17 else df.columns[5:]
    
    # Crea una copia per evitare SettingWithCopyWarning
    df_copy = df.copy()
    
    # Formatta le colonne numeriche
    for col in numeric_cols:
        if col in df.columns:
            # Converti i valori in stringhe con un decimale e virgola
            df_copy[col] = df_copy[col].apply(
                lambda x: str(x).replace('.', ',') if pd.notnull(x) else x
            )
    
    return df_copy

# Funzione per applicare lo stile alle celle colorate
def apply_cell_styling(df, color_df):
    """
    Applica lo stile alle celle del DataFrame per visualizzare i colori
    Ritorna un DataFrame con stile applicato
    """
    # Crea una funzione di stile che applica i colori di sfondo
    def highlight_cells(val, color):
        if color != '00000000' and color != 0:
            # Converti il colore in formato RGB
            # Nota: questa è una semplificazione, in realtà dovremmo convertire l'indice del colore
            # in un valore RGB, ma per semplicità usiamo il verde per tutti i colori non bianchi
            return 'background-color: #90EE90'  # Verde chiaro
        return ''
    
    # Applica lo stile
    styled_df = pd.DataFrame('', index=df.index, columns=df.columns)
    
    for col in df.columns:
        if col in color_df.columns:
            for i in range(len(df)):
                if i < len(color_df) and color_df[col].iloc[i] != '00000000' and color_df[col].iloc[i] != 0:
                    styled_df.loc[i, col] = 'background-color: #90EE90'
    
    return df.style.apply(lambda _: styled_df, axis=None)

# Inizializza lo stato della sessione
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.df = None
    st.session_state.color_df = None
    st.session_state.file_name = None

# Titolo dell'applicazione
st.title("📊 Visualizzatore Palinsesto BF")
st.markdown("""
Questa applicazione permette di visualizzare e filtrare i dati del palinsesto Betfair.
I dati caricati rimangono in memoria anche dopo la chiusura del browser.
""")

# Sidebar per le opzioni
st.sidebar.header("Opzioni")

# Caricamento del file Excel
uploaded_file = st.sidebar.file_uploader("Carica un nuovo file Excel", type=["xlsx"])

# Carica i dati esistenti o usa quelli appena caricati
if uploaded_file is not None:
    # Se viene caricato un nuovo file, sostituisci i dati esistenti
    df, color_df = load_excel_file(uploaded_file)
    if df is not None:
        # Applica le formattazioni richieste
        df = format_time_column(df)
        df = format_numeric_columns(df)
        
        st.session_state.df = df
        st.session_state.color_df = color_df
        st.session_state.file_name = uploaded_file.name
        st.session_state.data_loaded = True
        
        # Salva i dati per la persistenza
        save_data(df, color_df, uploaded_file.name)
        
        st.sidebar.success(f"File caricato con successo: {uploaded_file.name}")
elif not st.session_state.data_loaded:
    # Carica i dati salvati se non ci sono dati nella sessione
    df, color_df, file_name = load_data()
    if df is not None:
        # Applica le formattazioni richieste
        df = format_time_column(df)
        df = format_numeric_columns(df)
        
        st.session_state.df = df
        st.session_state.color_df = color_df
        st.session_state.file_name = file_name
        st.session_state.data_loaded = True
        st.sidebar.info(f"Dati caricati dal file salvato: {file_name}")
    else:
        st.info("Nessun dato caricato. Carica un file Excel per iniziare.")

# Se ci sono dati da visualizzare
if st.session_state.data_loaded and st.session_state.df is not None:
    df = st.session_state.df
    
    # Mostra informazioni sul DataFrame
    st.sidebar.write(f"Numero di righe: {df.shape[0]}")
    st.sidebar.write(f"Numero di colonne: {df.shape[1]}")
    
    # Opzioni di filtro
    st.sidebar.header("Filtri")
    
    # Crea filtri per ogni colonna
    filtered_df = df.copy()
    
    # Raggruppa le colonne in categorie per una migliore organizzazione
    # Mostra solo alcune colonne nel sidebar per non sovraffollarlo
    if len(df.columns) > 10:
        # Seleziona le colonne da mostrare nel sidebar
        filter_columns = st.sidebar.multiselect(
            "Seleziona le colonne da filtrare",
            options=list(df.columns),
            default=list(df.columns)[:5]  # Default: prime 5 colonne
        )
    else:
        filter_columns = list(df.columns)
    
    # Crea filtri per le colonne selezionate
    for column in filter_columns:
        # Ottieni i valori unici nella colonna
        unique_values = df[column].dropna().unique()
        
        # Se ci sono troppi valori unici, usa un input di testo invece di un multiselect
        if len(unique_values) > 10:
            filter_value = st.sidebar.text_input(f"Filtra {column}")
            if filter_value:
                filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(filter_value, case=False)]
        else:
            # Altrimenti usa un multiselect
            selected_values = st.sidebar.multiselect(
                f"Filtra {column}",
                options=sorted(unique_values),
                default=[]
            )
            if selected_values:
                filtered_df = filtered_df[filtered_df[column].isin(selected_values)]
    
    # Pulsante per reimpostare i filtri
    if st.sidebar.button("Reimposta filtri"):
        filtered_df = df.copy()
    
    # Opzioni di visualizzazione
    st.header("Dati del Palinsesto")
    
    # Mostra il nome del file caricato
    st.write(f"File caricato: {st.session_state.file_name}")
    
    # Mostra il numero di righe filtrate
    st.write(f"Visualizzazione di {filtered_df.shape[0]} righe su {df.shape[0]} totali")
    
    # Aggiungi un link per scaricare i dati filtrati
    st.markdown(get_table_download_link(filtered_df, "dati_filtrati.csv", "Scarica i dati filtrati come CSV"), unsafe_allow_html=True)
    
    # Visualizza il DataFrame filtrato con colori
    if st.session_state.color_df is not None:
        st.dataframe(apply_cell_styling(filtered_df, st.session_state.color_df), use_container_width=True)
    else:
        st.dataframe(filtered_df, use_container_width=True)

