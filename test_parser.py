#!/usr/bin/env python3
"""
Simple test script for the generated parser
"""

import pandas as pd
import sys
import os

def test_parser(bank_name: str):
    """Test the generated parser for a specific bank."""
    try:
        # Import the parser
        parser_module = __import__(f'custom_parsers.{bank_name}_parser', fromlist=['parse'])
        parse_func = getattr(parser_module, 'parse')
        
        # Test paths
        pdf_path = f"data/{bank_name}/icic_sample.pdf.txt"
        csv_path = f"data/{bank_name}/icic_sample.csv"  # Using the existing CSV
        
        # Run parser
        result_df = parse_func(pdf_path)
        expected_df = pd.read_csv(csv_path)
        
        # Compare results
        is_equal = result_df.equals(expected_df)
        
        if is_equal:
            print(f"{bank_name.upper()} parser test PASSED!")
            return True
        else:
            print(f"{bank_name.upper()} parser test FAILED!")
            print("Result:")
            print(result_df)
            print("Expected:")
            print(expected_df)
            return False
            
    except Exception as e:
        print(f"Error testing {bank_name} parser: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        bank_name = sys.argv[1]
    else:
        bank_name = "icici"
    
    success = test_parser(bank_name)
    sys.exit(0 if success else 1)
