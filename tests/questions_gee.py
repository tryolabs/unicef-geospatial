from tests.types import BechmarkQuestion

# Multi-Hazard Questions
data_single_hazard = (
    {
        "agricultural drought": {
            "Angola": 4099009,
            "Nicaragua": 878626,
            "Uruguay": 233589,
            "Colombia": 3149198,
        },
        "air pollution": {
            "Angola": 16338870,
            "Nicaragua": 1976847,
            "Uruguay": 604115,
            "Colombia": 11212840,
        },
        "coastal floods": {
            "Angola": 6909,
            "Nicaragua": 3977,
            "Uruguay": 910,
            "Colombia": 22714,
        },
        "drought SPEI": {
            "Angola": 573838,
            "Nicaragua": 6326,
            "Uruguay": 119691,
            "Colombia": 2361523,
        },
        "drought SPI": {
            "Angola": 114626,
            "Nicaragua": 6326,
            "Uruguay": 115915,
            "Colombia": 1438632,
        },
        "extreme heat": {
            "Angola": 2360001,
            "Nicaragua": 574883,
            "Uruguay": 0,
            "Colombia": 1272004,
        },
        "fire frequency": {
            "Angola": 5394005,
            "Nicaragua": 89740,
            "Uruguay": 120480,
            "Colombia": 157301,
        },
        "fire intensity": {
            "Angola": 1154385,
            "Nicaragua": 72040,
            "Uruguay": 60119,
            "Colombia": 589614,
        },
        "heatwave duration": {
            "Angola": 13274160,
            "Nicaragua": 1974811,
            "Uruguay": 0,
            "Colombia": 9452636,
        },
        "heatwave frequency": {
            "Angola": 13974860,
            "Nicaragua": 1971445,
            "Uruguay": 0,
            "Colombia": 10066570,
        },
        "heatwave severity": {
            "Angola": 0,
            "Nicaragua": 0,
            "Uruguay": 529360,
            "Colombia": 19277,
        },
        "river floods": {
            "Angola": 714157,
            "Nicaragua": 38704,
            "Uruguay": 47840,
            "Colombia": 797908,
        },
        "sand and dust storms": {
            "Angola": 1027946,
            "Nicaragua": 43,
            "Uruguay": 88,
            "Colombia": 32659,
        },
        "tropical storms": {
            "Angola": 0,
            "Nicaragua": 2024094,
            "Uruguay": 0,
            "Colombia": 1748864,
        },
        "vectorborne malaria pv": {
            "Angola": 0,
            "Nicaragua": 441785,
            "Uruguay": 0,
            "Colombia": 6174789,
        },
        "vectorborne malaria pf": {
            "Angola": 15984150,
            "Nicaragua": 77840,
            "Uruguay": 0,
            "Colombia": 366051,
        },
    },
)
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
