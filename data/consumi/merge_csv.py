import pandas as pd
import os
import glob

def process_csv_files(input_dirs, output_file):
    """
    Process all CSV files from multiple directories and merge them into a single file
    with proper handling of hierarchical structure and avoiding duplicates.
    
    Args:
        input_dirs (list): List of directory paths containing CSV files
        output_file (str): Path to save the merged CSV file
    """
    # Create empty list to store all processed data
    all_data = []
    
    # Process each directory
    for input_dir in input_dirs:
        if not os.path.exists(input_dir):
            print(f"Directory {input_dir} does not exist. Skipping.")
            continue
            
        # Get all CSV files in the directory
        csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
        
        for file_path in csv_files:
            print(f"Processing {file_path}")
            try:
                # Extract reparto name from directory name
                reparto_dir = os.path.basename(input_dir).split('_')[0]
                
                # Read CSV file
        df = pd.read_csv(file_path)
                
                # Rename columns to standardize
                if 'Primo Per.' in df.columns and 'Sec. Per.' in df.columns:
                    df = df.rename(columns={'Primo Per.': 'Primo_Periodo', 'Sec. Per.': 'Secondo_Periodo'})
                
                # Create a 'Valore' column that takes the value from 'Primo_Periodo'
                # (since Primo_Periodo and Secondo_Periodo are identical)
                if 'Primo_Periodo' in df.columns:
                    df['Valore'] = df['Primo_Periodo']
                
                # Add month and year information from filename
                filename = os.path.basename(file_path)
                if filename.startswith('details_'):
                    # Extract month from filename (assuming format: details_MM_REPARTO_MONTH_YEAR.csv)
                    parts = filename.split('_')
                    if len(parts) >= 2:
                        month = parts[1]
                        df['Mese'] = month
                
                # Add year column
                df['Anno'] = '2024'  # All files are from 2024
                
                # Fill NaN values with empty strings for string comparison
                for col in ['Reparto', 'Classe', 'Categoria', 'Codice', 'Descrizione']:
                    if col in df.columns:
                        df[col] = df[col].fillna('')
                
                # Handle hierarchical structure
                # First, identify row types to understand the hierarchy
                df['Row_Type'] = 'Unknown'
                
                # Reparto rows have Reparto filled but not Classe
                reparto_mask = (df['Reparto'] != '') & (df['Classe'] == '')
                df.loc[reparto_mask, 'Row_Type'] = 'Reparto'
                
                # Classe rows have Classe filled but not Categoria
                classe_mask = (df['Classe'] != '') & (df['Categoria'] == '')
                df.loc[classe_mask, 'Row_Type'] = 'Classe'
                
                # Categoria rows have Categoria filled but not Descrizione/Codice
                categoria_mask = (df['Categoria'] != '') & (df['Descrizione'] == '') & (df['Codice'] == '')
                df.loc[categoria_mask, 'Row_Type'] = 'Categoria'
                
                # Article rows have Descrizione and Codice
                articolo_mask = (df['Descrizione'] != '') & (df['Codice'] != '')
                df.loc[articolo_mask, 'Row_Type'] = 'Articolo'
                
                # Set default reparto name from directory if not present
                if df['Reparto'].str.strip().eq('').all():
                    df['Reparto_Dir'] = reparto_dir
                else:
                    # Extract the reparto from the file if it exists
                    reparto_values = df[df['Row_Type'] == 'Reparto']['Reparto'].unique()
                    if len(reparto_values) > 0 and reparto_values[0] != '':
                        df['Reparto_Dir'] = reparto_values[0]
                    else:
                        df['Reparto_Dir'] = reparto_dir
                
                # Now, propagate the values downward to fill the hierarchy
                df = propagate_hierarchy(df)
                
                # Keep only rows with values
                df = df[df['Valore'].notna()]
                
                # Append to the list of dataframes
                all_data.append(df)
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
    
    # Combine all dataframes
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Save to CSV
        combined_df.to_csv(output_file, index=False)
        print(f"Combined data saved to {output_file}")
        return combined_df
    else:
        print("No data to combine.")
        return None

def propagate_hierarchy(df):
    """
    Propagate hierarchical values downward, filling in missing values
    from higher levels in the hierarchy.
    """
    # Create a copy to avoid modifying the original during iteration
    result_df = df.copy()
    
    # Initialize current values
    current_reparto = ''
    current_classe = ''
    current_categoria = ''
    
    # Create new columns for the properly filled hierarchy
    result_df['Reparto_Filled'] = ''
    result_df['Classe_Filled'] = ''
    result_df['Categoria_Filled'] = ''
    
    # Iterate through rows in order
    for i, row in df.iterrows():
        row_type = row['Row_Type']
        
        if row_type == 'Reparto':
            current_reparto = row['Reparto']
            current_classe = ''
            current_categoria = ''
            
        elif row_type == 'Classe':
            current_classe = row['Classe']
            current_categoria = ''
            
        elif row_type == 'Categoria':
            current_categoria = row['Categoria']
            
        # Fill in the values for this row
        result_df.at[i, 'Reparto_Filled'] = current_reparto if current_reparto else row['Reparto_Dir']
        result_df.at[i, 'Classe_Filled'] = current_classe
        result_df.at[i, 'Categoria_Filled'] = current_categoria
    
    return result_df

