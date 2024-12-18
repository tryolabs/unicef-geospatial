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


def get_country_code(country: str) -> str:
    """Return the country code using the input."""
    try:
        country = standarize_country_name(country)
        country_obj = pycountry.countries.get(name=country)
        if country_obj:
            return country_obj.alpha_3
        else:
            return country
    except KeyError:
        return country
