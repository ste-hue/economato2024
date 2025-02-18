import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# PAGE CONFIG - Must be the first Streamlit command
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="📊 Dashboard Consumi Economato",
    page_icon="📊",
    layout="wide"
)

# -----------------------------------------------------------------------------
# GLOBAL SETTINGS
# -----------------------------------------------------------------------------

# Directory of this script: e.g. /Users/.../economato/app
BASE_DIR = Path(__file__).parent

# Excel file path: /Users/stefanodellapietra/Desktop/Projects/Development/economato/app/data/master_dataset.xlsx
DATA_FILE = Path("data/master_dataset.xlsx")# app/data/master_dataset.xl

def show_debug_info():
    """Optional debug info in the sidebar."""
    st.sidebar.write("Debug Info:")
    st.sidebar.write(f"Base Directory: {BASE_DIR}")
    st.sidebar.write(f"Data File: {DATA_FILE}")
    file_exists = DATA_FILE.exists()
    st.sidebar.write(f"File exists: {file_exists}")
    if file_exists:
        st.sidebar.write(f"Is file: {DATA_FILE.is_file()}")
        st.sidebar.write("Directory contents in /data/:")
        try:
            for item in (DATA_FILE.parent).iterdir():
                st.sidebar.write("- ", item.name)
        except Exception as e:
            st.sidebar.write(f"Error listing directory: {str(e)}")

# -----------------------------------------------------------------------------
# LOAD DATA
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    """Load and clean the Excel dataset."""
    # Check if the file is actually there
    if not DATA_FILE.exists():
        st.error(f"File not found: {DATA_FILE}")
        return pd.DataFrame()

    try:
        df = pd.read_excel(DATA_FILE, engine="openpyxl")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return pd.DataFrame()

    # Rename columns if they exist
    rename_dict = {
        'Dipartimento': 'reparto',
        'Descrizione': 'descrizione',
        'Quantita': 'quantita',
        'Euro_Medio': 'euro_medio',
        'Mese': 'mese',
        'Anno': 'anno',
        'Costo_Totale': 'costo'
    }
    df.rename(columns=rename_dict, inplace=True, errors='ignore')

    # Convert mese to string to handle 'Evento' or other text
    if 'mese' in df.columns:
        df['mese'] = df['mese'].astype(str)
        # Filter out rows that aren't numeric months
        df = df[df['mese'].str.isnumeric()]
        df['mese'] = df['mese'].astype(int)

    # Convert numeric fields
    numeric_cols = ['quantita', 'euro_medio', 'costo']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Clean text columns
    text_cols = ['reparto', 'descrizione']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna('N/A').str.strip()

    return df

