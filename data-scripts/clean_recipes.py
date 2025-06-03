import pandas as pd
import numpy as np
import ast
from datetime import datetime
import re
import json

def parse_time(time_str):
    """Convert ISO time format (PT24H45M) to minutes."""
    if pd.isna(time_str):
        return np.nan
    
    hours = re.search(r'(\d+)H', str(time_str))
    minutes = re.search(r'(\d+)M', str(time_str))
    
    total_minutes = 0
    if hours:
        total_minutes += int(hours.group(1)) * 60
    if minutes:
        total_minutes += int(minutes.group(1))
    
    return total_minutes

def clean_string_array(array_str):
    """Convert string arrays like c("value1", "value2") to Python lists."""
    if pd.isna(array_str):
        return []
    
    try:
        # Handle already processed lists
        if isinstance(array_str, list):
            return array_str
        
        # Convert string representation to list
        if isinstance(array_str, str):
            # Remove the c() wrapper if present
            cleaned = array_str.strip()
            if cleaned.startswith('c(') and cleaned.endswith(')'):
                cleaned = cleaned[2:-1]
            
            # Try to parse as JSON first
            try:
                result = json.loads(f'[{cleaned}]')
                return result
            except:
                # If JSON parsing fails, try ast.literal_eval
                try:
                    cleaned = cleaned.replace('c(', '[').replace(')', ']')
                    result = ast.literal_eval(cleaned)
                    return result if isinstance(result, list) else [result]
                except:
                    # If all parsing fails, split by comma and clean
                    items = [item.strip().strip('"\'') for item in cleaned.split(',')]
                    return [item for item in items if item]
        
        return []
    except Exception as e:
        print(f"Error processing string array: {str(e)}")
        return []

def clean_numeric(value):
    """Convert string numeric values to float, handling NA."""
    if pd.isna(value):
        return np.nan
    try:
        return float(value)
    except:
        return np.nan

def clean_recipes(df):
    """Main function to clean the recipes dataset."""
    
    # Create a copy to avoid modifying the original
    cleaned = df.copy()
    
    # 1. Convert time columns to minutes
    time_columns = ['CookTime', 'PrepTime', 'TotalTime']
    for col in time_columns:
        cleaned[col] = cleaned[col].apply(parse_time)
    
    # 2. Parse date
    cleaned['DatePublished'] = pd.to_datetime(cleaned['DatePublished'])
    
    # 3. Clean string arrays
    array_columns = [
        'Images', 'Keywords', 'RecipeCategory',
        'RecipeIngredientQuantities', 'RecipeIngredientParts',
        'RecipeInstructions'
    ]
    for col in array_columns:
        print(f"Processing column: {col}")
        cleaned[col] = cleaned[col].apply(clean_string_array)
    
    # 4. Convert numeric columns
    numeric_columns = [
        'AggregatedRating', 'ReviewCount', 'Calories',
        'FatContent', 'SaturatedFatContent', 'CholesterolContent',
        'SodiumContent', 'CarbohydrateContent', 'FiberContent',
        'SugarContent', 'ProteinContent', 'RecipeServings'
    ]
    for col in numeric_columns:
        cleaned[col] = cleaned[col].apply(clean_numeric)
    
    # 5. Clean up image URLs
    cleaned['MainImage'] = cleaned['Images'].apply(
        lambda x: x[0] if x and len(x) > 0 else None
    )
    
    # 6. Create ingredient pairs (combining quantities and parts)
    def combine_ingredients(row):
        quantities = row['RecipeIngredientQuantities']
        parts = row['RecipeIngredientParts']
        if not quantities or not parts:
            return []
        return [f"{q} {p}" for q, p in zip(quantities, parts)]
    
    cleaned['Ingredients'] = cleaned.apply(combine_ingredients, axis=1)
    
    # 7. Additional cleaning steps
    # Remove any completely empty rows
    cleaned = cleaned.dropna(how='all')
    
    # Reset the index
    cleaned = cleaned.reset_index(drop=True)
    
    return cleaned

def main():
    # Read the dataset
    print("Reading recipes dataset...")
    recipes_df = pd.read_csv('recipes.csv')
    
    # Clean the dataset
    print("Cleaning recipes dataset...")
    cleaned_df = clean_recipes(recipes_df)
    
    # Save the cleaned dataset
    print("Saving cleaned dataset...")
    try:
        # Save CSV first
        cleaned_df.to_csv('recipes_cleaned.csv', index=False)
        print("CSV file saved successfully")
        
        # Convert list columns to strings for parquet
        for col in cleaned_df.select_dtypes(include=['object']):
            if isinstance(cleaned_df[col].iloc[0], list):
                cleaned_df[col] = cleaned_df[col].apply(json.dumps)
        
        # Save parquet
        cleaned_df.to_parquet('recipes_cleaned.parquet')
        print("Parquet file saved successfully")
    except Exception as e:
        print(f"Error saving files: {str(e)}")
    
    print("Cleaning complete! Summary of changes:")
    print(f"Original shape: {recipes_df.shape}")
    print(f"Cleaned shape: {cleaned_df.shape}")
    
    # Print sample of first few rows
    print("\nSample of cleaned data:")
    print(cleaned_df.head(2).to_string())

if __name__ == "__main__":
    main() 