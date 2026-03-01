import sys
from typing import Dict, List, Union, Any
import pandas as pd

def validate_json(config: Dict[str, Any], df: pd.DataFrame = None) -> tuple[Dict[str, Any], List[str]]:
    errors = []

    # Extract from nested analysis or root level
    analysis = config.get("analysis", {})

    # Operation: look in analysis first, then root, then default to "average"
    operation = (
        analysis.get("operation")
        or config.get("operation")
        or "average"
    )

    # Output: analysis → root "output" → "output_type" → default "graphics"
    output = (
        analysis.get("output")
        or config.get("output")
        or config.get("output_type")
        or "graphics"
    )

    # Other fields (normalize everything to lists where appropriate)
    country_raw = analysis.get("country") or config.get("country", [])
    region_raw  = analysis.get("region") or analysis.get("continent") or config.get("region", []) or config.get("continent", [])
    year_raw    = analysis.get("year") or config.get("year", [])

    # Normalize to lists
    country = [country_raw] if isinstance(country_raw, str) else (country_raw if isinstance(country_raw, list) else [])
    region = [region_raw] if isinstance(region_raw, str) else (region_raw if isinstance(region_raw, list) else [])
    year = [year_raw] if isinstance(year_raw, int) else (year_raw if isinstance(year_raw, list) else [])

    # Phase 2 new params
    start_year = analysis.get("start_year", 1960)
    end_year = analysis.get("end_year", 2024)
    decline_years = analysis.get("decline_years", 3)
    top_n = analysis.get("top_n", 10)
    analyses_list = analysis.get("analyses", [])

    # 1. Required keys check (Phase 1/2)
    required = {"operation", "output_type", "data_path", "input_type"}
    missing = required - set(config.keys()) - set(analysis.keys())
    if missing:
        errors.append(f"Missing keys: {list(missing)}")

    # 2. Operation validation
    if operation not in {"sum", "average"}:
        errors.append(f"Invalid operation: {operation}")

    # 3. Output validation
    if output not in {"console", "graphics", "streamlit", "dashboard"}:
        errors.append(f"Invalid output: {output}")

    # 4. Country validation (cross-check with DF if provided - Phase 1 restore)
    if df is not None:
        df_countries = df["Country Name"].unique()
        invalid_countries = [c for c in country if c not in df_countries]
        if invalid_countries:
            errors.append(f"Invalid countries: {invalid_countries}")

    # 5. Region/Continent validation
    if df is not None:
        df_regions = df["Continent"].unique()
        invalid_regions = [r for r in region if r not in df_regions]
        if invalid_regions:
            errors.append(f"Invalid regions: {invalid_regions}")

    # 6. Year validation
    if df is not None:
        df_years = [int(col) for col in df.columns if str(col).isdigit()]
        invalid_years = [y for y in year if not isinstance(y, int) or y not in df_years or y < 1960 or y > 2024]
    else:
        invalid_years = [y for y in year if not isinstance(y, int) or y < 1960 or y > 2024]
    if invalid_years:
        errors.append(f"Invalid years: {invalid_years}")

    # Phase 2 validations
    input_type = config.get("input_type", "csv")
    if input_type not in {"csv", "json", "excel", "browser"}:
        errors.append(f"Invalid input_type: '{input_type}'")

    data_path = config.get("data_path")
    if not data_path:
        errors.append("Missing 'data_path' in config")

    if start_year >= end_year:
        errors.append("start_year must be < end_year")

    if decline_years <= 0:
        errors.append("decline_years must be > 0")

    if top_n <= 0:
        errors.append("top_n must be > 0")

    # Build validated config dict
    validated = {
        "operation": operation,
        "output_type": output,          # normalized name
        "country": country,
        "region": region,
        "continent": region,  # Alias
        "year": year,
        "input_type": input_type,
        "data_path": data_path,
        "analysis": {
            **analysis,
            "start_year": start_year,
            "end_year": end_year,
            "decline_years": decline_years,
            "top_n": top_n,
            "analyses": analyses_list
        }
    }

    if errors:
        print("Config validation errors:")
        for err in errors:
            print(f"  - {err}")

    else:
        print("[VALIDATION SUCCESS] Config is valid. Operation set to:", operation)

    return validated, errors