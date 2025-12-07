"""
Japanese currency formatting utilities.
Provides functions for formatting numbers in Japanese currency format (万円, 億円).
"""


def format_jpy_plain(value: float | int) -> str:
    """
    Format value as simple comma-separated yen.
    Example: 1234567 -> '¥1,234,567'
    """
    return f"¥{int(round(value)):,}"


def format_jpy_jpunit(value: float | int) -> str:
    """
    Format value in Japanese unit style (万円, 億円).
    
    Examples:
        100000000 -> '1億円'
        50000000  -> '5,000万円'
        123456789 -> '1億2,345万円'
        -12345678 -> '-1,234万円'
        0         -> '0円'
    """
    sign = "-" if value < 0 else ""
    v = abs(int(round(value)))
    
    oku, rem = divmod(v, 100_000_000)   # 億 (100 million)
    man, _ = divmod(rem, 10_000)        # 万 (10 thousand)
    
    parts = []
    if oku:
        parts.append(f"{oku}億")
    if man:
        parts.append(f"{man:,}万")
    if not parts:
        parts.append("0")
    
    return f"{sign}{''.join(parts)}円"


def format_jpy_axis(value: float | int) -> str:
    """
    Format value for chart axis labels (shorter format).
    
    Examples:
        100000000 -> '1億'
        50000000  -> '5,000万'
        0         -> '0'
    """
    if value == 0:
        return "0"
    
    sign = "-" if value < 0 else ""
    v = abs(int(round(value)))
    
    oku, rem = divmod(v, 100_000_000)
    man, _ = divmod(rem, 10_000)
    
    parts = []
    if oku:
        parts.append(f"{oku}億")
    if man:
        parts.append(f"{man:,}万")
    if not parts:
        return "0"
    
    return f"{sign}{''.join(parts)}"


def choose_axis_unit(max_value: float) -> tuple:
    """
    Choose appropriate axis unit based on max value.
    
    Returns:
        Tuple of (divisor, suffix, unit_name)
    """
    if max_value >= 1e8:
        return 1e8, "億円", "億"
    elif max_value >= 1e4:
        return 1e4, "万円", "万"
    else:
        return 1.0, "円", ""


def get_axis_tickvals_ticktext(min_val: float, max_val: float, num_ticks: int = 6) -> tuple:
    """
    Generate tick values and text for Plotly axis in Japanese format.
    
    Returns:
        Tuple of (tickvals, ticktext)
    """
    import numpy as np
    
    # Generate evenly spaced tick values
    tickvals = np.linspace(min_val, max_val, num_ticks)
    tickvals = [max(0, v) for v in tickvals]  # Ensure non-negative
    
    # Format tick text in Japanese
    ticktext = [format_jpy_axis(v) for v in tickvals]
    
    return tickvals, ticktext
