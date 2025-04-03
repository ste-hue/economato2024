import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar  # Needed for month names

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
# Use the enhanced, cleaned file
ENHANCED_ARTICLES_FILE = Path("data/processed_csv/enhanced_articles.csv")

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    """Load the cleaned and enhanced CSV dataset."""
    if not ENHANCED_ARTICLES_FILE.exists():
        st.error(f"File not found: {ENHANCED_ARTICLES_FILE}")
        st.error("Please run the data processing scripts first (merge_csv.py, validate_data.py, enhance_flat_data.py).")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(ENHANCED_ARTICLES_FILE)
        
        # Rename columns to match app expectations (lowercase, specific names)
        # Use 'Valore' as the primary cost column
        rename_dict = {
            'Reparto': 'reparto',
            'Classe': 'classe',
            'Categoria': 'categoria',
            'Descrizione': 'descrizione',
            'Quantita': 'quantita',
            'Euro Medio': 'euro_medio',
            'Valore': 'costo', # Map 'Valore' to 'costo'
            'Mese_Nome': 'mese_nome',
            'Data': 'data', # YYYY-MM format
            'Anno': 'anno',
            'Mese': 'mese', # Keep original month number if needed
            'Codice': 'codice',
            'U.M.A.': 'uma',
            'U.M.C.': 'umc',
            'Coeff Conv': 'coeff_conv'
        }
        df.rename(columns=rename_dict, inplace=True, errors='ignore')
        
        # Ensure correct data types
        numeric_cols = ['quantita', 'euro_medio', 'costo', 'coeff_conv']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Convert relevant columns to string/category for filtering
        cat_cols = ['reparto', 'classe', 'categoria', 'mese_nome', 'data', 'anno', 'mese']
        for col in cat_cols:
            if col in df.columns:
                df[col] = df[col].astype(str)
                
        # Handle potential empty strings after conversion if necessary
        for col in ['classe', 'categoria']:
             if col in df.columns:
                 df[col] = df[col].replace('', 'N/A') # Replace empty strings with N/A

        st.sidebar.success("Dati caricati correttamente!")
        return df

    except Exception as e:
        st.error(f"Errore durante il caricamento dei dati da {ENHANCED_ARTICLES_FILE}: {str(e)}")
        return pd.DataFrame()

def create_monthly_analysis(df):
    """Generate monthly bar charts and metrics using 'data' (YYYY-MM) and 'mese_nome'."""
    st.header("📅 Analisi Mensile")

    # Group by YYYY-MM and month name
    monthly_metrics = df.groupby(['data', 'mese_nome']).agg(
        costo_totale=('costo', 'sum'),
        quantita_totale=('quantita', 'sum'),
        prodotti_unici=('descrizione', 'nunique'),
        reparti_attivi=('reparto', 'nunique')
    ).reset_index()
    
    # Sort by date (YYYY-MM)
    monthly_metrics = monthly_metrics.sort_values(by='data')

    # Plotly subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Andamento Costi Mensili', 'Andamento Quantità Mensili'),
        vertical_spacing=0.15 # Increased spacing
    )

    # Bar for Costo
    fig.add_trace(
        go.Bar(
            x=monthly_metrics['mese_nome'], # Use month name for x-axis label
            y=monthly_metrics['costo_totale'],
            name='Costo',
            marker_color='#636EFA',
            text=monthly_metrics['costo_totale'].apply(lambda x: f'€ {x:,.0f}'), # Add text labels
            textposition='auto'
        ),
        row=1, col=1
    )

    # Bar for Quantità
    fig.add_trace(
        go.Bar(
            x=monthly_metrics['mese_nome'], # Use month name for x-axis label
            y=monthly_metrics['quantita_totale'],
            name='Quantità',
            marker_color='#EF553B',
            text=monthly_metrics['quantita_totale'].apply(lambda x: f'{x:,.0f}') # Add text labels
        ),
        row=2, col=1
    )

    # Update layout
    fig.update_layout(
        height=700, # Increased height
        title_text="Andamento Mensile (Costo e Quantità)",
        xaxis_title=None, # Remove x-axis title for first plot
        xaxis2_title="Mese", # Set x-axis title for second plot
        yaxis_title="Costo Totale (€)",
        yaxis2_title="Quantità Totale",
        showlegend=False,
        bargap=0.2 # Add gap between bars
    )
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=45, row=1, col=1)
    fig.update_xaxes(tickangle=45, row=2, col=1)


    st.plotly_chart(fig, use_container_width=True)

    # Metrics Table
    st.subheader("Metriche Mensili Dettagliate")
    display_metrics = monthly_metrics[['mese_nome', 'costo_totale', 'quantita_totale', 'prodotti_unici', 'reparti_attivi']].copy()
    display_metrics.rename(columns={
        'mese_nome': 'Mese',
        'costo_totale': 'Costo Totale (€)',
        'quantita_totale': 'Quantità Totale',
        'prodotti_unici': 'Prodotti Unici',
        'reparti_attivi': 'Reparti Attivi'
    }, inplace=True)
    # Format numbers
    display_metrics['Costo Totale (€)'] = display_metrics['Costo Totale (€)'].apply(lambda x: f'€ {x:,.2f}')
    display_metrics['Quantità Totale'] = display_metrics['Quantità Totale'].apply(lambda x: f'{x:,.0f}')

    st.dataframe(display_metrics.set_index('Mese'), use_container_width=True)

