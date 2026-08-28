import re
import math

def extract_decimals(text):
    """Yield (match_string, decimal_value, start_idx, end_idx) from prose."""
    matches = re.finditer(r'-?\d+(?:,\d{3})*(?:\.\d+)?', text)
    for match_obj in matches:
        match = match_obj.group(0)
        try:
            val = float(match.replace(',', ''))
            yield match, val, match_obj.start(), match_obj.end()
        except ValueError:
            pass

def extract_numbers_with_paths(obj, path="payload"):
    numbers = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            for num, paths in extract_numbers_with_paths(v, f"{path}.{k}").items():
                numbers.setdefault(num, []).extend(paths)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            for num, paths in extract_numbers_with_paths(v, f"{path}[{i}]").items():
                numbers.setdefault(num, []).extend(paths)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        numbers.setdefault(float(obj), []).append(path)
    elif isinstance(obj, str):
        import re
        matches = re.findall(r'(?<![a-zA-Z0-9_])-?\d+(?:,\d{3})*(?:\.\d+)?(?![a-zA-Z0-9_])', obj)
        for match in matches:
            try:
                val = float(match.replace(',', ''))
                numbers.setdefault(val, []).append(path)
            except ValueError:
                pass
    return numbers


def validate_prose_numbers(prose, numbers_whitelist, raise_on_fail=True):
    """
    Validates numbers in prose against a set/list/dict of whitelist decimals.
    """
    if isinstance(numbers_whitelist, dict):
        whitelist_vals = list(numbers_whitelist.keys())
        p10_exists = any("p10" in p.lower() for paths in numbers_whitelist.values() for p in paths)
        p90_exists = any("p90" in p.lower() for paths in numbers_whitelist.values() for p in paths)
    else:
        whitelist_vals = list(numbers_whitelist)
        p10_exists = True
        p90_exists = True

    errors = []
    
    for match, val, start_idx, end_idx in extract_decimals(prose):
        context = prose[max(0, start_idx - 10):min(len(prose), end_idx + 15)].lower()
        if val == 10.0 and any(label in context for label in ["10th", "p10", "10-90", "10‑90"]) and p10_exists:
            continue
        if abs(val) == 90.0 and any(label in context for label in ["90th", "p90", "10-90", "10‑90"]) and p90_exists:
            continue

        is_percentage = False
        if end_idx < len(prose) and prose[end_idx] == '%':
            is_percentage = True
            
        def is_exact_match(v):
            for a in whitelist_vals:
                if math.isclose(v, a, rel_tol=1e-5, abs_tol=1e-5):
                    return True
            return False

        if is_exact_match(val):
            continue
            
        if is_percentage:
            pct_decimal = val / 100.0
            if is_exact_match(pct_decimal):
                continue
                
            precision = 0
            if '.' in match:
                precision = len(match.split('.')[1])
                
            compare_places = precision + 2
            
            matched = False
            for w in whitelist_vals:
                rounded_w = round(w, compare_places)
                if math.isclose(pct_decimal, rounded_w, rel_tol=1e-5, abs_tol=1e-5):
                    matched = True
                    break
            if matched:
                continue
                
        err = f"Unsupported numeric claim in prose: {match} (value: {val}) not found in payload"
        errors.append((match, val, err))
        if raise_on_fail:
            raise ValueError(err)
            
    return errors
