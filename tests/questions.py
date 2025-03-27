# single dataset with non processing questions
simple_questions = {
    "What's the percentage of births without a birth weight registered in Nigeria?": "77",
    "What was the percentage of children vaccinated for tuberculosis in Ethiopia in 2020?": "70",
    # "How many children were born in Ethiopia in 2020?": "3961198",
    # "What percentage of adolescent from the poorest households complete secondary education in Uruguay?": "5.07",
    # "Whats the total percentage of girls aged 15-19 who are married in Costa Rica?": "9.5",
}

# multi dataset with non processing questions
medium_questions = {
    "How many births were vaccinated for tuberculosis in Ethiopia in 2020?": str(
        3961198 * 70 / 100
    ),
    "What was the frequency of heatwaves in Uruguay in the 1990s?": "4.85",
}

# multi dataset processing questions
hard_questions = {
    "How many children are affected by coastal floods in Colombia?": "22714",
    # "How many children are exposed to floods in South Asia region?": "XXXXXX",
    # south_asia = ["Afghanistan","Bangladesh","Bhutan","India","Sri Lanka","Maldives","Nepal","Pakistan",]
    # "How many malnourished children face multi-hazard risk?": "XXXXXX",
}
