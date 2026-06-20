"""
cr_asamblea_legislativa.py - Calculates allocation of seats to parties
in the Costa Rican General Election for the Legislative Assembly.

Source used for election data - https://www.tse.go.cr/SVR2026/

de la clase trabajadora - left
liberal progresista -
"""

import json

election_data: dict[str, dict] = {
    "San José": {
        "seats": 18,
        "results": {
            "Pueblo Soberano": 314_307,  # right/populist
            "Liberación Nacional": 203_357,  # center-left
            "Frente Amplio": 126_419,  # left
            "Coalición Agenda Ciudadana": 40_161,  # center-left
            "Unidad Social Cristiana": 38_313,  # center-right
            "Nueva República": 19_922,  # right
            "Avanza": 16_112,
            "Unidos Podemos": 7_701,
            "Compatriotas": 7_283,
            "Liberal Progresista": 5_706,  # right
            "Progreso Social Democratico": 5_267,  # left
            "Nueva Generación": 3_637,  # right
            "Integracion Nacional": 2_577,
            "Justicia Social Costarricense": 2_371,  # left
            "Centro Democrático y Social": 2_145,
            "De la Clase Trabajadora": 1_817,  # very left
            "Esperanza y Libertad": 1_375,
            "Esperanza Nacional": 1_306,
            "Unión Costarricense Democrática": 1_290,
            "Aquí Costa Rica Manda": 1_037,  # right
            "Anticorrupcion Costarricense": 939,
            "Alianza Costa Rica Primero": 799
        }
    },
    "Cartago": {
        "seats": 6,
        "results": {
            "Pueblo Soberano": 104_267,
            "Liberación Nacional": 84_805,
            "Frente Amplio": 40_718,
            "Coalición Agenda Ciudadana": 16_947,
            "Unidad Social Cristiana": 12_383,
            "Actuemos Ya": 11_577,
            "Unidos Podemos": 6_390,
            "Avanza": 5_160,
            "Nueva República": 4_473,
            "Nueva Generación": 3_051,
            "Progreso Social Democratico": 2_966,
            "Liberal Progresista": 2_346,
            "Justicia Social Costarricense": 1_165,
            "Alianza Costa Rica Primero": 1_089,
            "De la Clase Trabajadora": 986,
            "Integracion Nacional": 937,
            "Centro Democrático y Social": 806,
            "Esperanza y Libertad": 701,
            "Esperanza Nacional": 681,
            "Unión Costarricense Democrática": 499,
            "Aquí Costa Rica Manda": 429
        }
    },
    "Heredia": {
        "seats": 5,
        "results": {
            "Pueblo Soberano": 110_324,
            "Liberación Nacional": 71_733,
            "Frente Amplio": 43_912,
            "Coalición Agenda Ciudadana": 13_153,
            "Unidad Social Cristiana": 9_786,
            "Nueva República": 5_947,
            "Avanza": 5_176,
            "Unidos Podemos": 2_491,
            "Liberal Progresista": 2_299,
            "Progreso Social Democratico": 1_168,
            "Integracion Nacional": 996,
            "Alianza Costa Rica Primero": 959,
            "Centro Democrático y Social": 810,
            "Nueva Generación": 769,
            "Justicia Social Costarricense": 674,
            "De la Clase Trabajadora": 570,
            "Esperanza y Libertad": 554,
            "Esperanza Nacional": 418,
            "Unión Costarricense Democrática": 299,
            "Aquí Costa Rica Manda": 250
        }
    },
    "Alajuela": {
        "seats": 12,
        "results": {
            "Pueblo Soberano": 254_208,
            "Liberación Nacional": 110_207,
            "Frente Amplio": 52_399,
            "Unidad Social Cristiana": 16_628,
            "Coalición Agenda Ciudadana": 12_888,
            "Nueva República": 11_859,
            "Avanza": 7_941,
            "Unidos Podemos": 3_696,
            "Progreso Social Democratico": 3_508,
            "Liberal Progresista": 2_899,
            "Esperanza Nacional": 2_626,
            "Nueva Generación": 2_174,
            "Integracion Nacional": 1_563,
            "Centro Democrático y Social": 1_483,
            "Justicia Social Costarricense": 1_156,
            "De la Clase Trabajadora": 924,
            "Unión Costarricense Democrática": 832,
            "Esperanza y Libertad": 781,
            "Aquí Costa Rica Manda": 717,
            "Alianza Costa Rica Primero": 625
        }
    },
    "Guanacaste": {
        "seats": 5,
        "results": {
            "Pueblo Soberano": 83_052,
            "Liberación Nacional": 30_168,
            "Frente Amplio": 9_430,
            "Unidad Social Cristiana": 9_135,
            "Coalición Agenda Ciudadana": 5_594,
            "Unión Guanacasteca": 5_147,
            "Nueva Generación": 5_050,
            "Nueva República": 4_050,
            "Avanza": 3_403,
            "Unidos Podemos": 1_980,
            "Progreso Social Democratico": 1_667,
            "Liberal Progresista": 1_153,
            "Alianza Costa Rica Primero": 1_015,
            "Integracion Nacional": 557,
            "Justicia Social Costarricense": 536,
            "Centro Democrático y Social": 513,
            "Aquí Costa Rica Manda": 486,
            "Unión Costarricense Democrática": 444,
            "De la Clase Trabajadora": 329,
            "Esperanza y Libertad": 193,
            "Esperanza Nacional": 190
        }
    },
    "Puntarenas": {
        "seats": 6,
        "results": {
            "Pueblo Soberano": 114_410,
            "Liberación Nacional": 30_907,
            "Frente Amplio": 12_061,
            "Unidad Social Cristiana": 10_645,
            "Nueva República": 7_163,
            "Coalición Agenda Ciudadana": 3_809,
            "Progreso Social Democratico": 1_764,
            "Avanza": 1_725,
            "Unidos Podemos": 1_701,
            "Liberal Progresista": 1_661,
            "Alianza Costa Rica Primero": 1_655,
            "Centro Democrático y Social": 1_319,
            "Nueva Generación": 1_164,
            "Integracion Nacional": 730,
            "Espeanza y Libertad": 669,
            "Unión Costarricense Democrática": 642,
            "Justicia Social Costarricense": 561,
            "Aquí Costa Rica Manda": 477,
            "De la Clase Trabajadora": 472,
            "Esperanza Nacional": 464
        }
    },
    "Limón": {
        "seats": 5,
        "results": {
            "Pueblo Soberano": 95_109,
            "Liberación Nacional": 24_443,
            "Unidad Social Cristiana": 12_548,
            "Frente Amplio": 8_143,
            "Nueva República": 5_370,
            "Unidos Podemos": 4_531,
            "Coalición Agenda Ciudadana": 3_802,
            "Justicia Social Costarricense": 2_340,
            "Progreso Social Democratico": 1_924,
            "Avanza": 1_385,
            "Alianza Costa Rica Primero": 1_172,
            "Liberal Progresista": 1_099,
            "Nueva Generación": 1_081,
            "Centro Democrático y Social": 753,
            "Esperanza y Libertad": 718,
            "De la Clase Trabajadora": 465,
            "Integracion Nacional": 445,
            "Unión Costarricense Democrática": 443,
            "Aquí Costa Rica Manda": 432,
            "Esperanza Nacional": 376
        }
    },
}


