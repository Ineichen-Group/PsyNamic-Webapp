import re
from collections import defaultdict
import pandas as pd

all_unicode_characters = r'[^\W\d_/\.]'
digit = r'\d+(\.\d+)?'


def remove_whitespace_around_slashes(dosage: str) -> str:
    """Remove whitespace around slashes in the dosage string."""
    dosage = dosage.replace(" / ", "/").replace(" /", "/").replace("/ ", "/")
    return dosage


def normalize_dosage(dosage: str) -> str:
    """Normalize dosage string by removing extra spaces and converting to lowercase."""

    number_words = {
        "zero": "0",
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "ten": "10",
    }
    # replace number words with digits
    for word, digit in number_words.items():
        dosage = re.sub(rf"\b{word}\b", digit, dosage, flags=re.IGNORECASE)

    rename_map = {
        "mcg": "µg",
        "microg": "µg",
        "microgram": "µg",
        "micrograms": "µg",
        "mgs": "mg",
        "grams": "g",
        "kilogram": "kg",
        "hours": "h",
        "hour": "h",
        "hr": "h",
        "minutes": "min",
        "minute": "min",
        "mins": "min",
    }
    # remove white spaces around slashes
    dosage = remove_whitespace_around_slashes(dosage)
    dosage = dosage.lower()

    # replace weird decimal dot like 0·5 mg/kg with normal dot
    dosage = re.sub(r"(\d)·(\d)", r"\1.\2", dosage)

    dosage = re.sub(r"\s+per\s+", "/", dosage)

    # replace ± nubmer or +- with or without ' '
    dosage = re.sub(r"\s*(±|\+-)\s?.*?\s", "", dosage)
    # remove , in 4 or more digit numbers
    dosage = re.sub(r"(?<=\d),(?=\d{3,})", "", dosage)

    # add white space between number and unit if missing
    dosage = re.sub(rf"(\d)({all_unicode_characters}+)", r"\1 \2", dosage)

    # replace kg(-1), kg (-1), kg-1 with /kg, make it also work with min(-1)
    dosage = re.sub(rf"({all_unicode_characters}+)\s*\(*-1\)*", r"/\1", dosage)
    dosage = remove_whitespace_around_slashes(dosage)

    # replace ' to ' with '-'
    dosage = re.sub(r"\sto\s", "-", dosage)

    # get unit, all letters after a number or / , not including white spaces
    match = re.search(
        rf"\d+\s*({all_unicode_characters}+(?:/{all_unicode_characters}+)*)", dosage)
    if match:
        unit = match.group(1)

        if unit in rename_map:
            dosage = dosage.replace(unit, rename_map[unit])

    # if it start with .number, add leading 0
    dosage = re.sub(r"^\.(\d+)", r"0.\1", dosage)
    # remove anything that is not number at the beginning
    dosage = re.sub(r"^[^\d]*", "", dosage)
    # remove brackets
    dosage = re.sub(r"[\(\)]", "", dosage)

    # remove /day or /daily or /dose
    dosage = re.sub(r"/(day|daily|dose)$", "", dosage)
    # remove 'of body weight' at the end
    dosage = re.sub(
        r"\s*(of body weight|/?\s?bw|/?\s?bodyweight|/?\s?body-weight)$", "", dosage)

    # check all units (either after / or space) and replace if in rename_map, e.g. mg/kg --> mg and kg
    units = re.finditer(
        rf'(?:(?<=\d)\s*|/)\s*({all_unicode_characters}+)', dosage)
    for unit in units:
        unit_str = unit.group(1)
        if unit_str in rename_map:
            dosage = dosage.replace(unit_str, rename_map[unit_str], 1)

    # Remove any - after numbers that are not followed by another number 15- or 20-mg
    dosage = re.sub(r"(\d+)-(?=\D|$)", r"\1 ", dosage)

    # Remove whitspaces
    dosage = dosage.replace("  ", " ")
    # remove white space around comma in numbers
    dosage = re.sub(r"(\d)\s+,", r"\1,", dosage)

    dosage = dosage.rstrip(" ")  # remove trailing white space
    dosage = dosage.rstrip(",")  # remove trailing comma

    return dosage


