import streamlit as st
import pandas as pd
import base64
import os
import pickle
import re

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Visualizzatore Palinsesto BF",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Funzione per salvare i dati in memoria
def save_data(df, file_type="palinsesto"):
    """
    Salva i dati in un file pickle per la persistenza
    """
    # Crea una directory temporanea se non esiste
    if not os.path.exists(".streamlit"):
        os.makedirs(".streamlit")
    
    # Salva il DataFrame
    with open(f".streamlit/data_{file_type}.pkl", "wb") as f:
        pickle.dump({"df": df}, f)

# Funzione per caricare i dati dalla memoria
def load_data(file_type="palinsesto"):
    """
    Carica i dati dal file pickle se esiste
    """
    if os.path.exists(f".streamlit/data_{file_type}.pkl"):
        try:
            with open(f".streamlit/data_{file_type}.pkl", "rb") as f:
                data = pickle.load(f)
            return data["df"]
        except Exception:
            return None
    return None

# Funzione per generare un link di download per un DataFrame
def get_table_download_link(df, filename, text):
    """Genera un link per scaricare il dataframe come file CSV"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 {text}</a>'
    return href

# Funzione per caricare il file Excel
def load_excel_file(uploaded_file, sheet_name=None):
    try:
        # Carica il file Excel direttamente con pandas
        if sheet_name:
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Formatta la colonna ORA se esiste
        if 'ORA' in df.columns:
            df['ORA'] = df['ORA'].astype(str).str.replace(r'(\d{1,2}):(\d{2}):\d{2}', r'\1:\2', regex=True)
        
        # Formatta le colonne numeriche
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            df[col] = df[col].apply(lambda x: str(x).replace('.', ',') if pd.notnull(x) else x)
        
        return df
    except Exception as e:
        st.error(f"Errore durante il caricamento del file: {e}")
        return None

# Funzione per filtrare il DataFrame in base all'ora
def filter_by_time(df, column, min_time, max_time):
    """
    Filtra il DataFrame in base all'intervallo di orari
    """
    try:
        min_time_parts = min_time.split(':')
        max_time_parts = max_time.split(':')
        
        if len(min_time_parts) >= 2 and len(max_time_parts) >= 2:
            min_hour, min_minute = int(min_time_parts[0]), int(min_time_parts[1])
            max_hour, max_minute = int(max_time_parts[0]), int(max_time_parts[1])
            
            min_minutes = min_hour * 60 + min_minute
            max_minutes = max_hour * 60 + max_minute
            
            # Estrai ore e minuti con regex
            time_pattern = r'(\d{1,2}):(\d{2})'
            
            # Funzione per convertire l'ora in minuti totali
            def time_to_minutes(time_str):
                match = re.search(time_pattern, str(time_str))
                if match:
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    return hour * 60 + minute
                return -1  # Valore invalido
            
            # Applica la conversione a tutta la colonna
            time_minutes = df[column].apply(time_to_minutes)
            
            # Filtra in base ai minuti
            return df[(time_minutes >= min_minutes) & (time_minutes <= max_minutes)]
    except Exception:
        pass
    
    return df

# Inizializza lo stato della sessione
if 'palinsesto_loaded' not in st.session_state:
    st.session_state.palinsesto_loaded = False
    st.session_state.palinsesto_df = None

if 'archivio_loaded' not in st.session_state:
    st.session_state.archivio_loaded = False
    st.session_state.archivio_df = None

# Titolo dell'applicazione
st.title("📊 Visualizzatore Palinsesto BF")
st.markdown("""
Questa applicazione permette di visualizzare e filtrare i dati.
I dati caricati rimangono in memoria anche dopo la chiusura del browser.
""")

# Sidebar per le opzioni
st.sidebar.header("Opzioni")

# Selezione del tipo di dati da visualizzare
data_type = st.sidebar.radio(
    "Seleziona il tipo di dati da visualizzare:",
    ["Palinsesto BF", "Giornata Odierna FB"]
)

# Caricamento del file Excel per il palinsesto
if data_type == "Palinsesto BF":
    uploaded_file = st.sidebar.file_uploader("Carica un nuovo file Excel per il Palinsesto", type=["xlsx"], key="palinsesto_uploader")
    
    # Carica i dati esistenti o usa quelli appena caricati
    if uploaded_file is not None:
        # Se viene caricato un nuovo file, sostituisci i dati esistenti
        df = load_excel_file(uploaded_file)
        if df is not None:
            st.session_state.palinsesto_df = df
            st.session_state.palinsesto_loaded = True
            
            # Salva i dati per la persistenza
            save_data(df, "palinsesto")
            
            st.sidebar.success("File caricato con successo")
    elif not st.session_state.palinsesto_loaded:
        # Carica i dati salvati se non ci sono dati nella sessione
        df = load_data("palinsesto")
        if df is not None:
            st.session_state.palinsesto_df = df
            st.session_state.palinsesto_loaded = True
            st.sidebar.info("Dati caricati dal file salvato")
        else:
            st.info("Nessun dato caricato. Carica un file Excel per iniziare.")
    
    # Se ci sono dati da visualizzare
    if st.session_state.palinsesto_loaded and st.session_state.palinsesto_df is not None:
        df = st.session_state.palinsesto_df
        
        # Opzioni di filtro
        st.sidebar.header("Filtri")
        
        # Crea filtri per ogni colonna
        filtered_df = df.copy()
        
        # Seleziona le colonne da filtrare (limita a massimo 5 per migliorare le prestazioni)
        filter_columns = st.sidebar.multiselect(
            "Seleziona le colonne da filtrare (max 5)",
            options=list(df.columns),
            default=list(df.columns)[:min(5, len(df.columns))]
        )
        
        # Limita a massimo 5 colonne per migliorare le prestazioni
        filter_columns = filter_columns[:min(5, len(filter_columns))]
        
        # Crea filtri per le colonne selezionate
        for column in filter_columns:
            # Ottieni i valori unici nella colonna
            unique_values = df[column].dropna().unique()
            
            # Se ci sono troppi valori unici, usa un input di testo invece di un multiselect
            if len(unique_values) > 10:
                filter_type = st.sidebar.radio(
                    f"Tipo di filtro per {column}",
                    ["Testo", "Range"],
                    key=f"filter_type_{column}"
                )
                
                if filter_type == "Testo":
                    filter_value = st.sidebar.text_input(f"Filtra {column} (testo)", key=f"text_{column}")
                    if filter_value:
                        filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(filter_value, case=False)]
                else:  # Range
                    # Gestione speciale per la colonna ORA
                    if column == 'ORA':
                        # Crea un input di testo per l'ora minima e massima
                        min_time = st.sidebar.text_input(f"Ora minima (formato hh:mm)", value="00:00", key=f"min_time_{column}")
                        max_time = st.sidebar.text_input(f"Ora massima (formato hh:mm)", value="23:59", key=f"max_time_{column}")
                        
                        # Filtra in base all'ora
                        if min_time and max_time:
                            filtered_df = filter_by_time(filtered_df, column, min_time, max_time)
                    # Gestione per colonne numeriche
                    elif column in ['ABBINATE', '1 PUNTA', 'ABB 1 PUNTA', '2 PUNTA', 'ABB 2 PUNTA', 'PARI', 'ABB PARI', 'DISPARI', 'ABB DISPARI', 'GOAL', 'ABB GOAL', 'NOGOAL', 'ABB NOGOAL', 'OVER', 'ABB OVER', 'UNDER', 'ABB UNDER', 'GG', 'ABB GG', 'NG', 'ABB NG', '1X', 'ABB 1X', 'X2', 'ABB X2', '12', 'ABB 12', 'CASA', 'ABB CASA', 'FUORI', 'ABB FUORI', 'BANCA', 'ABB 2 BANCA']:
                        # Converti i valori in numerici per il filtro
                        try:
                            numeric_values = pd.to_numeric(df[column].str.replace(',', '.', regex=False), errors='coerce')
                            
                            # Calcola i valori min e max
                            min_val = float(numeric_values.min()) if not pd.isna(numeric_values.min()) else 0
                            max_val = float(numeric_values.max()) if not pd.isna(numeric_values.max()) else 100
                            
                            # Crea un slider per selezionare l'intervallo
                            range_min, range_max = st.sidebar.slider(
                                f"Intervallo per {column}",
                                min_value=min_val,
                                max_value=max_val,
                                value=(min_val, max_val),
                                key=f"range_{column}"
                            )
                            
                            # Filtra le righe in base all'intervallo
                            numeric_filtered_df = pd.to_numeric(filtered_df[column].str.replace(',', '.', regex=False), errors='coerce')
                            filtered_df = filtered_df[
                                (numeric_filtered_df >= range_min) & 
                                (numeric_filtered_df <= range_max)
                            ]
                        except Exception:
                            # Se c'è un errore, usa il filtro di testo
                            filter_value = st.sidebar.text_input(f"Filtra {column} (testo)", key=f"text_fallback_{column}")
                            if filter_value:
                                filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(filter_value, case=False)]
                    else:
                        # Per altri tipi di colonne, usa il filtro di testo
                        filter_value = st.sidebar.text_input(f"Filtra {column} (testo)", key=f"text_fallback_{column}")
                        if filter_value:
                            filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(filter_value, case=False)]
            else:
                # Altrimenti usa un multiselect
                selected_values = st.sidebar.multiselect(
                    f"Filtra {column}",
                    options=sorted(unique_values),
                    default=[],
                    key=f"multiselect_{column}"
                )
                if selected_values:
                    filtered_df = filtered_df[filtered_df[column].isin(selected_values)]
        
        # Pulsante per reimpostare i filtri
        if st.sidebar.button("Reimposta filtri", key="reset_palinsesto"):
            filtered_df = df.copy()
        
        # Opzioni di visualizzazione
        st.header("Dati del Palinsesto")
        
        # Mostra il numero di righe filtrate
        st.write(f"Visualizzazione di {filtered_df.shape[0]} righe su {df.shape[0]} totali")
        
        # Aggiungi un link per scaricare i dati filtrati
        st.markdown(get_table_download_link(filtered_df, "palinsesto_filtrato.csv", "Scarica i dati filtrati come CSV"), unsafe_allow_html=True)
        
        # Visualizza il DataFrame filtrato
        st.dataframe(filtered_df, use_container_width=True)

# Caricamento del file Excel per l'archivio
else:  # data_type == "Giornata Odierna FB"
    uploaded_file = st.sidebar.file_uploader("Carica un nuovo file Excel per la Giornata Odierna", type=["xlsx"], key="archivio_uploader")
    
    # Carica i dati esistenti o usa quelli appena caricati
    if uploaded_file is not None:
        # Se viene caricato un nuovo file, sostituisci i dati esistenti
        df = load_excel_file(uploaded_file, sheet_name="Giornata Odierna")
        if df is not None:
            st.session_state.archivio_df = df
            st.session_state.archivio_loaded = True
            
            # Salva i dati per la persistenza
            save_data(df, "archivio")
            
            st.sidebar.success("File caricato con successo")
    elif not st.session_state.archivio_loaded:
        # Carica i dati salvati se non ci sono dati nella sessione
        df = load_data("archivio")
        if df is not None:
            st.session_state.archivio_df = df
            st.session_state.archivio_loaded = True
            st.sidebar.info("Dati caricati dal file salvato")
        else:
            st.info("Nessun dato caricato. Carica un file Excel per iniziare.")
    
    # Se ci sono dati da visualizzare
    if st.session_state.archivio_loaded and st.session_state.archivio_df is not None:
        df = st.session_state.archivio_df
        
        # Opzioni di filtro
        st.sidebar.header("Filtri")
        
        # Crea filtri per ogni colonna
        filtered_df = df.copy()
        
        # Seleziona le colonne da filtrare (limita a massimo 5 per migliorare le prestazioni)
        filter_columns = st.sidebar.multiselect(
            "Seleziona le colonne da filtrare (max 5)",
            options=list(df.columns),
            default=list(df.columns)[:min(5, len(df.columns))]
        )
        
        # Limita a massimo 5 colonne per migliorare le prestazioni
        filter_columns = filter_columns[:min(5, len(filter_columns))]
        
        # Crea filtri per le colonne selezionate
        for column in filter_columns:
            # Ottieni i valori unici nella colonna
            unique_values = df[column].dropna().unique()
            
            # Se ci sono troppi valori unici, usa un input di testo invece di un multiselect
            if len(unique_values) > 10:
                filter_type = st.sidebar.radio(
                    f"Tipo di filtro per {column}",
                    ["Testo", "Range"],
                    key=f"filter_type_arch_{column}"
                )
                
                if filter_type == "Testo":
                    filter_value = st.sidebar.text_input(f"Filtra {column} (testo)", key=f"text_arch_{column}")
                    if filter_value:
                        filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(filter_value, case=False)]
                else:  # Range
                    # Gestione speciale per la colonna ORA
                    if column == 'ORA':
                        # Crea un input di testo per l'ora minima e massima
                        min_time = st.sidebar.text_input(f"Ora minima (formato hh:mm)", value="00:00", key=f"min_time_arch_{column}")
                        max_time = st.sidebar.text_input(f"Ora massima (formato hh:mm)", value="23:59", key=f"max_time_arch_{column}")
                        
                        # Filtra in base all'ora
                        if min_time and max_time:
                            filtered_df = filter_by_time(filtered_df, column, min_time, max_time)
                    # Gestione per colonne numeriche
                    elif column in df.columns[9:]:  # Colonne da J a BD
                        # Converti i valori in numerici per il filtro
                        try:
                            numeric_values = pd.to_numeric(df[column].str.replace(',', '.', regex=False), errors='coerce')
                            
                            # Calcola i valori min e max
                            min_val = float(numeric_values.min()) if not pd.isna(numeric_values.min()) else 0
                            max_val = float(numeric_values.max()) if not pd.isna(numeric_values.max()) else 100
                            
                            # Crea un slider per selezionare l'intervallo
                            range_min, range_max = st.sidebar.slider(
                                f"Intervallo per {column}",
                                min_value=min_val,
                                max_value=max_val,
                                value=(min_val, max_val),
                                key=f"range_arch_{column}"
                            )
                            
                            # Filtra le righe in base all'intervallo
                            numeric_filtered_df = pd.to_numeric(filtered_df[column].str.replace(',', '.', regex=False), errors='coerce')
                            filtered_df = filtered_df[
                                (numeric_filtered_df >= range_min) & 
                                (numeric_filtered_df <= range_max)
                            ]
                        except Exception:
                            # Se c'è un errore, usa il filtro di testo
                            filter_value = st.sidebar.text_input(f"Filtra {column} (testo)", key=f"text_fallback_arch_{column}")
                            if filter_value:
                                filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(filter_value, case=False)]
                    else:
                        # Per altri tipi di colonne, usa il filtro di testo
                        filter_value = st.sidebar.text_input(f"Filtra {column} (testo)", key=f"text_fallback_arch_{column}")
                        if filter_value:
                            filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(filter_value, case=False)]
            else:
                # Altrimenti usa un multiselect
                selected_values = st.sidebar.multiselect(
                    f"Filtra {column}",
                    options=sorted(unique_values),
                    default=[],
                    key=f"multiselect_arch_{column}"
                )
                if selected_values:
                    filtered_df = filtered_df[filtered_df[column].isin(selected_values)]
        
        # Pulsante per reimpostare i filtri
        if st.sidebar.button("Reimposta filtri", key="reset_archivio"):
            filtered_df = df.copy()
        
        # Opzioni di visualizzazione
        st.header("Dati della Giornata Odierna")
        
        # Mostra il numero di righe filtrate
        st.write(f"Visualizzazione di {filtered_df.shape[0]} righe su {df.shape[0]} totali")
        
        # Aggiungi un link per scaricare i dati filtrati
        st.markdown(get_table_download_link(filtered_df, "giornata_odierna_filtrata.csv", "Scarica i dati filtrati come CSV"), unsafe_allow_html=True)
        
        # Visualizza il DataFrame filtrato
        st.dataframe(filtered_df, use_container_width=True)

