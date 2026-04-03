import os
import csv
import argparse
from faker import Faker
from wrangler.core import WranglerEngine
from datasets.fintech.generator import FintechGenerator
from datasets.nlp.generator import NlpGenerator

# Registry of available scenarios
SCENARIOS = {
    'fintech': {'generator': FintechGenerator, 'path': 'datasets/fintech'},
    'nlp': {'generator': NlpGenerator, 'path': 'datasets/nlp'}
}

def write_csv(filename, data):
    if not data: return
    fieldnames = data[0].keys()
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main(scenario_name):
    if scenario_name not in SCENARIOS:
        print(f"Error: Scenario '{scenario_name}' not found.")
        return

    print(f"--- Launching Scenario: {scenario_name.upper()} ---")
    config = SCENARIOS[scenario_name]
    fake = Faker()
    
    # 1. Generate Data
    gen = config['generator'](fake)
    datasets = gen.generate(num_rows=10000)
    
    # 2. Save CSVs
    for filename, data in datasets.items():
        write_csv(filename, data)
        print(f"  Generated {filename} with {len(data)} rows.")

    # 3. Initialize DB and Load
    engine = WranglerEngine(f"{scenario_name}_analysis.db")
    engine.execute_script(f"{config['path']}/schema.sql")
    
    # 4. Optional: Run tests/benchmarks from dataset folder
    print(f"--- {scenario_name.upper()} Environment Ready ---")
    engine.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='DataWrangler Multi-Scenario Runner')
    parser.add_argument('--scenario', type=str, default='fintech', help='Scenario to run (fintech, nlp, etc.)')
    args = parser.parse_args()
    main(args.scenario)
