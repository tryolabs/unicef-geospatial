from tests.types import BechmarkQuestion

questions = [
    {
        "question": "What is the primary aim of the Children’s Climate Risk Index (CCRI)?",
        "answer": "The CCRI aims to rank countries where vulnerable children are also exposed to a wide range of climate and environmental hazards, providing a comprehensive assessment of how these hazards intersect with children’s existing vulnerabilities.",
    },
    {
        "question": "What is the foundational risk framework adopted by CCRI 2025?",
        "answer": "CCRI 2025 adopted the hazard x exposure x vulnerability as the foundational risk framework, based on IPCC (2020).",
    },
    {
        "question": "According to the CCRI 2025 framework, what does 'Exposure' refer to?",
        "answer": "In the CCRI framework, 'Exposure' refers to the presence of children that could be adversely affected by hazards.",
    },
    {
        "question": "What are the two main pillars that structure the CCRI 2025 analysis?",
        "answer": "The two main pillars are Pillar 1, focusing on children’s exposure to climate and climate-sensitive hazards, and Pillar 2, considering the inherent vulnerabilities of children.",
    },
    {
        "question": "How does the focus on hazard types differ between CCRI 2025 and CCRI 2021?",
        "answer": "CCRI 2025 focuses more specifically on climate and climate-sensitive hazards, whereas CCRI 2021 included a broader mix of climate and environmental hazards.",
    },
    {
        "question": "What significant geographic group is included in CCRI 2025 that was omitted in the 2021 version?",
        "answer": "CCRI 2025 includes the Small Island Developing States (SIDS), which were omitted from CCRI 2021 due to previous data limitations.",
    },
    {
        "question": "Does CCRI 2025 quantify the specific impact of human-induced climate change on children?",
        "answer": "No, CCRI 2025 does not quantify the impact of human-induced climate change separately from naturally occurring extreme weather events; it identifies children's exposure to all hazards.",
    },
    {
        "question": "Are future projections of climate risks included in the CCRI 2025 analysis?",
        "answer": "No, CCRI 2025 does not include analysis on future projections of climate risks on children due to uncertainty in available projections and child population data, and lack of reliable future child vulnerability estimates.",
    },
    {
        "question": "List three criteria used for selecting input data for the CCRI 2025.",
        "answer": "The criteria for input data selection include being Open source, Global, Quantifiable, Comparable, Spatially distributed, and Child centric. (Any three of these).",
    },
    {
        "question": "What specific data source is used for estimating the global child population in CCRI 2025?",
        "answer": "WorldPop’s global gridded children population estimate (Under 18) for 2024 at 100m spatial resolution was used.",
    },
    {
        "question": "What data source is utilized for the Fluvial Flood hazard analysis in CCRI 2025?",
        "answer": "JRC’s gridded Global Flood Hazard model (Baugh, 2024) at 100-year return period and 90m spatial resolution.",
    },
    {
        "question": "What water depth threshold is considered for riverine flood exposure analysis?",
        "answer": "A water depth above 1cm (pixel value greater than or equal to 1 in the processing pipeline) is considered for riverine flood exposure analysis.",
    },
    {
        "question": "How is Agricultural Drought defined within the CCRI 2025 document?",
        "answer": "Agricultural drought is defined as occurring when there is insufficient soil moisture to meet the needs of a particular crop at a particular time.",
    },
    {
        "question": "What index is used as a proxy to estimate children's exposure to agricultural drought?",
        "answer": "The Agricultural Stress Index (ASI) is used as a proxy for agricultural drought exposure.",
    },
    {
        "question": "What wind speed threshold is used to classify a tropical storm in the CCRI 2025 methodology?",
        "answer": "A wind speed greater than 63 km/hr is considered as a named tropical storm, following WMO guidance.",
    },
    {
        "question": "List the four dimensions considered when defining a heatwave in CCRI 2025.",
        "answer": "The four dimensions considered for heatwaves are: frequency (number per year), duration (total days), severity (temperature above local average), and extremely high temperatures (days exceeding 35 degrees Celsius).",
    },
    {
        "question": "What is the data source for the temperature input used in the heatwave analysis?",
        "answer": "Daily aggregate temperature data from the ERA5 reanalysis (produced by Copernicus Climate Change Service at ECMWF) is used.",
    },
    {
        "question": "What threshold, based on WHO guidelines, is adopted for PM2.5 air pollution exposure analysis?",
        "answer": "A threshold of 5 μg/m3, following WHO air quality guidance (WHO, 2021), is adopted for PM2.5 exposure.",
    },
    {
        "question": "Which specific vector-borne disease is included in CCRI 2025, and why are others excluded?",
        "answer": "Only Malaria is included in CCRI 2025. Other vector-borne diseases like dengue and zika are excluded due to a lack of global data availability.",
    },
    {
        "question": "What are the 7 components included in Pillar 2 (Child Vulnerability) of CCRI 2025?",
        "answer": "The 7 components of Pillar 2 are: Health, Nutrition, WASH, Education, Protection, Poverty, and Child Survival.",
    },
    {
        "question": "Name two indicators used within the 'Health' component of Pillar 2.",
        "answer": "Indicators under Health include: Percentage of infants receiving DTP1 vaccine, Percentage of infants receiving DTP3 vaccine, Percentage of deliveries attended by skilled health personnel, and Percentage of population with access to electricity. (Any two).",
    },
    {
        "question": "What normalization technique is applied to all indicators, components, and pillars in CCRI 2025?",
        "answer": "The min-max normalization technique is used to scale values to a 0-10 range.",
    },
    {
        "question": "What aggregation method is used to combine the absolute and relative exposure indicators for individual hazards in Pillar 1?",
        "answer": "The geometric mean is used to aggregate the absolute and relative exposure indicators for individual hazard components in Pillar 1.",
    },
    {
        "question": "Which aggregation method is used to combine indicators within the components of Pillar 2 (Child Vulnerability)?",
        "answer": "The arithmetic mean is used to aggregate the indicators and components in Pillar 2.",
    },
    {
        "question": "What is the primary purpose of using Principal Component Analysis (PCA) in the pixel-level CCRI calculation?",
        "answer": "PCA is applied to reduce the dimensionality of the climate risk data (Pillar 1 hazards) while preserving as much variability as possible, helping to identify the most significant components.",
    },
    {
        "question": "How are the pixel-level Pillar 1 hazard data and the country-level Pillar 2 vulnerability data combined to create the final pixel-level index?",
        "answer": "The geometric mean is used to combine the Pillar 1 (pixel-level) and Pillar 2 (country-level, applied homogeneously across the country's pixels) indicators.",
    },
    {
        "question": "What is one limitation mentioned regarding the interpretation of the composite CCRI score?",
        "answer": "One limitation is that combining multiple indicators into one score can obscure individual component performance, or a low overall score might hide poor performance in specific areas. (Other valid limitations: invites overly simplistic interpretations, results depend on indicator/threshold choices, missing data affects scores, normalization/aggregation choices affect scores).",
    },
    {
        "question": "What types of climate-related processes are explicitly mentioned as *not* being considered in the CCRI 2025 index?",
        "answer": "The index does not consider slow-onset processes such as rising sea levels, glacier melting, or ocean warming and acidification.",
    },
    {
        "question": "What probability does a '100-year return period' represent for an event occurring in any given year?",
        "answer": "A 100-year return period indicates a 1% probability of the event being equaled or exceeded in any given year.",
    },
    {
        "question": "What data resolution is used for the gridded child population data from WorldPop?",
        "answer": "The WorldPop gridded child population data used has a 100m spatial resolution.",
    },
]

benchmark_questions = [
    BechmarkQuestion(**question, variations=None, response_type="textual")
    for question in questions
]
