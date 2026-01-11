"""
Example script demonstrating LLM-based lithology matching in dh2loop
=====================================================================

This script shows how to use the LLM-based alternative to fuzzywuzzy
for matching company lithology descriptions to standardized terms.

Supported providers:
- Ollama (local)
- llama-server (local)
- AWS Bedrock (cloud)
- OpenRouter (cloud)
"""

import os
import sys
import csv
import yaml
from pathlib import Path

# Add dh2loop to path if needed
sys.path.insert(0, str(Path(__file__).parent))

from dh2l_llm import create_matcher, load_litho_dictionary


def load_config(config_path: str = None):
    """Load configuration from YAML file"""
    if config_path is None:
        config_path = Path(__file__).parent / "llm_config.yaml"
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Warning: Could not load config file: {e}")
        return {}


def process_lithology_file(input_csv: str, 
                           output_csv: str,
                           litho_dict_file: str,
                           provider: str = "ollama",
                           config: dict = None):
    """
    Process a CSV file of company lithology descriptions and match them
    to standardized terms using an LLM.
    
    Args:
        input_csv: Input CSV with company lithology data
        output_csv: Output CSV with matched lithology and scores
        litho_dict_file: Path to lithology dictionary/thesaurus
        provider: LLM provider to use
        config: Configuration dict for the provider
    """
    
    print(f"Processing lithology file using {provider}...")
    
    # Load lithology dictionary
    print(f"Loading lithology dictionary from {litho_dict_file}...")
    litho_dict = load_litho_dictionary(litho_dict_file)
    print(f"Loaded {len(litho_dict)} lithology terms")
    
    # Create matcher
    if config is None:
        config = {}
    
    config['provider'] = provider
    matcher = create_matcher(config)
    print(f"Initialized {provider} matcher")
    
    # Read input CSV
    print(f"Reading input file: {input_csv}")
    input_data = []
    with open(input_csv, 'r', encoding='ISO-8859-1') as f:
        reader = csv.DictReader(f)
        for row in reader:
            input_data.append(row)
    
    print(f"Found {len(input_data)} records to process")
    
    # Process with LLM
    print("Matching lithology descriptions (this may take a while)...")
    results = []
    threshold = config.get('threshold', 0.8)
    
    for i, record in enumerate(input_data, 1):
        company_litho = record.get('Company_Litho', '')
        
        if not company_litho:
            continue
            
        print(f"Processing {i}/{len(input_data)}: {company_litho}")
        
        best_match, score = matcher.match_lithology(
            company_litho, 
            litho_dict,
            threshold=threshold
        )
        
        result = record.copy()
        result['CET_Litho'] = best_match
        result['Score'] = score
        results.append(result)
    
    # Write output CSV
    print(f"Writing results to: {output_csv}")
    if results:
        fieldnames = list(results[0].keys())
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
    
    print(f"Done! Processed {len(results)} records")
    
    # Print summary statistics
    classified = sum(1 for r in results if r['CET_Litho'] != 'unclassified_rock')
    avg_score = sum(float(r['Score']) for r in results) / len(results) if results else 0
    
    print(f"\nSummary:")
    print(f"  Total records: {len(results)}")
    print(f"  Classified: {classified} ({classified/len(results)*100:.1f}%)")
    print(f"  Unclassified: {len(results)-classified}")
    print(f"  Average score: {avg_score:.1f}")


def simple_example():
    """Run a simple example with hardcoded data"""
    
    print("=" * 60)
    print("Simple LLM-based Lithology Matching Example")
    print("=" * 60)
    
    # Example lithology dictionary (small subset)
    litho_dict = [
        "granite", "basalt", "andesite", "rhyolite",
        "sandstone", "limestone", "shale", "mudstone",
        "quartzite", "schist", "gneiss", "marble",
        "coal", "conglomerate", "breccia", "dolomite"
    ]
    
    # Example company descriptions
    company_descriptions = [
        "coarse grained granite with quartz",
        "dark volcanic basaltic rock",
        "fine grained sedimentary sandstone",
        "metamorphic schist with mica",
        "carbonate limestone layer",
        "unknown rock material"
    ]
    
    # Try Ollama first (most likely to be available for local testing)
    try:
        print("\nAttempting to use Ollama (local LLM)...")
        print("Note: Make sure Ollama is running: ollama serve")
        
        config = {
            "provider": "ollama",
            "model": "llama2",
            "endpoint": "http://localhost:11434"
        }
        
        matcher = create_matcher(config)
        
        print("\nMatching descriptions:")
        print("-" * 60)
        
        for desc in company_descriptions:
            match, score = matcher.match_lithology(desc, litho_dict, threshold=0.8)
            status = "✓" if score >= 80 else "✗"
            print(f"{status} '{desc}'")
            print(f"  -> {match} (score: {score:.1f})")
            print()
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nTo use this example, you need:")
        print("1. Install Ollama: https://ollama.ai/")
        print("2. Run: ollama pull llama2")
        print("3. Run: ollama serve")
        print("\nOr configure a different provider (bedrock, openrouter, llama-server)")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="LLM-based lithology matching for dh2loop"
    )
    parser.add_argument(
        '--mode', 
        choices=['simple', 'file'],
        default='simple',
        help='Run mode: simple example or process file'
    )
    parser.add_argument(
        '--input',
        help='Input CSV file with company lithology data'
    )
    parser.add_argument(
        '--output',
        help='Output CSV file for matched results'
    )
    parser.add_argument(
        '--dictionary',
        help='Path to lithology dictionary/thesaurus CSV'
    )
    parser.add_argument(
        '--provider',
        choices=['ollama', 'bedrock', 'openrouter', 'llama-server'],
        default='ollama',
        help='LLM provider to use'
    )
    parser.add_argument(
        '--config',
        help='Path to YAML config file'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'simple':
        simple_example()
    
    elif args.mode == 'file':
        if not all([args.input, args.output, args.dictionary]):
            parser.error("File mode requires --input, --output, and --dictionary")
        
        # Load config
        config = load_config(args.config)
        provider_config = config.get('providers', {}).get(args.provider, {})
        
        # Process file
        process_lithology_file(
            args.input,
            args.output,
            args.dictionary,
            args.provider,
            provider_config
        )


if __name__ == "__main__":
    main()
