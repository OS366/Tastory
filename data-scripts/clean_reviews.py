from datetime import datetime

import numpy as np
import pandas as pd


def clean_text(text):
    """Clean text fields by removing extra whitespace and handling missing values."""
    if pd.isna(text):
        return ""
    return str(text).strip()


def clean_rating(rating):
    """Convert rating to float and validate range."""
    try:
        rating = float(rating)
        if 0 <= rating <= 5:
            return rating
        return np.nan
    except:
        return np.nan


def clean_reviews(df):
    """Main function to clean the reviews dataset."""

    # Create a copy to avoid modifying the original
    cleaned = df.copy()

    # 1. Clean text fields
    text_columns = ["AuthorName", "Review"]
    for col in text_columns:
        print(f"Cleaning text column: {col}")
        cleaned[col] = cleaned[col].apply(clean_text)

    # 2. Clean rating
    print("Cleaning ratings")
    cleaned["Rating"] = cleaned["Rating"].apply(clean_rating)

    # 3. Convert dates to datetime
    print("Converting dates")
    date_columns = ["DateSubmitted", "DateModified"]
    for col in date_columns:
        cleaned[col] = pd.to_datetime(cleaned[col])

    # 4. Convert IDs to integers
    print("Converting IDs")
    id_columns = ["ReviewId", "RecipeId", "AuthorId"]
    for col in id_columns:
        cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce").astype("Int64")

    # 5. Remove reviews with missing essential data
    print("Removing invalid entries")
    # Remove rows where essential fields are missing
    essential_columns = ["ReviewId", "RecipeId", "Rating"]
    cleaned = cleaned.dropna(subset=essential_columns)

    # 6. Add derived features
    print("Adding derived features")
    # Add review length
    cleaned["ReviewLength"] = cleaned["Review"].str.len()
    # Add time between submission and modification
    cleaned["TimeDelta"] = (cleaned["DateModified"] - cleaned["DateSubmitted"]).dt.total_seconds()
    # Flag if review was modified
    cleaned["WasModified"] = cleaned["TimeDelta"] > 0

    # 7. Sort by date
    print("Sorting data")
    cleaned = cleaned.sort_values("DateSubmitted")

    # Reset the index
    cleaned = cleaned.reset_index(drop=True)

    return cleaned


def main():
    # Read the dataset
    print("Reading reviews dataset...")
    reviews_df = pd.read_csv("reviews.csv")

    # Clean the dataset
    print("Cleaning reviews dataset...")
    cleaned_df = clean_reviews(reviews_df)

    # Save the cleaned dataset
    print("Saving cleaned dataset...")
    try:
        # Save CSV
        cleaned_df.to_csv("reviews_cleaned.csv", index=False)
        print("CSV file saved successfully")

        # Save parquet
        cleaned_df.to_parquet("reviews_cleaned.parquet")
        print("Parquet file saved successfully")
    except Exception as e:
        print(f"Error saving files: {str(e)}")

    print("\nCleaning complete! Summary of changes:")
    print(f"Original shape: {reviews_df.shape}")
    print(f"Cleaned shape: {cleaned_df.shape}")

    # Print data info
    print("\nDataset Info:")
    print(cleaned_df.info())

    # Print sample statistics
    print("\nRating Statistics:")
    print(cleaned_df["Rating"].describe())

    # Print sample of first few rows
    print("\nSample of cleaned data:")
    print(cleaned_df.head(2).to_string())


if __name__ == "__main__":
    main()