# -----------------------------------------------------------------------------
# MONTHLY ANALYSIS
# -----------------------------------------------------------------------------
def create_monthly_analysis(df):
    """Generate monthly bar charts and metrics."""
    st.header("📅 Analisi Mensile")
    
    mesi_italiani = {
        1: 'Gennaio', 2: 'Febbraio', 3: 'Marzo', 4: 'Aprile',
        5: 'Maggio', 6: 'Giugno', 7: 'Luglio', 8: 'Agosto',
        9: 'Settembre', 10: 'Ottobre', 11: 'Novembre', 12: 'Dicembre'
    }
    
    monthly_metrics = df.groupby('mese').agg({
        'costo': 'sum',
        'quantita': 'sum',
        'descrizione': 'nunique',
        'reparto': 'nunique'
    }).reset_index()
    
    monthly_metrics.columns = [
        'Mese', 'Costo Totale', 'Quantità',
        'Prodotti Unici', 'Reparti Attivi'
    ]
    monthly_metrics['Mese'] = monthly_metrics['Mese'].map(mesi_italiani)
    
    # Plotly subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Andamento Costi Mensili', 'Andamento Quantità Mensili'),
        vertical_spacing=0.12
    )
    
    # Bar for Costo
    fig.add_trace(
        go.Bar(
            x=monthly_metrics['Mese'],
            y=monthly_metrics['Costo Totale'],
            name='Costo',
            marker_color='#636EFA'
        ),
        row=1, col=1
    )
    
    # Bar for Quantità
    fig.add_trace(
        go.Bar(
            x=monthly_metrics['Mese'],
            y=monthly_metrics['Quantità'],
            name='Quantità',
            marker_color='#EF553B'
        ),
        row=2, col=1
    )
    
    fig.update_layout(height=800, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Media Costi Mensili",
            f"€ {monthly_metrics['Costo Totale'].mean():,.2f}"
        )
    with col2:
        st.metric(
            "Media Prodotti Unici",
            f"{monthly_metrics['Prodotti Unici'].mean():,.0f}"
        )
    with col3:
        st.metric(
            "Media Quantità",
            f"{monthly_metrics['Quantità'].mean():,.0f}"
        )
    with col4:
        st.metric(
            "Media Reparti Attivi",
            f"{monthly_metrics['Reparti Attivi'].mean():,.0f}"
        )
    
    # Monthly details table
    st.subheader("Dettaglio Mensile")
    monthly_metrics['Costo Totale'] = monthly_metrics['Costo Totale'].apply(lambda x: f"€ {x:,.2f}")
    monthly_metrics['Quantità'] = monthly_metrics['Quantità'].apply(lambda x: f"{x:,.0f}")
    st.dataframe(monthly_metrics, use_container_width=True)
    
    # Top products per selected month
    st.subheader("Top Prodotti per Mese")
    selected_month = st.selectbox(
        "Seleziona Mese",
        options=monthly_metrics['Mese'].tolist()
    )
    # Reverse mapping
    month_num = {v: k for k, v in mesi_italiani.items()}[selected_month]
    month_data = df[df['mese'] == month_num]
    
    top_products = month_data.groupby('descrizione').agg({
        'costo': 'sum',
        'quantita': 'sum'
    }).sort_values('costo', ascending=False).head(5)
    
    fig_products = px.bar(
        top_products,
        y=top_products.index,
        x='costo',
        orientation='h',
        title=f"Top 5 Prodotti - {selected_month}",
        labels={'descrizione': 'Prodotto', 'costo': 'Costo Totale (€)'}
    )
    st.plotly_chart(fig_products, use_container_width=True)