def show_debug_info():
    """Optional debug info in the sidebar."""
    st.sidebar.write("Debug Info:")
    st.sidebar.write(f"Base Directory: {BASE_DIR}")
    st.sidebar.write(f"Enhanced Articles File: {ENHANCED_ARTICLES_FILE}")
    articles_exists = ENHANCED_ARTICLES_FILE.exists()
    st.sidebar.write(f"Enhanced Articles file exists: {articles_exists}")
    if articles_exists:
        st.sidebar.write("Processed CSV directory contents (/data/processed_csv/):")
        try:
            for item in (ENHANCED_ARTICLES_FILE.parent).iterdir():
                st.sidebar.write(f"- {item.name} ({'dir' if item.is_dir() else 'file'})")
        except Exception as e:
            st.sidebar.write(f"Error listing directory: {str(e)}")

# -----------------------------------------------------------------------------
# MAIN APP
# -----------------------------------------------------------------------------
def main():
    # --- Authentication --- (Keep existing logic)
    if not hasattr(st, "secrets"): # Fallback if secrets are not defined
         st.warning("Secrets not found. Skipping authentication.")
         st.session_state.authenticated = True
    elif "authenticated" not in st.session_state:
         st.session_state.authenticated = False

    if not st.session_state.get("authenticated", False):
        st.title("📊 Dashboard Consumi Economato")
        # Check if secrets are loaded
        if not hasattr(st, "secrets") or "USERNAME" not in st.secrets or "PASSWORD" not in st.secrets:
             st.error("Credentials non configurate correttamente nei secrets di Streamlit.")
             st.stop()

        AUTHORIZED_USERNAME = st.secrets["USERNAME"]
        AUTHORIZED_PASSWORD = st.secrets["PASSWORD"]

        def authenticate(username, password):
            return username == AUTHORIZED_USERNAME and password == AUTHORIZED_PASSWORD

        username = st.text_input("Username", key="username")
        password = st.text_input("Password", type="password", key="password")
        if st.button("Login"):
            if authenticate(username, password):
                st.session_state.authenticated = True
                st.rerun() # Rerun to load the main app
            else:
                st.error("Username o password non validi.")
        st.stop() # Stop execution until authenticated

    # --- Main App Logic ---
    st.sidebar.image("https://www.puntaldia.com/wp-content/uploads/2022/04/logo-puntaldia-dark-new.png", width=200)
    st.sidebar.title("Dashboard Consumi")

    # Load data using the updated function
    df = load_data()

    if df.empty:
        st.error("Nessun dato caricato. Verifica che il file CSV esista e che gli script di elaborazione siano stati eseguiti.")
        return

    # --- Filters ---
    st.sidebar.header("Filtri")

    # Year Filter (if data spans multiple years, otherwise just display 2024)
    available_years = sorted(df['anno'].unique())
    if len(available_years) > 1:
        selected_anno = st.sidebar.selectbox("Anno", ["Tutti"] + available_years)
    else:
        selected_anno = available_years[0]
        st.sidebar.info(f"Dati disponibili solo per l'anno: {selected_anno}")

    # Month Filter (using month names)
    # Sort months chronologically using the 'data' column
    month_order = df.sort_values(by='data')['mese_nome'].unique()
    selected_mese = st.sidebar.selectbox("Mese", ["Tutti"] + list(month_order))

    # Department Filter
    selected_reparto = st.sidebar.selectbox("Reparto", ["Tutti"] + sorted(df['reparto'].unique()))

    # Class Filter
    available_classes = ["Tutti"] + sorted(df['classe'].unique())
    selected_classe = st.sidebar.selectbox("Classe", available_classes)

    # Category Filter (dynamic based on selected class)
    if selected_classe != "Tutti":
        available_categories = ["Tutti"] + sorted(df[df['classe'] == selected_classe]['categoria'].unique())
    else:
        available_categories = ["Tutti"] + sorted(df['categoria'].unique())
    selected_categoria = st.sidebar.selectbox("Categoria", available_categories)

    # --- Apply All Filters to the main DataFrame ---
    filtered_df = df.copy()
    # Store initial count before filtering for debugging
    initial_row_count = len(df)
    rows_after_filter = initial_row_count

    if selected_anno != "Tutti":
        filtered_df = filtered_df[filtered_df['anno'] == selected_anno]
        rows_after_filter = len(filtered_df)
    if selected_mese != "Tutti":
        filtered_df = filtered_df[filtered_df['mese_nome'] == selected_mese]
        rows_after_filter = len(filtered_df)
    if selected_reparto != "Tutti":
        filtered_df = filtered_df[filtered_df['reparto'] == selected_reparto]
        rows_after_filter = len(filtered_df)
    if selected_classe != "Tutti":
        filtered_df = filtered_df[filtered_df['classe'] == selected_classe]
        rows_after_filter = len(filtered_df)
    if selected_categoria != "Tutti":
        filtered_df = filtered_df[filtered_df['categoria'] == selected_categoria]
        rows_after_filter = len(filtered_df)

    # --- Specific Debug for BRK/April --- 
    if selected_reparto == 'BRK' and selected_mese == 'April':
        st.sidebar.subheader("Debug BRK - Aprile")
        st.sidebar.write(f"Righe filtrate per BRK/Aprile: {len(filtered_df)}")
        brk_april_cost = filtered_df['costo'].sum()
        st.sidebar.write(f"Somma costo calcolata: € {brk_april_cost:,.2f}")
        st.sidebar.write("Primi 5 record filtrati:")
        st.sidebar.dataframe(filtered_df[['reparto', 'classe', 'categoria', 'codice', 'descrizione', 'costo', 'mese_nome']].head())
    # --- End Specific Debug --- 

    if filtered_df.empty:
        st.warning("Nessun dato corrisponde ai filtri selezionati.")
        # Add debug info even if no data found
        st.info(f"Debug: Selezione - Anno: {selected_anno}, Mese: {selected_mese}, Reparto: {selected_reparto}, Classe: {selected_classe}, Categoria: {selected_categoria}")
        st.info(f"Debug: Righe nel df originale: {initial_row_count}, Righe dopo applicazione filtri: {rows_after_filter}")
        return

    # --- Main Dashboard Area ---
    st.title("📊 Analisi Consumi Economato")

    # Overview metrics
    st.header("📈 Panoramica Generale")
    col1, col2, col3 = st.columns(3)
    total_cost = filtered_df['costo'].sum()
    total_qty = filtered_df['quantita'].sum()
    unique_products = filtered_df['descrizione'].nunique()

    with col1:
        st.metric("Costo Totale Consumi", f"€ {total_cost:,.2f}")
    with col2:
        st.metric("Quantità Totale Articoli", f"{total_qty:,.0f}")
    with col3:
        st.metric("Prodotti Unici Utilizzati", f"{unique_products}")

    st.divider()

    # --- Top Products Analysis ---
    st.header("🥇 Top Prodotti")
    col_cost, col_qty = st.columns(2)

    with col_cost:
        st.subheader("Top 10 per Costo")
        top_cost = (
            filtered_df.groupby(["descrizione", "codice"])["costo"] # Group also by code
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index() # Reset index to access columns
        )
        if not top_cost.empty:
            # Create labels with code and description
            top_cost['label'] = top_cost['codice'] + ' - ' + top_cost['descrizione']
            fig_cost = px.bar(
                top_cost,
                x="costo", # Cost on x-axis
                y="label", # Label on y-axis
                orientation='h', # Horizontal bar chart
                labels={"label": "Prodotto", "costo": "Costo Totale (€)"},
                title="Top 10 Prodotti per Costo Totale",
                color_discrete_sequence=px.colors.qualitative.Pastel,
                text='costo' # Display cost value on bars
            )
            fig_cost.update_traces(texttemplate='€%{text:,.2f}', textposition='outside')
            fig_cost.update_layout(yaxis={'categoryorder':'total ascending'}, # Order bars
                                   margin=dict(l=40, r=40, t=40, b=40),
                                   height=400)
            st.plotly_chart(fig_cost, use_container_width=True)
        else:
            st.info("Nessun prodotto presente per i filtri selezionati.")

    with col_qty:
        st.subheader("Top 10 per Quantità")
        top_qty = (
            filtered_df.groupby(["descrizione", "codice", "umc"])["quantita"] # Group by code and UMC
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index() # Reset index to access columns
        )
        if not top_qty.empty:
             # Create labels with code, description and UMC
            top_qty['label'] = top_qty['codice'] + ' - ' + top_qty['descrizione'] + ' (' + top_qty['umc'] + ')'
            fig_qty = px.bar(
                top_qty,
                x="quantita", # Quantity on x-axis
                y="label", # Label on y-axis
                orientation='h', # Horizontal bar chart
                labels={"label": "Prodotto (Unità di Misura Consumo)", "quantita": "Quantità Totale"},
                title="Top 10 Prodotti per Quantità Totale",
                color_discrete_sequence=px.colors.qualitative.Pastel1,
                text='quantita' # Display quantity value on bars
            )
            fig_qty.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_qty.update_layout(yaxis={'categoryorder':'total ascending'}, # Order bars
                                  margin=dict(l=40, r=40, t=40, b=40),
                                  height=400)
            st.plotly_chart(fig_qty, use_container_width=True)
        else:
            st.info("Nessun prodotto presente per i filtri selezionati.")

    st.divider()

    # --- Hierarchical Analysis ---
    st.header("🏢 Analisi Gerarchica (Reparto > Classe > Categoria)")
    col_rep, col_cla, col_cat = st.columns(3)

    with col_rep:
         st.subheader("Costo per Reparto")
         dept_cost = filtered_df.groupby('reparto')['costo'].sum().reset_index()
         dept_cost = dept_cost.sort_values('costo', ascending=False)
         if not dept_cost.empty:
             fig_dept_pie = px.pie(dept_cost, names='reparto', values='costo',
                                   title="Distribuzione Costi per Reparto", hole=0.3)
             fig_dept_pie.update_traces(textposition='inside', textinfo='percent+label')
             st.plotly_chart(fig_dept_pie, use_container_width=True)
         else:
             st.info("Nessun dato reparto.")

    with col_cla:
        st.subheader("Costo per Classe")
        class_cost = filtered_df.groupby('classe')['costo'].sum().reset_index()
        class_cost = class_cost.sort_values('costo', ascending=False)
        if not class_cost.empty:
             fig_class_pie = px.pie(class_cost.head(10), names='classe', values='costo', # Show top 10
                                   title="Distribuzione Costi per Classe (Top 10)", hole=0.3)
             fig_class_pie.update_traces(textposition='inside', textinfo='percent+label')
             st.plotly_chart(fig_class_pie, use_container_width=True)
        else:
             st.info("Nessun dato classe.")

    with col_cat:
        st.subheader("Costo per Categoria")
        cat_cost = filtered_df.groupby('categoria')['costo'].sum().reset_index()
        cat_cost = cat_cost.sort_values('costo', ascending=False)
        if not cat_cost.empty:
             fig_cat_pie = px.pie(cat_cost.head(10), names='categoria', values='costo', # Show top 10
                                  title="Distribuzione Costi per Categoria (Top 10)", hole=0.3)
             fig_cat_pie.update_traces(textposition='inside', textinfo='percent+label')
             st.plotly_chart(fig_cat_pie, use_container_width=True)
        else:
             st.info("Nessun dato categoria.")


    # --- Monthly Analysis ---
    st.divider()
    create_monthly_analysis(filtered_df)

    # --- Detailed Data Table ---
    st.divider()
    st.header("📦 Dati Dettagliati Filtrati")
    # Select and order columns for display
    show_columns = [
        'reparto', 'classe', 'categoria', 'codice', 'descrizione',
        'quantita', 'umc', 'euro_medio', 'costo', 'mese_nome', 'data'
    ]
    valid_display_cols = [col for col in show_columns if col in filtered_df.columns]
    st.dataframe(filtered_df[valid_display_cols], use_container_width=True)

    # CSV download
    try:
        csv_data = filtered_df[valid_display_cols].to_csv(index=False, decimal=',', sep=';').encode('utf-8-sig') # Use semicolon for Excel Italy
        st.download_button(
            label="📥 Scarica Dati Filtrati (CSV per Excel)",
            data=csv_data,
            file_name=f"consumi_{selected_anno}_{selected_mese}_{selected_reparto}.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Errore durante la preparazione del file CSV: {e}")


    # --- Footer & Debug ---
    st.sidebar.markdown("---")
    # Add a logout button
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    st.sidebar.markdown("---")
    with st.sidebar.expander("🛠️ Debug Info", expanded=False):
        show_debug_info()
        st.write("### Colonne DataFrame Caricato:")
        st.write(df.columns.tolist())
        st.write("### Tipi Dati DataFrame Caricato:")
        st.write(df.dtypes)
        st.write("### Dati Filtrati (Primi 5):")
        st.write(filtered_df.head())


if __name__ == "__main__":
    main()