import csv
import json
import os
import sys
import unicodedata

def remove_accents(s: str) -> str:
    """Normalize to NFD and strip combining marks to handle accent variations."""
    return "".join(
        ch for ch in unicodedata.normalize("NFD", s)
        if not unicodedata.combining(ch)
    )

# Standard allocation of 57 seats across provinces
DEFAULT_PROVINCIAL_SEATS = {
    "San José": 18,
    "Alajuela": 12,
    "Cartago": 6,
    "Heredia": 5,
    "Guanacaste": 5,
    "Puntarenas": 6,
    "Limón": 5
}

def title_case_party(name: str) -> str:
    """
    Converts a party name to proper Title Case, keeping Spanish minor words 
    (like 'de', 'la', 'el', 'y', 'del', 'los', 'las', 'en', 'con', 'sin') in lowercase 
    unless they start the name. Corrects all-caps entries smoothly.
    """
    words = name.strip().split()
    if not words:
        return ""
    
    minor_words = {"de", "la", "el", "y", "del", "los", "las", "en", "con", "sin"}
    title_words = []
    for i, word in enumerate(words):
        word_lower = word.lower()
        if i > 0 and word_lower in minor_words:
            title_words.append(word_lower)
        else:
            title_words.append(word_lower.capitalize())
            
    return " ".join(title_words)


def standardize_headers(headers: list[str]) -> dict[str, str]:
    """
    Standardizes header name variations (English/Spanish, lowercase/uppercase)
    to map them to the corresponding internal keys.
    Supports accentless variants like 'escanos', 'escano', and synonyms like 'curules'.
    """
    header_mapping = {}
    for header in headers:
        clean = header.strip().lower()
        if clean in ["provincia", "province", "state", "region"]:
            header_mapping["province"] = header
        elif clean in ["partido", "partido político", "party", "political party"]:
            header_mapping["party"] = header
        elif clean in ["votos", "votes", "vote count"]:
            header_mapping["votes"] = header
        elif clean in ["seats", "escaños", "escanos", "escaño", "escano", "plazas", "plaza", "curules", "curul"]:
            header_mapping["seats"] = header
    return header_mapping


def clean_vote_tally(val_str: str) -> int:
    """
    Safely converts a string representation of a vote count to an integer.
    Handles diverse regional formatting variations:
    - Dot thousands separators: "126.419" -> 126419
    - Comma thousands separators: "126,419" -> 126419
    - Spaces: "126 419" -> 126419
    - Floating point zeros: "126419.00" -> 126419
    """
    clean = val_str.strip()
    if not clean:
        return 0
        
    # Remove percentage signs if present
    clean = clean.replace("%", "")
    
    # Handle ambiguous dots and commas (e.g. 1.246.307,00 or 1,246,307.00)
    if "." in clean and "," in clean:
        if clean.find(".") < clean.find(","):
            # Dot is thousands separator, comma is decimal
            clean = clean.replace(".", "").split(",")[0]
        else:
            # Comma is thousands separator, dot is decimal
            clean = clean.replace(",", "").split(".")[0]
    elif "." in clean:
        # Check if the dot is a thousands separator (e.g. "126.419") or decimal point (e.g. "126419.0")
        parts = clean.split(".")
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            clean = "".join(parts)
        else:
            clean = parts[0]
    elif "," in clean:
        # Check if the comma is a thousands separator or a decimal point
        parts = clean.split(",")
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            clean = "".join(parts)
        else:
            clean = parts[0]
            
    # Strip any spaces
    clean = "".join(clean.split())
    
    return int(float(clean))