# -----------------------------------------------------------------------------
# MAIN APP
# -----------------------------------------------------------------------------
def main():
    st.title("📊 Dashboard Consumi Economato")
    st.markdown(
        "Questa dashboard fornisce una **visione d'insieme** dei consumi "
        "unificati, con la possibilità di filtrare, analizzare e scaricare i dati."
    )

    # Load data
    df = load_data()
    if df.empty:
        st.warning("Nessun dato disponibile nel file master_dataset.xlsx.")
        return

    # Sidebar filters
    st.sidebar.header("🔎 Filtri")
    
    if 'reparto' in df.columns:
        reparti = ["Tutti"] + sorted(df['reparto'].dropna().unique().tolist())
        selected_reparto = st.sidebar.selectbox("Seleziona Reparto", reparti)
    else:
        selected_reparto = "Tutti"

    if 'mese' in df.columns:
        mesi = ["Tutti"] + sorted(df['mese'].dropna().astype(str).unique().tolist())
        selected_mese = st.sidebar.selectbox("Seleziona Mese", mesi)
    else:
        selected_mese = "Tutti"

    # Apply filters
    filtered_df = df.copy()
    if selected_reparto != "Tutti":
        filtered_df = filtered_df[filtered_df['reparto'] == selected_reparto]
    if selected_mese != "Tutti":
        filtered_df = filtered_df[filtered_df['mese'].astype(str) == selected_mese]

    if filtered_df.empty:
        st.warning("Nessun dato corrisponde ai filtri selezionati.")
        return

    # Overview metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        total_cost = filtered_df['costo'].sum()
        st.metric("Costo Totale", f"€ {total_cost:,.2f}")
    with col2:
        total_qty = filtered_df['quantita'].sum()
        st.metric("Quantità Totale", f"{total_qty:,.0f}")
    with col3:
        avg_cost = total_cost / total_qty if total_qty > 0 else 0
        st.metric("Costo Medio", f"€ {avg_cost:,.2f}")

    st.divider()

    # Top 10 cost
    st.subheader("Top 10 Prodotti per Costo")
    top_cost = (
        filtered_df.groupby("descrizione")["costo"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    if not top_cost.empty:
        fig_cost = px.bar(
            top_cost,
            x=top_cost.index,
            y=top_cost.values,
            labels={"x": "Prodotto", "y": "Costo Totale (€)"},
            title="Prodotti con Costo Totale più elevato",
            color_discrete_sequence=["#636EFA"],
        )
        fig_cost.update_layout(margin=dict(l=40, r=40, t=40, b=40))
        st.plotly_chart(fig_cost, use_container_width=True)
    else:
        st.info("Nessun prodotto presente per il filtro selezionato.")

    # Top 10 quantity
    st.subheader("Top 10 Prodotti per Quantità")
    top_qty = (
        filtered_df.groupby("descrizione")["quantita"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    if not top_qty.empty:
        fig_qty = px.bar(
            top_qty,
            x=top_qty.index,
            y=top_qty.values,
            labels={"x": "Prodotto", "y": "Quantità Totale"},
            title="Prodotti con Quantità Totale più elevata",
            color_discrete_sequence=["#EF553B"],
        )
        fig_qty.update_layout(margin=dict(l=40, r=40, t=40, b=40))
        st.plotly_chart(fig_qty, use_container_width=True)
    else:
        st.info("Nessun prodotto presente per il filtro selezionato.")

    st.divider()

    # Reparto analysis
    if not filtered_df.empty:
        st.subheader("Analisi per Reparto")
        dept_metrics = filtered_df.groupby('reparto').agg({
            'costo': 'sum',
            'quantita': 'sum',
            'descrizione': 'nunique'
        }).reset_index()
        
        dept_metrics.columns = [
            'Reparto', 'Costo Totale',
            'Quantità Totale', 'Prodotti Unici'
        ]
        dept_metrics['Costo Totale'] = dept_metrics['Costo Totale'].apply(lambda x: f"€ {x:,.2f}")
        dept_metrics['Quantità Totale'] = dept_metrics['Quantità Totale'].apply(lambda x: f"{x:,.0f}")
        
        st.dataframe(dept_metrics, use_container_width=True)

        # Bar chart cost by Reparto
        fig_dept = px.bar(
            filtered_df.groupby('reparto')['costo'].sum().reset_index(),
            x='reparto',
            y='costo',
            title="Confronto Costi per Reparto",
            labels={'reparto': 'Reparto', 'costo': 'Costo Totale (€)'}
        )
        st.plotly_chart(fig_dept, use_container_width=True)

    # Monthly analysis
    if not filtered_df.empty:
        st.divider()
        create_monthly_analysis(filtered_df)

    # Final dataframe
    st.subheader("Dati Filtrati")
    show_columns = ["reparto", "descrizione", "quantita", "euro_medio", "costo", "mese"]
    valid_cols = [col for col in show_columns if col in filtered_df.columns]
    st.dataframe(filtered_df[valid_cols], use_container_width=True)

    # CSV download
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Scarica Dati (CSV)",
        data=csv_data,
        file_name="consumi_filtrati.csv",
        mime="text/csv"
    )

    # Debug in sidebar
    st.sidebar.markdown("<br>" * 10, unsafe_allow_html=True)
    with st.sidebar.expander("🛠️ Debug", expanded=False):
        if st.checkbox("Mostra informazioni di debug", False):
            show_debug_info()

if __name__ == "__main__":
    main()