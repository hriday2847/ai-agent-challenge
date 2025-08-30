#!/usr/bin/env python3
"""
AI Agent Challenge - Bank Statement Parser Generator
An autonomous coding agent that generates custom parsers for bank statement PDFs.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import re
from datetime import datetime

# LLM imports
try:
    import google.generativeai as genai
    from google.generativeai import GenerativeModel
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Agent state management
from dataclasses import dataclass, field
from typing import TypedDict, Annotated
import asyncio

# Rich console for better output
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

console = Console()

@dataclass
class AgentState:
    """State management for the agent loop."""
    target_bank: str
    pdf_path: str
    csv_path: str
    attempt: int = 1
    max_attempts: int = 3
    parser_code: str = ""
    test_results: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    success: bool = False

class ParserGenerator:
    """Main agent class for generating bank statement parsers."""
    
    def __init__(self, api_provider: str = "google"):
        self.api_provider = api_provider
        self.llm = self._setup_llm()
        
    def _setup_llm(self):
        """Setup LLM provider based on available APIs."""
        if self.api_provider == "google" and GOOGLE_AVAILABLE:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                console.print("[red]GOOGLE_API_KEY environment variable not set![/red]")
                sys.exit(1)
            genai.configure(api_key=api_key)
            return GenerativeModel('gemini-1.5-flash')
        
        elif self.api_provider == "groq" and GROQ_AVAILABLE:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                console.print("[red]GROQ_API_KEY environment variable not set![/red]")
                sys.exit(1)
            return Groq(api_key=api_key)
        
        else:
            console.print("[red]No valid LLM provider available![/red]")
            console.print("Please install google-generativeai or groq and set API keys.")
            sys.exit(1)
    
    def analyze_pdf_structure(self, pdf_path: str) -> str:
        """Analyze PDF structure and extract text content."""
        try:
            # For demo purposes, we'll read the text file representation
            if pdf_path.endswith('.txt'):
                with open(pdf_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                # In real implementation, use pdfplumber or PyPDF2
                content = "PDF content would be extracted here"
            
            return content
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    def analyze_csv_schema(self, csv_path: str) -> Dict[str, Any]:
        """Analyze CSV schema and structure."""
        try:
            df = pd.read_csv(csv_path)
            schema = {
                "columns": list(df.columns),
                "dtypes": df.dtypes.to_dict(),
                "sample_data": df.head(3).to_dict('records'),
                "total_rows": len(df)
            }
            return schema
        except Exception as e:
            return {"error": str(e)}
    
    def generate_parser_code(self, pdf_content: str, csv_schema: Dict[str, Any], bank_name: str) -> str:
        """Generate parser code using LLM."""
        
        prompt = f"""
You are an expert Python developer specializing in PDF parsing. Create a custom parser for {bank_name} bank statements.

PDF Content Structure:
{pdf_content}

Expected CSV Schema:
{json.dumps(csv_schema, indent=2)}

Requirements:
1. Create a function `parse(pdf_path: str) -> pd.DataFrame`
2. The function must return a DataFrame matching the CSV schema exactly
3. Handle date parsing, number formatting, and text extraction
4. Include proper error handling and validation
5. Use pandas, pdfplumber, and other standard libraries
6. Add comprehensive docstrings and type hints

Generate ONLY the Python code, no explanations:
"""
        
        try:
            if self.api_provider == "google":
                response = self.llm.generate_content(prompt)
                return response.text
            elif self.api_provider == "groq":
                response = self.llm.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                return response.choices[0].message.content
        except Exception as e:
            return f"# Error generating code: {str(e)}\n\n# Placeholder parser code\nimport pandas as pd\n\ndef parse(pdf_path: str) -> pd.DataFrame:\n    return pd.DataFrame()"
    
    def test_parser(self, parser_code: str, pdf_path: str, csv_path: str) -> Dict[str, Any]:
        """Test the generated parser against the expected CSV."""
        try:
            # Create temporary parser file
            parser_file = f"temp_parser_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            
            with open(parser_file, 'w') as f:
                f.write(parser_code)
            
            # Import and test the parser
            import importlib.util
            spec = importlib.util.spec_from_file_location("temp_parser", parser_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Run parser
            result_df = module.parse(pdf_path)
            expected_df = pd.read_csv(csv_path)
            
            # Compare results
            is_equal = result_df.equals(expected_df)
            
            # Cleanup
            os.remove(parser_file)
            
            return {
                "success": is_equal,
                "result_shape": result_df.shape,
                "expected_shape": expected_df.shape,
                "columns_match": list(result_df.columns) == list(expected_df.columns),
                "data_match": is_equal
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def fix_parser_code(self, parser_code: str, test_results: Dict[str, Any], pdf_content: str, csv_schema: Dict[str, Any]) -> str:
        """Fix parser code based on test results."""
        
        error_analysis = f"""
Previous parser failed with these issues:
{json.dumps(test_results, indent=2)}

PDF Content:
{pdf_content}

Expected Schema:
{json.dumps(csv_schema, indent=2)}

Previous Code:
{parser_code}

Please fix the parser code to address the issues above. Focus on:
1. Correct column names and data types
2. Proper date parsing
3. Number formatting
4. Text extraction logic
5. Error handling

