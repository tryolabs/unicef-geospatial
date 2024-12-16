import pycountry


def standarize_country_name(country: str) -> str:
    """Return the official country name using the input."""
    try:
        country_obj = (
            pycountry.countries.get(name=country)
            or pycountry.countries.get(alpha_2=country)
            or pycountry.countries.get(alpha_3=country)
        )
        if country_obj:
            return country_obj.name
        else:
            return country
    except KeyError:
        return country
