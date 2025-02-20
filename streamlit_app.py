import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="📊 Dashboard Consumi Economato",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# GLOBAL SETTINGS
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
DATA_FILE = Path("data/master_dataset.xlsx")

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    """Load and clean the Excel dataset."""
    if not DATA_FILE.exists():
        st.error(f"File not found: {DATA_FILE}")
        return pd.DataFrame()

    try:
        df = pd.read_excel(DATA_FILE, engine="openpyxl")
    except Exception as e:
        st.error(f"Error reading Excel file: {str(e)}")
        return pd.DataFrame()

    # Rename columns
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

    # Convert mese to string and filter out non-numeric months
    if 'mese' in df.columns:
        df['mese'] = df['mese'].astype(str)
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

    # Update layout
    fig.update_layout(
        height=600,
        title_text="Andamento Mensile",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # Metrics
    st.subheader("Metriche Mensili")
    st.dataframe(monthly_metrics)

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
# MAIN APP
# -----------------------------------------------------------------------------
def main():
    # Authentication
    AUTHORIZED_USERNAME = st.secrets["USERNAME"]
    AUTHORIZED_PASSWORD = st.secrets["PASSWORD"]

    def authenticate(username, password):
        if username == AUTHORIZED_USERNAME and password == AUTHORIZED_PASSWORD:
            return True
        return False

    # Show login form only if not authenticated
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("📊 Dashboard Consumi Economato")
        username = st.text_input("Username", key="username")
        password = st.text_input("Password", type="password", key="password")
        if st.button("Login"):
            if authenticate(username, password):
                st.session_state.authenticated = True
            else:
                st.error("Invalid username or password.")
    else:
        # Load data
        df = load_data()

        # Filters
        st.sidebar.header("Filtri")
        selected_reparto = st.sidebar.selectbox("Reparto", ["Tutti"] + sorted(df['reparto'].unique()))
        selected_mese = st.sidebar.selectbox("Mese", ["Tutti"] + sorted(df['mese'].astype(str).unique()))

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

        # Add a logout button
        if st.button("Logout"):
            st.session_state.authenticated = False

if __name__ == "__main__":
    main()