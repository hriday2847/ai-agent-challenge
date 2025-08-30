import pytest
import pandas as pd
from custom_parsers.icici_parser import parse

def test_icici_parser():
    """Test the generated icici parser."""
    pdf_path = "data/icici/icic_sample.pdf.txt"
    expected_csv = "data/icici/icic_sample.csv"
    
    # Run parser
    result_df = parse(pdf_path)
    expected_df = pd.read_csv(expected_csv)
    
    # Assert equality
    assert result_df.equals(expected_df), f"Parser output does not match expected CSV"
    print("Parser test passed!")

if __name__ == "__main__":
    test_icici_parser()
