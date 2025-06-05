import streamlit as st
import pandas as pd
import numpy as np
import base64
from io import BytesIO
import os
from datetime import datetime
import json
import openpyxl
from openpyxl.styles import PatternFill

# Configurazione della pagina
st.set_page_config(
    page_title="Visualizzatore BF",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Funzione per convertire colori Excel in formato CSS
def excel_color_to_css(excel_color):
    if excel_color == '00000000' or not excel_color:
        return None
    # Rimuovi il prefisso FF se presente (openpyxl aggiunge FF all'inizio per indicare opacità)
    if excel_color.startswith('FF'):
        excel_color = excel_color[2:]
    # Converti da formato ARGB a RGB
    return f"#{excel_color}"

# Funzione per estrarre i colori delle celle dal file Excel
def extract_cell_colors(file_path):
    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active
    cell_colors = {}
    
    for row in range(1, sheet.max_row + 1):
        for col in range(1, sheet.max_column + 1):
            cell = sheet.cell(row=row, column=col)
            if cell.fill.start_color.index != '00000000':
                cell_colors[f"{row}_{col}"] = excel_color_to_css(cell.fill.start_color.index)
    
    return cell_colors

# Funzione per salvare i dati in sessione
def save_session_data(df, cell_colors):
    session_data = {
        'dataframe': df.to_dict(),
        'cell_colors': cell_colors,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state['data'] = session_data

# Funzione per caricare i dati dalla sessione
def load_session_data():
    if 'data' in st.session_state:
        session_data = st.session_state['data']
        df = pd.DataFrame.from_dict(session_data['dataframe'])
        cell_colors = session_data['cell_colors']
        timestamp = session_data['timestamp']
        return df, cell_colors, timestamp
    return None, None, None

# Funzione per generare CSS per colorare le celle
def generate_cell_style(cell_colors):
    css = """
    <style>
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 0.9em;
        font-family: sans-serif;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
    }
    .styled-table thead tr {
        background-color: #009879;
        color: #ffffff;
        text-align: left;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    .styled-table th,
    .styled-table td {
        padding: 12px 15px;
        border: 1px solid #dddddd;
    }
    .styled-table tbody tr {
        border-bottom: 1px solid #dddddd;
    }
    .styled-table tbody tr:hover {
        background-color: rgba(173, 216, 230, 0.3);
    }
    .styled-table tbody tr.selected {
        background-color: rgba(173, 216, 230, 0.5);
    }
    .dark-mode .styled-table thead tr {
        background-color: #262730;
    }
    .dark-mode .styled-table th,
    .dark-mode .styled-table td {
        border: 1px solid #4e4e4e;
    }
    """
    
    # Aggiungi stili per celle colorate
    for cell_key, color in cell_colors.items():
        row, col = cell_key.split('_')
        css += f"""
        .cell-{cell_key} {{
            background-color: {color} !important;
        }}
        """
    
    css += """
    </style>
    """
    return css

# Funzione per creare HTML della tabella con colori
def create_colored_table_html(df, cell_colors):
    # Genera CSS per le celle colorate
    table_html = f"""
    <div class="table-container" style="overflow-x: auto; overflow-y: auto; max-height: 600px;">
    <table class="styled-table">
        <thead>
            <tr>
    """
    
    # Aggiungi intestazioni
    for col in df.columns:
        table_html += f"<th>{col}</th>"
    
    table_html += """
            </tr>
        </thead>
        <tbody>
    """
    
    # Aggiungi righe
    for row_idx, row in df.iterrows():
        table_html += f'<tr id="row-{row_idx}" onclick="highlightRow({row_idx})">'
        for col_idx, col_name in enumerate(df.columns):
            cell_value = row[col_name]
            cell_key = f"{row_idx + 2}_{col_idx + 1}"  # +2 perché la riga 1 è l'intestazione in Excel
            cell_class = f"cell-{cell_key}" if cell_key in cell_colors else ""
            table_html += f'<td class="{cell_class}">{cell_value}</td>'
        table_html += "</tr>"
    
    table_html += """
        </tbody>
    </table>
    </div>
    <script>
    function highlightRow(rowIdx) {
        // Rimuovi la classe selected da tutte le righe
        var rows = document.querySelectorAll('.styled-table tbody tr');
        rows.forEach(function(row) {
            row.classList.remove('selected');
        });
        
        // Aggiungi la classe selected alla riga cliccata
        var selectedRow = document.getElementById('row-' + rowIdx);
        if (selectedRow) {
            selectedRow.classList.add('selected');
        }
    }
    </script>
    """
    
    return table_html

# Inizializzazione dello stato della sessione
if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = False

# Applica il tema scuro se selezionato
if st.session_state.get('dark_mode', False):
    st.markdown("""
    <style>
    body {
        color: white;
        background-color: #121212;
    }
    .stApp {
        background-color: #121212;
    }
    .dark-mode {
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)
    dark_class = "dark-mode"
else:
    st.markdown("""
    <style>
    .dark-mode {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)
    dark_class = ""

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
        # Salva temporaneamente il file per estrarre i colori
        temp_file_path = os.path.join("/tmp", uploaded_file.name)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        # Leggi il file Excel
        df = pd.read_excel(uploaded_file)
        
        # Estrai i colori delle celle
        cell_colors = extract_cell_colors(temp_file_path)
        
        # Salva i dati in sessione
        save_session_data(df, cell_colors)
        
        st.success(f"File caricato: {uploaded_file.name}")
    
    st.markdown("---")
    
    # Pulsante per cancellare la tabella (posizionato in basso nella sidebar)
    st.markdown("<div style='position: fixed; bottom: 60px; width: 80%;'>", unsafe_allow_html=True)
    if st.button("🗑️ Cancella Tabella", key="clear_table"):
        if 'data' in st.session_state:
            del st.session_state['data']
            st.success("Tabella cancellata")
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Contenuto principale
st.title("Visualizzazione Dati BF")

# Carica i dati dalla sessione se disponibili
df, cell_colors, timestamp = load_session_data()

if df is not None:
    st.info(f"Dati caricati - Ultimo aggiornamento: {timestamp}")
    
    # Aggiungi filtri per colonna
    st.subheader("Filtri")
    col_filters = st.columns(min(4, len(df.columns)))
    
    filtered_df = df.copy()
    filter_applied = False
    
    for i, col_name in enumerate(df.columns):
        filter_col = col_filters[i % 4]
        with filter_col:
            # Crea un filtro appropriato in base al tipo di dati
            if df[col_name].dtype == 'object':  # Per colonne di testo
                unique_values = df[col_name].dropna().unique()
                if len(unique_values) < 20:  # Se ci sono pochi valori unici, usa multiselect
                    selected_values = st.multiselect(
                        f"Filtra {col_name}",
                        options=sorted(unique_values),
                        default=[]
                    )
                    if selected_values:
                        filtered_df = filtered_df[filtered_df[col_name].isin(selected_values)]
                        filter_applied = True
                else:  # Altrimenti usa un campo di testo
                    text_filter = st.text_input(f"Cerca in {col_name}", "")
                    if text_filter:
                        filtered_df = filtered_df[filtered_df[col_name].astype(str).str.contains(text_filter, case=False)]
                        filter_applied = True
            elif np.issubdtype(df[col_name].dtype, np.number):  # Per colonne numeriche
                min_val = float(df[col_name].min())
                max_val = float(df[col_name].max())
                if min_val != max_val:
                    filter_range = st.slider(
                        f"Intervallo {col_name}",
                        min_value=min_val,
                        max_value=max_val,
                        value=(min_val, max_val)
                    )
                    if filter_range != (min_val, max_val):
                        filtered_df = filtered_df[(filtered_df[col_name] >= filter_range[0]) & 
                                                 (filtered_df[col_name] <= filter_range[1])]
                        filter_applied = True
    
    # Mostra informazioni sul filtraggio
    if filter_applied:
        st.success(f"Filtri applicati: visualizzazione di {len(filtered_df)} righe su {len(df)} totali")
    
    # Genera CSS per le celle colorate
    cell_style = generate_cell_style(cell_colors)
    st.markdown(cell_style, unsafe_allow_html=True)
    
    # Crea la tabella HTML con colori
    table_html = create_colored_table_html(filtered_df, cell_colors)
    
    # Aggiungi la classe dark-mode se necessario
    table_html = f'<div class="{dark_class}">{table_html}</div>'
    
    # Visualizza la tabella
    st.markdown(table_html, unsafe_allow_html=True)
    
    # Mostra informazioni sulla tabella
    st.markdown(f"**Righe totali:** {len(filtered_df)}")
else:
    st.info("Carica un file Excel dalla barra laterale per visualizzare i dati.")
    st.markdown("""
    ### Istruzioni:
    1. Utilizza il pulsante "Carica file Excel" nella barra laterale per caricare il tuo file
    2. La tabella verrà visualizzata qui con le formattazioni di colore originali
    3. Puoi filtrare i dati utilizzando i controlli sopra la tabella
    4. Clicca su una riga per evidenziarla
    5. Utilizza il pulsante "Cambia Tema" per passare tra tema chiaro e scuro
    6. I dati rimarranno disponibili anche dopo aver chiuso e riaperto la pagina
    7. Per caricare un nuovo file, usa prima il pulsante "Cancella Tabella"
    """)

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>Visualizzatore BF - Sviluppato con Streamlit</div>", unsafe_allow_html=True)