def convert_csv_to_raw_json(csv_filepath: str, json_filepath: str = "election_raw_data_2022.json", raw_data: dict = None) -> dict:
    """
    Reads an electoral CSV file, dynamically handles segmented "Lugar: [Province]" blocks,
    aggregates vote tallies per party/province, and saves the formatted data to the standard JSON schema.
    Can accept an existing raw_data dictionary to accumulate values across multiple files.
    """
    if not os.path.exists(csv_filepath):
        raise FileNotFoundError(f"Source CSV file not found: {csv_filepath}")

    if raw_data is None:
        raw_data = {}
        
    current_province = None
    headers = None
    header_map = {}

    with open(csv_filepath, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        
        for row_idx, row in enumerate(reader, start=1):
            if not row or all(cell.strip() == "" for cell in row):
                continue
            
            # Clean cells
            row_cleaned = [cell.strip() for cell in row]
            first_cell = row_cleaned[0]

            # Look for province location indicator rows, e.g., "Lugar: SAN JOSE" or "Lugar: ALAJUELA"
            if first_cell.lower().startswith("lugar:") or first_cell.lower().startswith("provincia:"):
                prov_candidate = first_cell.split(":", 1)[1].strip()
                
                # Map to standard provincial naming conventions (handling accent variables)
                for standard_name in DEFAULT_PROVINCIAL_SEATS:
                    if prov_candidate.lower() in remove_accents(standard_name.lower()) \
                        or standard_name.lower() in remove_accents(prov_candidate.lower()):
                        current_province = standard_name
                        break
                else:
                    current_province = prov_candidate.title()
                
                # Reset header scanning because the columns may adjust below a new block header
                headers = None
                header_map = {}
                continue

            # If we don't have active headers yet, check if this line functions as a header row
            if not headers:
                temp_map = standardize_headers(row_cleaned)
                
                # If we already have a segmented metadata province, we only need party & vote columns
                if current_province and "party" in temp_map and "votes" in temp_map:
                    headers = row_cleaned
                    header_map = temp_map
                    continue
                # If we don't have a metadata province, we need a flat structure with a "province" column
                elif "province" in temp_map and "party" in temp_map and "votes" in temp_map:
                    headers = row_cleaned
                    header_map = temp_map
                    continue
                else:
                    # Line is treated as standard unparseable metadata, skip safely
                    continue

            # Skip overall summary rows if they are present
            if "TOTAL" in first_cell.upper() or "TSE" in first_cell.upper():
                continue

            try:
                # Retrieve Party Name and convert to proper Title Case
                raw_party = row_cleaned[headers.index(header_map["party"])]
                party_val = title_case_party(raw_party)
                
                # Skip statistical rows, metadata, summary lines, and empty cells
                party_upper = party_val.upper()
                if any(sig in party_upper for sig in [
                    "TOTAL", "TSE", "PARTICIPACIÓN", "ABSTENCIONISMO", "ABSTENCIÓN", 
                    "JUNTAS", "ELECTORES", "VOTOS RECIBIDOS", "VOTOS VÁLIDOS", 
                    "VOTOS EMITIDOS", "NULOS", "BLANCOS", "MESAS", "FALTANTES", "PROCESADAS"
                ]):
                    continue

                # Retrieve Vote Tally with our safe numeric cleaner
                votes_str = row_cleaned[headers.index(header_map["votes"])]
                votes_val = clean_vote_tally(votes_str)

                # Retrieve Province (Column has priority; active metadata acts as fallback)
                prov_val = current_province
                if "province" in header_map:
                    prov_raw = row_cleaned[headers.index(header_map["province"])]
                    for standard_name in DEFAULT_PROVINCIAL_SEATS:
                        if prov_raw.lower() in standard_name.lower() or standard_name.lower() in prov_raw.lower():
                            prov_val = standard_name
                            break
                    else:
                        prov_val = prov_raw.title()

                if not prov_val:
                    continue  # Ignore data lines if no province association could be established

                # Retrieve allocated seats if present, otherwise fall back to standard limits
                seats_val = None
                if "seats" in header_map:
                    seats_idx = headers.index(header_map["seats"])
                    if seats_idx < len(row_cleaned):
                        seats_str = row_cleaned[seats_idx]
                        if seats_str:
                            seats_val = int(seats_str)
                
                if not seats_val:
                    seats_val = DEFAULT_PROVINCIAL_SEATS.get(prov_val, 5)

                # Initialize structures inside raw_data
                if prov_val not in raw_data:
                    raw_data[prov_val] = {
                        "seats": seats_val,
                        "results": {}
                    }
                
                # Add or aggregate candidate counts (aggregates multiple counts cleanly)
                province_results = raw_data[prov_val]["results"]
                province_results[party_val] = province_results.get(party_val, 0) + votes_val

            except (ValueError, IndexError, KeyError) as e:
                # Gracefully swallow unexpected structure/format discrepancies on specific line loops
                continue

    # Write aggregated data out to standard target JSON filepath
    with open(json_filepath, 'w', encoding='utf-8') as out_f:
        json.dump(raw_data, out_f, ensure_ascii=False, indent=2)

    print(f"[Processed] CSV: '{os.path.basename(csv_filepath)}'")
    return raw_data


def generate_sample_csv(filepath: str):
    """Generates a dummy/sample CSV structure so the user has an immediate layout to test with."""
    sample_data = [
        ["Provincia", "Partido", "Votos", "Seats"],
        ["San José", "Pueblo Soberano", "314307", "18"],
        ["San José", "Liberación Nacional", "203357", "18"],
        ["San José", "Frente Amplio", "126419", "18"],
        ["Cartago", "Pueblo Soberano", "104267", "6"],
        ["Cartago", "Liberación Nacional", "84805", "6"],
        ["Heredia", "Pueblo Soberano", "110324", "5"],
        ["Heredia", "Liberación Nacional", "71733", "5"]
    ]
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(sample_data)
    print(f"[Info] Generated test CSV format: '{filepath}'")


if __name__ == "__main__":
    subfolder = "election_raw_data_2022"
    output_json = "election_raw_data_2022.json"
    
    # 1. Create directory if it doesn't exist
    if not os.path.exists(subfolder):
        os.makedirs(subfolder)
        print(f"[Info] Created missing subfolder: '{subfolder}'")
        
    # 2. Collect all CSV files in target folder
    csv_files = [f for f in os.listdir(subfolder) if f.lower().endswith('.csv')]
    
    # 3. Create a fallback sample CSV if the directory is empty
    if not csv_files:
        sample_path = os.path.join(subfolder, "sample_election_tallies.csv")
        generate_sample_csv(sample_path)
        csv_files = [os.path.basename(sample_path)]

    print(f"\n--- Processing {len(csv_files)} CSV file(s) in '{subfolder}' ---")
    
    # 4. Aggregatively process all CSV files inside a single dictionary
    aggregated_raw_data = {}
    success_count = 0
    
    for filename in sorted(csv_files):
        full_csv_path = os.path.join(subfolder, filename)
        try:
            convert_csv_to_raw_json(full_csv_path, json_filepath=output_json, raw_data=aggregated_raw_data)
            success_count += 1
        except Exception as e:
            print(f"[Error] Failed to process '{filename}': {e}", file=sys.stderr)

    if success_count > 0:
        print(f"\n[Success] Consolidated data compiled into -> '{output_json}'\n")
    else:
        print(f"\n[Warning] No files were parsed successfully.", file=sys.stderr)