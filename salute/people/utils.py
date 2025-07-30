from phonenumber_field.phonenumber import PhoneNumber


def format_phone_number(phone_number: PhoneNumber | None) -> str | None:
    """
    Format a phone number for display.
    If the phone number is in the UK (country code 44), return it in national format.
    Otherwise, return it in international format.
    """
    if phone_number:
        if phone_number.country_code == 44:
            return phone_number.as_national
        return phone_number.as_international
    return None