def extract_dosages(dosage: str) -> dict[str, str]:
    """Extract quantity and unit from a dosage string.

    Some decision rules:
    - If there is a range (e.g. 5-10 mg), extract min and max dosage
    - If there is a per weight unit (e.g. mg/kg), extract weight reference if available (e.g. 98 mg/70 kg -> weight reference is 70 kg)
    - If there is a per time unit (e.g. mg/h), extract time unit and set dose type to relative_time
    - If there is both per weight and per time unit (e.g. mg/kg/h), set dose type to relative_weight_time
    - If there is no per weight or per time unit, set dose type to absolute

    Look at test cases in test_dosage_norm.py for examples of how this should work.

    """
    dosage = normalize_dosage(dosage)

    dosage_dict = {
        "norm_text": dosage,
        "min": None,
        "max": None,
        "unit": None,
        "per_weight_unit": None,
        "weight_reference": None,
        "per_time_unit": None,
        "dose_type": None,
    }

    # extract unit, last digit followed by space and then unit
    unit = None
    if '/' in dosage:
        # unit last thing before first /
        match = re.search(rf"({all_unicode_characters}+)(?=/)", dosage)
        if match:
            unit = match.group(1)
            dosage_dict["unit"] = unit
    else:
        matches = re.findall(rf"[\d\.]+\s({all_unicode_characters}+)", dosage)
        if matches:
            unit = matches[-1]   # <-- last occurrence
            dosage_dict["unit"] = unit

    # \sor\s or \sand\s in dosage or comma separated numbers
    if re.search(r"\sor\s|\sand\s|\d\s?[-‐]\s?\d", dosage) or re.search(r",", dosage):
        dosage_without_units = dosage.split(unit)
        if '/' in dosage_without_units[-1]:
            # remove last part after last unit if it contains another unit reference like /kg or /h
            dosage_without_units = dosage_without_units[:-1]

        dosage_without_units = " ".join(dosage_without_units)
        # get first and last digit
        numbers = re.findall(r"[\d\.]+", dosage_without_units)
        if len(numbers) >= 2:
            # sort numbers and take first and last as min and max
            numbers = sorted([float(n) for n in numbers])
            dosage_dict["min"] = numbers[0]
            dosage_dict["max"] = numbers[-1]
        else:
            raise ValueError(
                f"Could not extract min and max from dosage: {dosage}")

    else:
        numbers = [n for n in re.findall(r'\d*\.\d+|\d+', dosage)]
        if len(numbers) == 1:
            dosage_dict["min"] = float(numbers[0])
            dosage_dict["max"] = float(numbers[0])

        elif len(numbers) > 1 and '/' not in dosage:
            # if more than 2 numbers and no /, take first and last as min and max
            dosage_dict["min"] = float(numbers[0])
            dosage_dict["max"] = float(numbers[-1])

        # Check if only one number before the unit (and other number is unit reference): '98 mg/70 kg'
        elif len(re.findall(rf"\d+\s*{unit}", dosage)) == 1:
            dosage_dict["min"] = float(numbers[0])
            dosage_dict["max"] = float(numbers[0])
        else:
            raise ValueError(f"Could not extract dosage from: {dosage}")

    # if /kg or /h in dosage -> relative dose
    if re.search(r"/[\s\d]*kg", dosage):
        # if digit before kg, use it as weight reference
        dosage_dict["per_weight_unit"] = "kg"
        weight_ref_match = re.search(r"/\s*(\d+(\.\d+)?)\s*kg", dosage)
        if weight_ref_match:
            dosage_dict["weight_reference"] = float(weight_ref_match.group(1))
        else:
            dosage_dict["weight_reference"] = 1

        if re.search(r"/h|/min", dosage):
            time_unit_match = re.search(r"/(h|min)", dosage)
            if time_unit_match:
                dosage_dict["per_time_unit"] = time_unit_match.group(1)
            dosage_dict["dose_type"] = "relative_weight_time"
        else:
            dosage_dict["dose_type"] = "relative_weight"
    elif re.search(r"/h|/min", dosage):
        time_unit_match = re.search(r"/(h|min)", dosage)
        if time_unit_match:
            dosage_dict["per_time_unit"] = time_unit_match.group(1)
        dosage_dict["dose_type"] = "relative_time"

    else:
        dosage_dict["dose_type"] = "absolute"

    return dosage_dict


