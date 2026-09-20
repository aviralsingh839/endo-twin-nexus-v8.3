"""Generate synthetic longitudinal dataset - V8.3."""
from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from src.utils.synthetic import generate_scenario_dataset, generate_synthetic_cohort

if __name__ == "__main__":
    print("Generating 6 longitudinal scenarios...")
    scenarios = generate_scenario_dataset(Path("data/synthetic/scenarios"), seed=42)
    print(f"Generated {len(scenarios)} scenarios")

    print("Generating synthetic cohort (10 subjects, 30 days)...")
    cohort = generate_synthetic_cohort(n_subjects=10, days=30, samples_per_day=12,
                                       output_dir=Path("data/synthetic/cohort"), seed=42)
    print(f"Generated cohort with {len(cohort)} subjects")
    print("All synthetic data clearly labelled SYNTHETIC")