Generate ONLY the corrected Python code:
"""
        
        try:
            if self.api_provider == "google":
                response = self.llm.generate_content(error_analysis)
                return response.text
            elif self.api_provider == "groq":
                response = self.llm.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": error_analysis}],
                    temperature=0.1
                )
                return response.choices[0].message.content
        except Exception as e:
            return parser_code  # Return original if fix fails
    
    def run_agent_loop(self, state: AgentState) -> AgentState:
        """Main agent loop: plan → generate → test → fix."""
        
        console.print(Panel(f"[bold blue]Starting Agent Loop for {state.target_bank}[/bold blue]"))
        
        while state.attempt <= state.max_attempts and not state.success:
            console.print(f"\n[bold yellow]Attempt {state.attempt}/{state.max_attempts}[/bold yellow]")
            
            # Step 1: Analyze inputs
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Analyzing PDF structure...", total=None)
                pdf_content = self.analyze_pdf_structure(state.pdf_path)
                progress.update(task, description="Analyzing CSV schema...")
                csv_schema = self.analyze_csv_schema(state.csv_path)
            
            # Step 2: Generate parser code
            console.print("[green]Generating parser code...[/green]")
            if state.attempt == 1:
                state.parser_code = self.generate_parser_code(pdf_content, csv_schema, state.target_bank)
            else:
                state.parser_code = self.fix_parser_code(state.parser_code, state.test_results[-1], pdf_content, csv_schema)
            
            # Step 3: Test parser
            console.print("[green]Testing parser...[/green]")
            test_result = self.test_parser(state.parser_code, state.pdf_path, state.csv_path)
            state.test_results.append(test_result)
            
            if test_result.get("success", False):
                state.success = True
                console.print("[bold green]✅ Parser generated successfully![/bold green]")
                break
            else:
                console.print(f"[red]❌ Test failed: {test_result.get('error', 'Unknown error')}[/red]")
                state.attempt += 1
        
        return state
    
    def save_parser(self, parser_code: str, bank_name: str):
        """Save the generated parser to custom_parsers directory."""
        parser_file = f"custom_parsers/{bank_name}_parser.py"
        
        # Ensure directory exists
        os.makedirs("custom_parsers", exist_ok=True)
        
        with open(parser_file, 'w') as f:
            f.write(parser_code)
        
        console.print(f"[green]Parser saved to: {parser_file}[/green]")
        return parser_file

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="AI Agent for Bank Statement Parser Generation")
    parser.add_argument("--target", required=True, help="Target bank name (e.g., icici)")
    parser.add_argument("--pdf", help="Path to PDF file (default: data/{target}/{target}_sample.pdf)")
    parser.add_argument("--csv", help="Path to CSV file (default: data/{target}/{target}_sample.csv)")
    parser.add_argument("--provider", choices=["google", "groq"], default="google", help="LLM provider")
    
    args = parser.parse_args()
    
    # Set default paths
    if not args.pdf:
        args.pdf = f"data/{args.target}/{args.target}_sample.pdf"
    if not args.csv:
        args.csv = f"data/{args.target}/{args.target}_sample.csv"
    
    # Handle text file for demo
    if not os.path.exists(args.pdf) and os.path.exists(args.pdf + ".txt"):
        args.pdf = args.pdf + ".txt"
    
    # Validate inputs
    if not os.path.exists(args.pdf):
        console.print(f"[red]PDF file not found: {args.pdf}[/red]")
        sys.exit(1)
    
    if not os.path.exists(args.csv):
        console.print(f"[red]CSV file not found: {args.csv}[/red]")
        sys.exit(1)
    
    # Initialize agent
    agent = ParserGenerator(api_provider=args.provider)
    
    # Create initial state
    state = AgentState(
        target_bank=args.target,
        pdf_path=args.pdf,
        csv_path=args.csv
    )
    
    # Run agent loop
    final_state = agent.run_agent_loop(state)
    
    if final_state.success:
        # Save parser
        parser_file = agent.save_parser(final_state.parser_code, args.target)
        
        # Generate test file
        test_file = f"tests/test_{args.target}_parser.py"
        os.makedirs("tests", exist_ok=True)
        
        test_code = f'''import pytest
import pandas as pd
from custom_parsers.{args.target}_parser import parse

def test_{args.target}_parser():
    """Test the generated {args.target} parser."""
    pdf_path = "{args.pdf}"
    expected_csv = "{args.csv}"
    
    # Run parser
    result_df = parse(pdf_path)
    expected_df = pd.read_csv(expected_csv)
    
    # Assert equality
    assert result_df.equals(expected_df), f"Parser output does not match expected CSV"
    print("✅ Parser test passed!")

if __name__ == "__main__":
    test_{args.target}_parser()
'''
        
        with open(test_file, 'w') as f:
            f.write(test_code)
        
        console.print(f"[green]Test file generated: {test_file}[/green]")
        console.print("\n[bold green]🎉 Agent completed successfully![/bold green]")
        console.print(f"Run: pytest {test_file} -v")
        
    else:
        console.print("[red]❌ Agent failed to generate working parser after all attempts[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
