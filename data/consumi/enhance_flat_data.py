import pandas as pd
import os
import calendar

def enhance_flat_data():
    """
    Enhance the flat article data with month names and additional statistics.
    """
    # Check if the file exists
    flat_file = 'data/processed_csv/flat_articles.csv'
    if not os.path.exists(flat_file):
        print(f"File {flat_file} not found. Run validate_data.py first.")
        return
    
    # Load the flat article data
    print("Loading flat article data...")
    df = pd.read_csv(flat_file)
    
    # Ensure values are numeric
    df['Valore'] = pd.to_numeric(df['Valore'], errors='coerce')
    df['Quantita'] = pd.to_numeric(df['Quantita'], errors='coerce')
    
    # Add month name based on month number
    def get_month_name(month_str):
        try:
            # Try to convert to integer (04 → 4)
            month_num = int(month_str)
            return calendar.month_name[month_num]
        except (ValueError, TypeError):
            return month_str
    
    df['Mese_Nome'] = df['Mese'].apply(get_month_name)
    
    # Create Date column in YYYY-MM format for time series
    # Ensure both values are strings before concatenation
    df['Anno'] = df['Anno'].astype(str)
    df['Mese'] = df['Mese'].astype(str).str.zfill(2)
    df['Data'] = df['Anno'] + '-' + df['Mese']
    
    # Save enhanced flat data
    enhanced_file = 'data/processed_csv/enhanced_articles.csv'
    df.to_csv(enhanced_file, index=False)
    print(f"Enhanced data saved to {enhanced_file}")
    
    # Generate summary statistics
    print("\nGenerating summary statistics...")
    
    # Total by month
    monthly_total = df.groupby(['Data', 'Mese_Nome'])['Valore'].sum().reset_index()
    monthly_total = monthly_total.sort_values(by='Data')
    monthly_total.to_csv('data/processed_csv/monthly_totals.csv', index=False)
    print(f"Monthly totals saved to data/processed_csv/monthly_totals.csv")
    
    # Top 20 most expensive products
    top_products = df.groupby(['Codice', 'Descrizione'])['Valore'].sum().reset_index()
    top_products = top_products.sort_values(by='Valore', ascending=False).head(20)
    top_products.to_csv('data/processed_csv/top_products.csv', index=False)
    print(f"Top products saved to data/processed_csv/top_products.csv")
    
    # Department breakdown by month
    dept_by_month = df.groupby(['Data', 'Mese_Nome', 'Reparto'])['Valore'].sum().reset_index()
    dept_by_month = dept_by_month.sort_values(by=['Data', 'Valore'], ascending=[True, False])
    dept_by_month.to_csv('data/processed_csv/dept_by_month.csv', index=False)
    print(f"Department by month saved to data/processed_csv/dept_by_month.csv")
    
    # Class breakdown overall
    class_breakdown = df.groupby(['Reparto', 'Classe'])['Valore'].sum().reset_index()
    class_breakdown = class_breakdown.sort_values(by=['Reparto', 'Valore'], ascending=[True, False])
    class_breakdown.to_csv('data/processed_csv/class_breakdown.csv', index=False)
    print(f"Class breakdown saved to data/processed_csv/class_breakdown.csv")
    
    # Category breakdown by class
    category_breakdown = df.groupby(['Reparto', 'Classe', 'Categoria'])['Valore'].sum().reset_index()
    category_breakdown = category_breakdown.sort_values(
        by=['Reparto', 'Classe', 'Valore'], ascending=[True, True, False]
    )
    category_breakdown.to_csv('data/processed_csv/category_breakdown.csv', index=False)
    print(f"Category breakdown saved to data/processed_csv/category_breakdown.csv")
    
    # Top products per department
    for reparto in df['Reparto'].unique():
        reparto_df = df[df['Reparto'] == reparto]
        if len(reparto_df) > 0:
            top_products_reparto = reparto_df.groupby(['Codice', 'Descrizione'])['Valore'].sum().reset_index()
            top_products_reparto = top_products_reparto.sort_values(by='Valore', ascending=False).head(10)
            
            # Create a safe filename from the reparto name
            safe_reparto = ''.join(c if c.isalnum() else '_' for c in reparto)
            output_file = f'data/processed_csv/top_products_{safe_reparto}.csv'
            top_products_reparto.to_csv(output_file, index=False)
            print(f"Top products for {reparto} saved to {output_file}")
    
    # Create detailed stats file with top articles by department, class, and category
    print("\nCreating detailed statistics file...")
    
    # Get the top articles overall
    stats = []
    stats.append("# TOP ARTICLES OVERALL")
    for _, row in top_products.head(10).iterrows():
        stats.append(f"{row['Codice']}: {row['Descrizione']} - {row['Valore']:.2f} EUR")
    
    # Get top departments
    stats.append("\n# TOP DEPARTMENTS")
    top_depts = df.groupby('Reparto')['Valore'].sum().reset_index()
    top_depts = top_depts.sort_values(by='Valore', ascending=False)
    for _, row in top_depts.head(10).iterrows():
        stats.append(f"{row['Reparto']} - {row['Valore']:.2f} EUR")
    
    # Get top classes
    stats.append("\n# TOP CLASSES")
    top_classes = df.groupby('Classe')['Valore'].sum().reset_index()
    top_classes = top_classes.sort_values(by='Valore', ascending=False)
    for _, row in top_classes.head(10).iterrows():
        stats.append(f"{row['Classe']} - {row['Valore']:.2f} EUR")
    
    # Save all stats to text file
    with open('data/processed_csv/detailed_stats.txt', 'w') as f:
        f.write('\n'.join(stats))
    print("Detailed statistics saved to data/processed_csv/detailed_stats.txt")
    
    print("\nData enhancement completed!")

if __name__ == "__main__":
    enhance_flat_data() 