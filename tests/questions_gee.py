from tests.types import BechmarkQuestion

# Multi-Hazard Questions
data_single_hazard = {
    "agricultural drought": {
        "Angola": 4734925,
        "Nicaragua": 1025854,
        "Uruguay": 261217,
        "Colombia": 3653606,
    },
    "air pollution": {
        "Angola": 18705698,
        "Nicaragua": 2311490,
        "Uruguay": 664396,
        "Colombia": 12998935,
    },
    "coastal floods": {
        "Angola": 4561,
        "Nicaragua": 7392,
        "Uruguay": 1099,
        "Colombia": 29475,
    },
    "drought SPEI": {
        "Angola": 637076,
        "Nicaragua": 12040,
        "Uruguay": 139014,
        "Colombia": 2769387,
    },
    "drought SPI": {
        "Angola": 99655,
        "Nicaragua": 12040,
        "Uruguay": 134579,
        "Colombia": 1691547,
    },
    "extreme heat": {
        "Angola": 2751854,
        "Nicaragua": 672663,
        "Uruguay": 0,
        "Colombia": 1489703,
    },
    "fire frequency": {
        "Angola": 6238879,
        "Nicaragua": 104389,
        "Uruguay": 140182,
        "Colombia": 187259,
    },
    "fire intensity": {
        "Angola": 1347117,
        "Nicaragua": 86302,
        "Uruguay": 68997,
        "Colombia": 690200,
    },
    "heatwave duration": {
        "Angola": 15501006,
        "Nicaragua": 2319487,
        "Uruguay": 0,
        "Colombia": 10975115,
    },
    "heatwave frequency": {
        "Angola": 16055660,
        "Nicaragua": 2319955,
        "Uruguay": 0,
        "Colombia": 11686740,
    },
    "heatwave severity": {
        "Angola": 0,
        "Nicaragua": 0,
        "Uruguay": 591412,
        "Colombia": 22840,
    },
    "river floods": {
        "Angola": 661223,
        "Nicaragua": 47062,
        "Uruguay": 49735,
        "Colombia": 930693,
    },
    "sand and dust storms": {
        "Angola": 1171088,
        "Nicaragua": 43,
        "Uruguay": 70,
        "Colombia": 36200,
    },
    "tropical storms": {
        "Angola": 0,
        "Nicaragua": 2382957,
        "Uruguay": 0,
        "Colombia": 2009752,
    },
    "vectorborne malaria pv": {
        "Angola": 0,
        "Nicaragua": 534003,
        "Uruguay": 0,
        "Colombia": 7155117,
    },
    "vectorborne malaria pf": {
        "Angola": 18325996,
        "Nicaragua": 90363,
        "Uruguay": 0,
        "Colombia": 432189,
    },
}


data_multi_hazard = {
    # and river and coastal floods
    "river and coastal floods": {
        "Colombia": 12368,
        "Angola": 1293,
        "Nicaragua": 2039,
        "Uruguay": 807,
    },
    # or river or coastal floods
    "river or coastal floods": {
        "Colombia": 808254,
        "Angola": 719773,
        "Nicaragua": 40642,
        "Uruguay": 47943,
    },
    # and malaria
    "both kinds of malaria": {
        "Colombia": 366034,
        "Angola": 0,
        "Nicaragua": 44914,
        "Uruguay": 0,
    },
    # or malaria
    "any kind of malaria": {
        "Colombia": 6174806,
        "Angola": 15984153,
        "Nicaragua": 474711,
        "Uruguay": 0,
    },
    # and floods
    "all kinds of floods": {
        "Colombia": 12035,
        "Angola": 367,
        "Nicaragua": 1693,
        "Uruguay": 724,
    },
    # or floods
    "some kind of flood": {
        "Colombia": 8191207,
        "Angola": 8974501,
        "Nicaragua": 1190525,
        "Uruguay": 620872,
    },
}


# Iterate through data to create benchmark questions
# Combine single and multi-hazard data
data = {**data_single_hazard, **data_multi_hazard}
benchmark_questions = []
for hazard_name, countries in data.items():
    for country, value in countries.items():
        benchmark_questions.append(
            BechmarkQuestion(
                question=f"How many children were exposed to {hazard_name} in {country}",
                answer=value,
                variations=[
                    f"How many children were affected by {hazard_name} in {country}?",
                    f"children impacted by {hazard_name} in {country}",
                ],
                response_type="numerical",
            )
        )
