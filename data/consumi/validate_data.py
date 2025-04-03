import pandas as pd
import os
import glob

def load_all_original_data():
    """
    Load all original CSV files to get raw data for validation.
    """
    # Get all consumption directories
    base_dir = 'data/consumi'
    consumption_dirs = [os.path.join(base_dir, d) for d in os.listdir(base_dir) 
                       if os.path.isdir(os.path.join(base_dir, d)) and 'Consumi_2024' in d]
    
    all_articles = []
    
    for input_dir in consumption_dirs:
        # Get all CSV files in the directory
        csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
        
        for file_path in csv_files:
            try:
                # Extract reparto name from directory name
                reparto = os.path.basename(input_dir).split('_')[0]
                
                # Read CSV file
                df = pd.read_csv(file_path)
                
                # Standardize column names
                if 'Primo Per.' in df.columns and 'Sec. Per.' in df.columns:
                    df = df.rename(columns={'Primo Per.': 'Primo_Periodo', 'Sec. Per.': 'Secondo_Periodo'})
                
                # Only keep article rows (those with Codice and Descrizione)
                df = df[(df['Codice'].notna()) & (df['Descrizione'].notna())]
                
                # Add reparto, month, and year information
                df['Reparto_Dir'] = reparto
                
                filename = os.path.basename(file_path)
                if filename.startswith('details_'):
                    parts = filename.split('_')
                    if len(parts) >= 2:
                        df['Mese'] = parts[1]
                
                df['Anno'] = '2024'
                
                # Use only the first period value (they are the same)
                df['Valore'] = df['Primo_Periodo']
                
                # Extract class and category from code if available
                df['Classe_Code'] = df['Codice'].apply(lambda x: x.split('.')[0] if isinstance(x, str) and '.' in x else '')
                df['Categoria_Code'] = df['Codice'].apply(lambda x: x.split('.')[1] if isinstance(x, str) and '.' in x and len(x.split('.')) > 1 else '')
                
                all_articles.append(df)
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
    
    if all_articles:
        combined_df = pd.concat(all_articles, ignore_index=True)
        return combined_df
    else:
        return None

def validate_processed_data():
    """
    Validate that our processed data matches the original raw data.
    """
    # Load the original data
    print("Loading original data...")
    original_df = load_all_original_data()
    
    if original_df is None:
        print("Failed to load original data.")
        return
    
    # Calculate total value from original data
    original_df['Valore'] = pd.to_numeric(original_df['Valore'], errors='coerce')
    original_total = original_df['Valore'].sum()
    print(f"Total value from original data: {original_total:.2f}")
    
    # Load the processed data
    print("Loading processed data...")
    try:
        processed_df = pd.read_csv('data/processed_csv/cleaned_consumi_2024.csv')
        processed_df['Valore'] = pd.to_numeric(processed_df['Valore'], errors='coerce')
        processed_total = processed_df['Valore'].sum()
        print(f"Total value from processed data: {processed_total:.2f}")
        
        # Compare totals
        diff = abs(original_total - processed_total)
        if diff < 0.01:
            print("VALIDATION PASSED: Totals match within rounding error.")
        else:
            print(f"VALIDATION FAILED: Difference of {diff:.2f}")
        
        # Validate totals by reparto
        print("\nValidating totals by department...")
        reparto_summary = pd.read_csv('data/processed_csv/reparto_summary.csv')
        reparto_total = reparto_summary['Valore'].sum()
        print(f"Total from reparto summary: {reparto_total:.2f}")
        
        if abs(reparto_total - processed_total) < 0.01:
            print("VALIDATION PASSED: Reparto summary matches processed data.")
        else:
            print(f"VALIDATION FAILED: Difference of {abs(reparto_total - processed_total):.2f}")
            
        # Create a flat version with just articles
        print("\nCreating flat article file...")
        flat_articles = processed_df.copy()
        
        # Save the flat article file
        flat_articles.to_csv('data/processed_csv/flat_articles.csv', index=False)
        print(f"Created flat article file with {len(flat_articles)} records")
        
        # Group by different hierarchies and verify the totals
        print("\nVerifying hierarchical groupings...")
        
        # Verify reparto totals
        reparto_verification = flat_articles.groupby('Reparto')['Valore'].sum().reset_index()
        reparto_verification_total = reparto_verification['Valore'].sum()
        print(f"Total from reparto verification: {reparto_verification_total:.2f}")
        
        # Verify class totals
        class_verification = flat_articles.groupby(['Reparto', 'Classe'])['Valore'].sum().reset_index()
        class_verification_total = class_verification['Valore'].sum()
        print(f"Total from class verification: {class_verification_total:.2f}")
        
        # Verify category totals
        category_verification = flat_articles.groupby(['Reparto', 'Classe', 'Categoria'])['Valore'].sum().reset_index()
        category_verification_total = category_verification['Valore'].sum()
        print(f"Total from category verification: {category_verification_total:.2f}")
        
    except Exception as e:
        print(f"Error validating data: {e}")

if __name__ == "__main__":
    validate_processed_data() 