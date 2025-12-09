"""
Simplified data cleaning utilities for survey question data
"""
import pandas as pd
import numpy as np
from pathlib import Path

def clean_survey_data(input_path, output_path=None):
    """
    Clean the raw survey data:
    1. Remove empty/unnamed columns
    2. Clean column names and question text
    3. Remove rows with missing questions
    4. Remove duplicate rows (data entry errors)
    
    Args:
        input_path: Path to raw CSV
        output_path: Path to save cleaned CSV (optional)
    
    Returns:
        Cleaned DataFrame
    """
    print("Loading raw data...")
    df = pd.read_csv(input_path)
    
    print(f"Original shape: {df.shape}")
    
    # 1. Remove unnamed/empty columns
    print("\n1. Cleaning columns...")
    cols_before = len(df.columns)
    
    # Drop columns that are unnamed or completely empty
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(axis=1, how='all')
    
    # Remove trailing whitespace from column names
    df.columns = df.columns.str.strip()
    
    cols_after = len(df.columns)
    print(f"   Removed {cols_before - cols_after} empty/unnamed columns")
    print(f"   Remaining columns: {cols_after}")
    
    # 2. Identify survey columns (everything except 'Question')
    question_col = 'Question'
    survey_cols = [col for col in df.columns if col != question_col]
    
    print(f"\n2. Data structure:")
    print(f"   Survey columns: {len(survey_cols)}")
    
    # 3. Clean question text
    print(f"\n3. Cleaning question text...")
    rows_before = len(df)
    
    # Remove rows with missing question text
    df = df[df[question_col].notna()]
    df = df[df[question_col].str.strip() != '']
    
    # Strip whitespace from questions
    df[question_col] = df[question_col].str.strip()
    
    rows_after = len(df)
    print(f"   Removed {rows_before - rows_after} rows with empty questions")
    
    # 4. Remove duplicate rows (data entry errors)
    print(f"\n4. Removing duplicate rows...")
    rows_before = len(df)
    
    # Drop exact duplicate rows across all columns
    df = df.drop_duplicates()
    
    rows_after = len(df)
    duplicates_removed = rows_before - rows_after
    print(f"   Removed {duplicates_removed} duplicate rows (data entry errors)")
    print(f"   Remaining questions: {rows_after}")
    
    # 5. Verify data - count non-null values in survey columns
    print(f"\n5. Verification...")
    survey_counts = {}
    for col in survey_cols:
        count = df[col].notna().sum()
        if count > 0:
            survey_counts[col] = count
    
    total_pairs = sum(survey_counts.values())
    print(f"   Total question-survey pairs: {total_pairs:,}")
    print(f"   Questions per survey (top 5):")
    
    top_surveys = sorted(survey_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    for survey, count in top_surveys:
        survey_name = survey[:50] + '...' if len(survey) > 50 else survey
        print(f"     {survey_name}: {count}")
    
    # 6. Save if output path provided
    if output_path:
        print(f"\n6. Saving cleaned data...")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"   ✓ Saved to: {output_path}")
    
    print(f"\n✓ Data cleaning complete!")
    print(f"Final shape: {df.shape}")
    
    return df

if __name__ == "__main__":
    # Run as script
    DATA_DIR = Path(__file__).parent.parent / 'data'
    RAW_DATA = DATA_DIR / 'raw' / 'PublicSurveyQuestions.csv'
    CLEANED_DATA = DATA_DIR / 'processed' / 'cleaned_survey_data.csv'
    
    df_clean = clean_survey_data(RAW_DATA, CLEANED_DATA)
    
    print(f"\nCleaned data ready for analysis!")