def to_mg(value, unit_str):
    if value is None:
        return None
    try:
        v = float(value)
    except Exception:
        return None

    if not unit_str:
        return v

    u = unit_str.lower()
    # normalize microgram variants
    if u in ("µg", "μg", "ug", "microg"):
        return v / 1000.0
    if u in ("mg",):
        return v
    if u in ("g", "gram", "grams"):
        return v * 1000.0
    # fallback: return original value
    return v


def normalize_relative_weight_dosages(minv: float, maxv: float, dosage: float, per_weight_unit: str, factor: int = 70) -> tuple[float, float]:
    try:
        ref = float(dosage) if dosage else None
    except Exception:
        ref = None

    if ref is not None:
        if per_weight_unit == 'kg':
            ref_kg = ref
        elif per_weight_unit == 'g':
            ref_kg = ref / 1000.0
        elif per_weight_unit == 'mg':
            ref_kg = ref / 1_000_000.0
        else:
            ref_kg = ref
    else:
        ref_kg = None

    if ref_kg and ref_kg > 0:
        factor = 70.0 / ref_kg  # Scale to 70 kg person, careful introducing bias
    else:
        factor = 70.0

    min_val = (minv * factor) if minv is not None else None
    max_val = (maxv * factor) if maxv is not None else None
    return min_val, max_val


def remove_several_substances_dosages(df: pd.DataFrame) -> pd.DataFrame:
    """
        Remove papers that have more than 1 substance, except for the allowed combinations:
        * Combination Therapy + any other substance (e.g. "Combination Therapy + LSD", but not "Combination Therapy + Ketamine")
        * Ketamine + S-ketamine (or similar, e.g. "Ketamine (S-ketamine)")
        * Ketamine + Combination Therapy, if there is no other substance in the paper (i.e. the only substances are ketamine and combination therapy, but no other substance)
    """
    combinations_counts = defaultdict(list)
    # find all study ids that have more than 1 substance,
    for study_id, group in df.groupby('Study_ID'):
        substances = group['Substance'].unique()
        if len(substances) > 1:
            # skip if it is just substance + combination therapy
            if len(substances) == 2 and 'Combination Therapy' in substances:
                continue

            # allow ketamine + S-ketamine, but not ketamine + other substance
            elif all('Ketamine' in s for s in substances):
                continue

            elif 'Ketamine' in substances and 'Combination Therapy' in substances:
                substances = [s for s in substances if 'ketamine' not in s.lower(
                ) and s != 'Combination Therapy']
                if len(substances) == 0:
                    continue

            # use a tuple as a hashable dict key
            key = tuple(substances)
            combinations_counts[key].append(study_id)

    combinations_counts = dict(sorted(
        combinations_counts.items(), key=lambda item: len(item[1]), reverse=True))
    
    # Get all combinations and their counts
    for combo, count in combinations_counts.items():
        print(f"{combo}: {count}")

    several_substances_ids = []
    for combo, ids in combinations_counts.items():
        several_substances_ids.extend(ids)

    print(
        f'Total papers with multiple substance: {len(several_substances_ids)}')

    # Remove all papers that have more than 1 substance, except for the allowed combinations
    df_refined = df[~df['Study_ID'].isin(
        several_substances_ids)].reset_index(drop=True)
    print(
        f'Total papers in refined df: {len(df_refined)}')
    removed_dosages = len(df) - \
        len(df_refined)
    total_dosages = len(df)
    excluded_pct = (removed_dosages / total_dosages *
                    100) if total_dosages else 0
    total_papers = len(df['Study_ID'].unique())
    total_papers_refined = len(df_refined['Study_ID'].unique())

    print(
        f'Total papers with multiple substances removed: {total_papers - total_papers_refined} ({(total_papers - total_papers_refined) / total_papers * 100:.1f}%)'
    )

    print(
        f'Total dosages with multiple substances removed: {removed_dosages} ({excluded_pct:.1f}%)')
    return df_refined