def main():
    # Create output directory if it doesn't exist
    os.makedirs('data/processed_csv', exist_ok=True)
    
    # Get all consumption directories
    base_dir = 'data/consumi'
    consumption_dirs = [os.path.join(base_dir, d) for d in os.listdir(base_dir) 
                       if os.path.isdir(os.path.join(base_dir, d)) and 'Consumi_2024' in d]
    
    # Output file
    output_file = 'data/processed_csv/all_consumi_2024.csv'
    
    # Process all files
    result_df = process_csv_files(consumption_dirs, output_file)
    
    # Create analysis files
    if result_df is not None:
        # Use only Articolo rows for summaries to avoid double counting
        articoli_df = result_df[result_df['Row_Type'] == 'Articolo'].copy()
        
        # Convert Valore to numeric to ensure proper aggregation
        articoli_df['Valore'] = pd.to_numeric(articoli_df['Valore'], errors='coerce')
        
        # Use the filled hierarchy columns for grouping
        # Group by Reparto
        reparto_summary = articoli_df.groupby('Reparto_Filled')['Valore'].sum().reset_index()
        reparto_summary.rename(columns={'Reparto_Filled': 'Reparto'}, inplace=True)
        reparto_summary.to_csv('data/processed_csv/reparto_summary.csv', index=False)
        print(f"Created reparto summary with {len(reparto_summary)} records")
        
        # Group by Classe
        classe_summary = articoli_df.groupby(['Reparto_Filled', 'Classe_Filled'])['Valore'].sum().reset_index()
        classe_summary.rename(columns={'Reparto_Filled': 'Reparto', 'Classe_Filled': 'Classe'}, inplace=True)
        classe_summary.to_csv('data/processed_csv/classe_summary.csv', index=False)
        print(f"Created classe summary with {len(classe_summary)} records")
        
        # Group by Categoria
        categoria_summary = articoli_df.groupby(['Reparto_Filled', 'Classe_Filled', 'Categoria_Filled'])['Valore'].sum().reset_index()
        categoria_summary.rename(columns={'Reparto_Filled': 'Reparto', 'Classe_Filled': 'Classe', 'Categoria_Filled': 'Categoria'}, inplace=True)
        categoria_summary.to_csv('data/processed_csv/categoria_summary.csv', index=False)
        print(f"Created categoria summary with {len(categoria_summary)} records")
        
        # Create a more advanced analysis file with proper hierarchical information
        advanced_summary = result_df.copy()
        advanced_summary['Valore'] = pd.to_numeric(advanced_summary['Valore'], errors='coerce')
        
        # Only keep rows with non-zero values
        advanced_summary = advanced_summary[advanced_summary['Valore'] != 0]
        
        # Create an 'Anno-Mese' column for easier time analysis
        if 'Mese' in advanced_summary.columns and 'Anno' in advanced_summary.columns:
            advanced_summary['Anno-Mese'] = advanced_summary['Anno'] + '-' + advanced_summary['Mese']
        
        # Save the advanced analysis
        advanced_summary.to_csv('data/processed_csv/advanced_analysis.csv', index=False)
        print(f"Created advanced analysis with {len(advanced_summary)} records")
        
        # Create a cleaned version with just the necessary columns and proper hierarchy
        try:
            # Get available columns
            available_columns = articoli_df.columns.tolist()
            
            # Define needed columns with fallbacks
            needed_columns = ['Reparto_Filled', 'Classe_Filled', 'Categoria_Filled', 
                            'Codice', 'Descrizione', 'Valore', 'Mese']
            
            # Add optional columns if available
            if 'U.M.A.' in available_columns:
                needed_columns.append('U.M.A.')
            if 'U.M.C.' in available_columns:
                needed_columns.append('U.M.C.')
            if 'Coeff Conv' in available_columns:
                needed_columns.append('Coeff Conv')
            if 'Euro Medio' in available_columns:
                needed_columns.append('Euro Medio')
            if 'Quantita' in available_columns:
                needed_columns.append('Quantita')
            if 'Anno' in available_columns:
                needed_columns.append('Anno')
            
            # Extract only needed columns
            cleaned_df = articoli_df[needed_columns].copy()
            
            # Rename columns for clarity
            cleaned_df.rename(columns={
                'Reparto_Filled': 'Reparto',
                'Classe_Filled': 'Classe',
                'Categoria_Filled': 'Categoria'
            }, inplace=True)
            
            # Save cleaned data
            cleaned_df.to_csv('data/processed_csv/cleaned_consumi_2024.csv', index=False)
            print(f"Created cleaned data with {len(cleaned_df)} records")
            
        except Exception as e:
            print(f"Error creating cleaned file: {e}")
        
        print("Summary files created in data/processed_csv/")

if __name__ == "__main__":
    main() 