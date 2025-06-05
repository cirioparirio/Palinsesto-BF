import streamlit as st
import pandas as pd
import numpy as np
import base64
from io import BytesIO
import os
from datetime import datetime
import json
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
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
    """
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

# Funzione per creare la tabella AgGrid con colori
def create_colored_table(df, cell_colors):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(
        resizable=True, 
        filterable=True, 
        sortable=True, 
        editable=False
    )
    
    # Aggiungi la funzionalità di evidenziazione della riga al click
    gb.configure_grid_options(
        rowSelection='single',
        domLayout='normal',
        enableRangeSelection=True,
        suppressRowClickSelection=False,
        suppressCellSelection=False,
        onRowClicked=JsCode("""
        function(e) {
            // Evidenzia la riga cliccata
            const allRows = document.querySelectorAll('.ag-row');
            allRows.forEach(row => row.classList.remove('selected-row'));
            e.node.setSelected(true);
            const rowElement = document.querySelector('.ag-row-selected');
            if (rowElement) {
                rowElement.classList.add('selected-row');
            }
        }
        """)
    )
    
    # Configura le opzioni per bloccare l'intestazione
    gb.configure_grid_options(
        headerHeight=50,
        suppressMovableColumns=True,
    )
    
    # Applica i colori alle celle
    for col_idx, col_name in enumerate(df.columns):
        for row_idx in range(len(df)):
            cell_key = f"{row_idx + 2}_{col_idx + 1}"  # +2 perché la riga 1 è l'intestazione in Excel
            if cell_key in cell_colors:
                gb.configure_column(
                    col_name,
                    cellStyle=JsCode(f"""
                    function(params) {{
                        if (params.rowIndex === {row_idx}) {{
                            return {{ backgroundColor: '{cell_colors[cell_key]}' }};
                        }}
                        return null;
                    }}
                    """)
                )
    
    grid_options = gb.build()
    
    # Aggiungi CSS personalizzato per l'evidenziazione della riga
    st.markdown("""
    <style>
    .selected-row {
        background-color: rgba(173, 216, 230, 0.5) !important;
    }
    .ag-header-row {
        position: sticky;
        top: 0;
        z-index: 100;
        background-color: white;
    }
    .dark .ag-header-row {
        background-color: #262730;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Crea la tabella AgGrid
    return AgGrid(
        df,
        gridOptions=grid_options,
        height=600,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True,
        theme='streamlit' if not st.session_state.get('dark_mode', False) else 'dark',
        custom_css={
            ".ag-row-hover": {"background-color": "rgba(173, 216, 230, 0.3) !important"},
            ".ag-header-cell-label": {"font-weight": "bold"},
        }
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

# Applica il tema scuro se selezionato
if st.session_state['dark_mode']:
    st.markdown("""
    <style>
    body {
        color: white;
        background-color: #121212;
    }
    .stApp {
        background-color: #121212;
    }
    .st-bw {
        background-color: #262730;
    }
    .st-bb {
        border-color: #4e4e4e;
    }
    .st-bh {
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# Contenuto principale
st.title("Visualizzazione Dati BF")

# Carica i dati dalla sessione se disponibili
df, cell_colors, timestamp = load_session_data()

if df is not None:
    st.info(f"Dati caricati - Ultimo aggiornamento: {timestamp}")
    
    # Crea la tabella colorata
    grid_response = create_colored_table(df, cell_colors)
    
    # Mostra informazioni sulla tabella
    st.markdown(f"**Righe totali:** {len(df)}")
else:
    st.info("Carica un file Excel dalla barra laterale per visualizzare i dati.")
    st.markdown("""
    ### Istruzioni:
    1. Utilizza il pulsante "Carica file Excel" nella barra laterale per caricare il tuo file
    2. La tabella verrà visualizzata qui con le formattazioni di colore originali
    3. Puoi filtrare i dati cliccando sulle intestazioni delle colonne
    4. Clicca su una cella per evidenziare l'intera riga
    5. Utilizza il pulsante "Cambia Tema" per passare tra tema chiaro e scuro
    6. I dati rimarranno disponibili anche dopo aver chiuso e riaperto la pagina
    7. Per caricare un nuovo file, usa prima il pulsante "Cancella Tabella"
    """)

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>Visualizzatore BF - Sviluppato con Streamlit</div>", unsafe_allow_html=True)
