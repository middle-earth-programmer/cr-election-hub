import json
import os

# Costa Rican General Election data for the Legislative Assembly by province.
# Source: Tribunal Supremo de Elecciones (TSE)
def load_election_raw_data(filepath: str = "election_raw_data.json") -> dict:
    """Loads and parses raw electoral data from an external JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Electoral raw data file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def filter_votes(results: dict[str, int], threshold: int|float):
    """Filters results by subquotient threshold as defined by Costa Rican law."""
    pass_filter = {}
    fail_filter = {}
    for party, vote_count in results.items():
        if vote_count >= threshold:
            pass_filter[party] = vote_count
        else:
            fail_filter[party] = vote_count
    return {"pass": pass_filter, "fail": fail_filter}


def allot_seats(seats: int, results: dict[str, int]):
    """Calculates allocated seats using quotient and remainder metrics."""
    total = sum(results.values())
    if total == 0 or seats == 0:
        return {}
    
    quotient = total / seats
    subquotient = quotient / 2

    # Parties must cross the subquotient threshold to participate in allotment
    filtered = filter_votes(results, subquotient)
    remaining_votes = filtered["pass"]

    # Allot whole numbers of seats based on the quotient
    seat_allocation = {
        party: int(vote_count // quotient)
        for party, vote_count in remaining_votes.items()
    }
    
    # Calculate leftovers (remainders)
    remaining_votes = {
        party: vote_count % quotient
        for party, vote_count in remaining_votes.items()
    }

    # Distribute left-over seats by greatest remainder
    unallocated_seats = seats - sum(seat_allocation.values())

    used_remainders = {}
    while unallocated_seats > 0 and remaining_votes:
        highest_remainder = max(
            remaining_votes,
            key=lambda p: (remaining_votes[p], seat_allocation.get(p, 0) > 0)
        )
        seat_allocation[highest_remainder] = seat_allocation.get(highest_remainder, 0) + 1
        unallocated_seats -= 1
        used_remainders[highest_remainder] = remaining_votes.pop(highest_remainder)
        
        if not remaining_votes and unallocated_seats > 0:
            remaining_votes = used_remainders.copy()

    # Clean up parties with 0 seats
    return {party: seats for party, seats in seat_allocation.items() if seats > 0}


def calculate_national_seats(election_data: dict[str, dict]):
    """Aggregates calculated seat allocations from all provinces."""
    national_results = {}
    for provincia, data in election_data.items():
        province_results = allot_seats(data["seats"], data["results"])
        for party, seats in province_results.items():
            national_results[party] = national_results.get(party, 0) + seats
    return national_results


def generate_web_payload(election_data: dict[str, dict]):
    """
    Processes election data, calculates seat distribution, compiles popular vote 
    shares, and packages them dynamically into the structured dashboard JSON.
    """
    # 1. First, calculate seats for all parties
    national_seats = calculate_national_seats(election_data)
    
    # 2. Identify "major parties" (any party that won at least 1 seat nationally)
    major_parties = {party for party, seats in national_seats.items() if seats > 0}
    
    # 3. Compute national vote sums for calculating accurate popular vote %
    national_vote_sums = {}
    total_national_votes = 0
    for provincia, data in election_data.items():
        for party, votes in data["results"].items():
            national_vote_sums[party] = national_vote_sums.get(party, 0) + votes
            total_national_votes += votes

    # Compile National Seat & Popular Vote metrics
    processed_national_seats = {}
    processed_national_votes = {}
    
    other_seats = 0
    other_votes = 0

    for party, seats in national_seats.items():
        if party in major_parties:
            processed_national_seats[party] = seats
        else:
            other_seats += seats

    for party, votes in national_vote_sums.items():
        percentage = (votes / total_national_votes) * 100 if total_national_votes > 0 else 0
        if party in major_parties:
            processed_national_votes[party] = round(percentage, 2)
        else:
            other_votes += percentage

    if other_seats > 0:
        processed_national_seats["Other"] = other_seats
    processed_national_votes["Other"] = round(other_votes, 2)

    payload = {
        "national_total": {
            "seats": processed_national_seats,
            "popular_vote": processed_national_votes
        },
        "provinces": {}
    }

    # Compile Provincial Seat & Popular Vote metrics
    for provincia, data in election_data.items():
        province_seats = allot_seats(data["seats"], data["results"])
        province_votes_raw = data["results"]
        total_provincial_votes = sum(province_votes_raw.values())

        prov_seats_processed = {}
        prov_votes_processed = {}
        prov_other_seats = 0
        prov_other_votes = 0

        # Map seats
        for party, seats in province_seats.items():
            if party in major_parties:
                prov_seats_processed[party] = seats
            else:
                prov_other_seats += seats

        # Map votes
        for party, votes in province_votes_raw.items():
            percentage = (votes / total_provincial_votes) * 100 if total_provincial_votes > 0 else 0
            if party in major_parties:
                prov_votes_processed[party] = round(percentage, 2)
            else:
                prov_other_votes += percentage

        if prov_other_seats > 0:
            prov_seats_processed["Other"] = prov_other_seats
        prov_votes_processed["Other"] = round(prov_other_votes, 2)

        payload["provinces"][provincia] = {
            "total_seats_available": data["seats"],
            "seats": prov_seats_processed,
            "popular_vote": prov_votes_processed
        }

    return payload

# The main program for raw election data processing
if __name__ == "__main__":
    try:
        raw_data_filename = 'election_raw_data.json'
        election_data = load_election_raw_data(raw_data_filename)
        web_data = generate_web_payload(election_data)
        
        # Save directly to JSON for immediate web ingestion
        output_filename = 'election_results.json'
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(web_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n[Success] Calculated seat allotment & compiled vote ratios successfully!")
        print(f"[Success] Loaded raw input: '{raw_data_filename}' -> Exported compiled profile: '{output_filename}'\n")

        # Output Console summary of National Seats for reference
        print("--- Calculated National Seats Summary ---")
        for party, seats in sorted(web_data["national_total"]["seats"].items(), key=lambda x: x[1], reverse=True):
            print(f" * {party}: {seats} seats")
    except Exception as e:
        print(f"\n[Error] Failed to execute seat allotment calculations: {e}\n")