def filter_votes(results: dict[str, int], filter: int|float):
    pass_filter = {}
    fail_filter = {}
    for party, vote_count in results.items():
        if vote_count >= filter:
            pass_filter[party] = vote_count
        else:
            fail_filter[party] = vote_count
    return {"pass": pass_filter, "fail": fail_filter}


def allot_seats(seats: int, results: dict[str, int]):
    # 1. Calculate total, quotient, and subquotient
    total = sum(results.values())
    quotient = total / seats
    subquotient = quotient / 2
    #print(f"Total: {total}")
    #print(f"Quotient: {quotient}")
    #print(f"Subquotient: {subquotient}")

    # 2. Only consider groups under the subquotient
    remaining_votes = filter_votes(results, subquotient)["pass"]
    #print(remaining_votes)

    # 3. Allot whole numbers of seats
    seat_allocation = {
        party: int(vote_count // quotient)
        for party, vote_count in remaining_votes.items()
    }
    remaining_votes = {
        party: vote_count % quotient
        for party, vote_count in remaining_votes.items()
    }

    #print(seat_allocation)
    #print(remaining_votes)

    # 4. Distribute remaining seats by greatest remainder
    seats -= sum(seat_allocation.values())

    used_remainders = {}
    while seats:
        highest_remainder = max(remaining_votes,
                                key=lambda p:
                                (remaining_votes[p], seat_allocation[p] > 0))
        seat_allocation[highest_remainder] += 1
        seats -= 1
        used_remainders[highest_remainder] = remaining_votes.pop(
            highest_remainder)
        if not remaining_votes and seats:
            remaining_votes = used_remainders.copy()

    return seat_allocation


def calculate_results(election_data: dict[str, dict[str, int]]):
    election_results = {}
    for provincia, data in election_data.items():
        province_results = allot_seats(data["seats"], data["results"])
        for party, seats in province_results.items():
            election_results.setdefault(party, 0)
            election_results[party] += seats
    return election_results


def print_results(results: dict[str, int]):
    results = results.copy()
    while results:
        current = max(results, key=results.get)
        print(f"{current}: {results[current]}")
        del results[current]


print(
    "\n*** 2026 Costa Rican General Election - Legislative Assembly Seat Allocation by Party ***\n"
)
print_results(calculate_results(election_data))

print("\n\n*** By Province ***")

for provincia, data in election_data.items():
    province_results = allot_seats(data["seats"], data["results"])
    print(f"\n-- {provincia} --\n")
    print_results(province_results)


def generate_web_payload(election_data: dict[str, int]):
    """Packages the results into a structured format for the web."""
    national_results = calculate_results(election_data)
    
    payload = {
        "national_total": national_results,
        "provinces": {}
    }
    
    for provincia, data in election_data.items():
        province_results = allot_seats(data["seats"], data["results"])
        
        # Sort the dictionary so the frontend receives it in descending order
        sorted_results = dict(sorted(province_results.items(), key=lambda item: item[1], reverse=True))
        
        payload["provinces"][provincia] = {
            "total_seats_available": data["seats"],
            "allocation": sorted_results
        }
        
    return payload

# Instead of printing, you now export the JSON:
web_data = generate_web_payload(election_data)
print(json.dumps(web_data, indent=2, ensure_ascii=False))

# Optional: Save it directly to a file for your frontend to read
with open('election_results.json', 'w', encoding='utf-8') as f:
    json.dump(web_data, f, ensure_ascii=False, indent=2)
