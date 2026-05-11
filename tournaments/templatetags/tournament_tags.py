from django import template

register = template.Library()

@register.filter
def first_leg_for_fixture(fixtures, fixture):
    """Returns the matchday of the first leg for a given fixture pairing."""
    if not fixture.round_type or fixture.bracket_index is None:
        return fixture.matchday
    
    # Filter for same round and same bracket index
    pairing = [f for f in fixtures if f.round_type == fixture.round_type and f.bracket_index == fixture.bracket_index]
    if pairing:
        return min(f.matchday for f in pairing)
    return fixture.matchday

@register.filter
def get_second_leg(fixtures, fixture):
    """Returns the second leg fixture for a given first leg."""
    if not fixture.round_type or fixture.bracket_index is None:
        return None
    
    pairing = [f for f in fixtures if f.round_type == fixture.round_type and f.bracket_index == fixture.bracket_index]
    if len(pairing) > 1:
        # Sort by matchday and pick the second one
        pairing.sort(key=lambda x: x.matchday)
        return pairing[1]
    return None

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument."""
    try:
        return int(float(value) * float(arg))
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtracts the argument from the value."""
    try:
        return int(float(value) - float(arg))
    except (ValueError, TypeError):
        return 0
