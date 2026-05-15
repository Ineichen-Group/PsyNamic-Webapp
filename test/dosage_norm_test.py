import os
import unittest
from data.dosage_norm import normalize_dosage, extract_dosages, normalize_relative_weight_dosages, to_mg


class DosageNormTest(unittest.TestCase):

    def test_dosage_norm_unit_term(self):
        norm = '10 µg'
        dosages = [
            '10 mcg',
            '10 microg',
            '10 microgram'
        ]
        for dosage in dosages:
            self.assertEqual(normalize_dosage(dosage), norm)

        norm = '5 mg'
        dosage = '5mgs'
        self.assertEqual(normalize_dosage(dosage), norm)

        norm = '10 g'
        dosage = '10 grams'
        self.assertEqual(normalize_dosage(dosage), norm)

        norm = '3 kg'
        dosages = [
            '3 kilogram',
            '3 Kg'
        ]
        for dosage in dosages:
            self.assertEqual(normalize_dosage(dosage), norm)

        norm = '3 h'
        dosages = [
            '3 hours',
            '3 hour',
            '3 hr'
        ]
        for dosage in dosages:
            self.assertEqual(normalize_dosage(dosage), norm)

        norm = '15 min'
        dosage = [
            '15 minutes',
            '15 minute',
            '15 mins'
        ]
        for d in dosage:
            self.assertEqual(normalize_dosage(d), norm)

    def test_clean_dosage(self):
        input_output = {
            '0.5 mg / kg': '0.5 mg/kg',
            'of 5 μg': '5 μg',
            '100 mg / day': '100 mg',
            '100 mg/daily': '100 mg',
            '0.1-0.2 mg / kg / dose': '0.1-0.2 mg/kg',
            '0.1-0.2 mg/kg/dose': '0.1-0.2 mg/kg',
            '1 mg / kg of body weight': '1 mg/kg',
            '0.25 mg / kg bw': '0.25 mg/kg',
            '0.25 mg / kg /bw': '0.25 mg/kg',
            '0.25 mg / kg / bw': '0.25 mg/kg',
            '0.25 mg / kg / bodyweight': '0.25 mg/kg',
            '0.25 mg / kg / bodyweight': '0.25 mg/kg',
            '0.25 mg / kg / body-weight': '0.25 mg/kg',
            '( 200 microg / kg )': '200 µg/kg',
            '.5mg/kg': '0.5 mg/kg',
            '2μg / kg / min': '2 μg/kg/min',
            '(56 mg or 84 mg': '56 or 84 mg',
            '15- or 20-mg ': '15 or 20 mg',
            'one microgram per kilogram': '1 µg/kg',
            '60-, 120-, and 180-mg ': '60, 120, and 180 mg',
            '6.5μg, ': '6.5 μg',
        }

        for inp, outp in input_output.items():
            self.assertEqual(normalize_dosage(inp), outp)

    def test_unit_spelling(self):
        input_output = {
            '0.15 mg kg(-1)': '0.15 mg/kg',
            '2.5 mg.kg(-1) ': '2.5 mg/kg',
            '0.15 mg kg(-1 )': '0.15 mg/kg',
            '0.15 mg kg -1': '0.15 mg/kg',
            '0.15 mg kg-1': '0.15 mg/kg',
            '0.3 mg min(-1)': '0.3 mg/min',
            '0.3 mg min -1': '0.3 mg/min',
            '0.3 mg min-1': '0.3 mg/min',
            '0.3 mg min (-1 )': '0.3 mg/min',
            '1.4 microg kg(-1) min(-1 )': '1.4 µg/kg/min',
            '0.25 mg hour(-1)': '0.25 mg/h',
            '0.25 mg hour -1': '0.25 mg/h',
            '0.25 mg hour-1': '0.25 mg/h',
            '0.1 to 0.5 mg / Kg': '0.1-0.5 mg/kg',
        }
        for inp, outp in input_output.items():
            self.assertEqual(normalize_dosage(inp), outp)

    def test_plus_minus(self):
        input_output = {
            '1,540 ± 920 mg': '1540 mg',
            '1,540 +- 920 mg': '1540 mg',
            '1540 ±920 mg': '1540 mg',
            '1540+-920 mg': '1540 mg',
        }
        for inp, outp in input_output.items():
            self.assertEqual(normalize_dosage(inp), outp)

    def test_with_substance_name(self):
        input_output = {
            "1, 2, or 3 ml SM‐001 per kg": "1, 2, or 3 ml/kg",
            "1 mg DMT kg(-1)": "1 mg/kg",
        }
        for inp, outp in input_output.items():
            self.assertEqual(normalize_dosage(inp), outp)

    def test_with_dot(self):
        input_output = {
            '2.5 mg./kg': '2.5 mg/kg',
            '2.5 mg.kg(-1)': '2.5 mg/kg',
        }
        for inp, outp in input_output.items():
            self.assertEqual(normalize_dosage(inp), outp)

    def test_with_several_units(self):
        input_output = {
            '80 mg or 120 mg ': '80 or 120 mg',
        }
        for inp, outp in input_output.items():
            self.assertEqual(normalize_dosage(inp), outp)

    def test_with_time_and_bracket(self):
        input_output = {
            '(0.01 mg/kg/h)': '0.01 mg/kg/h',
            '0.15-0.3 mg/kg/hr ': '0.15-0.3 mg/kg/h',
            '1.4 microg kg(-1) min(-1) ': '1.4 µg/kg/min',

            '0.25 mg kg(-1) hr(-1) ': '0.25 mg/kg/h',
            '0.3 mg kg-1 h-1 ': '0.3 mg/kg/h',
            '30 mg/hour': '30 mg/h',
        }
        for inp, outp in input_output.items():
            self.assertEqual(normalize_dosage(inp), outp)

    def test_with_several_slash(self):
        input_output = {
            '56/84 mg': '56 or 84 mg',
            '28/56/84 mg': '28, 56, or 84 mg',
            '28 / 56 / 84 mg': '28, 56, or 84 mg',
        }
        for inp, outp in input_output.items():
            self.assertEqual(normalize_dosage(inp), outp)

class DosageExtractTest(unittest.TestCase):
    def test_simple_absolute_dose(self):
        # "10 mg"
        result = extract_dosages("10 mg")
        self.assertEqual(result["min"], 10)
        self.assertEqual(result["max"], 10)
        self.assertEqual(result["unit"], "mg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")

    def test_multiple_numeric_values_with_and(self):
        # "5 , 10 , and 20 µg"
        result = extract_dosages(normalize_dosage("5 , 10 , and 20 µg"))
        self.assertEqual(result["min"], 5)
        self.assertEqual(result["max"], 20)
        self.assertEqual(result["unit"], "µg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")

    def test_multiple_values_with_comma_no_whitespace(self):
        # "1,2,3 mg"
        result = extract_dosages("1,2,3 mg")
        self.assertEqual(result["min"], 1)
        self.assertEqual(result["max"], 3)
        self.assertEqual(result["unit"], "mg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")

    def test_multiple_numeric_values_with_or(self):
        # "10 , 20 , 30 , or 40 mg"
        result = extract_dosages("10 , 20 , 30 , or 40 mg")
        self.assertEqual(result["min"], 10)
        self.assertEqual(result["max"], 40)
        self.assertEqual(result["unit"], "mg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")

    def test_relative_time_or(self):
        # "0.6 or 1 mg / min"
        result = extract_dosages("0.6 or 1 mg / min")
        self.assertEqual(result["min"], 0.6)
        self.assertEqual(result["max"], 1)
        self.assertEqual(result["unit"], "mg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertEqual(result["per_time_unit"], "min")
        self.assertEqual(result["dose_type"], "relative_time")

    def test_relative_weight_multiple_values(self):
        # "10 , 20 , 30 mg/70 kg"
        result = extract_dosages("10 , 20 , 30 mg/70 kg")
        self.assertEqual(result["min"], 10)
        self.assertEqual(result["max"], 30)
        self.assertEqual(result["unit"], "mg")
        self.assertEqual(result["per_weight_unit"], "kg")
        self.assertEqual(result["weight_reference"], 70)
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "relative_weight")

    def test_range_dose_dash(self):
        # "5 - 20 µg"
        result = extract_dosages("5 - 20 µg")
        self.assertEqual(result["min"], 5)
        self.assertEqual(result["max"], 20)
        self.assertEqual(result["unit"], "µg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")

    def test_range_with_to_and_weight(self):
        # "0.5 to 1.25 mg / kg"
        result = extract_dosages("0.5 to 1.25 mg / kg")
        self.assertEqual(result["min"], 0.5)
        self.assertEqual(result["max"], 1.25)
        self.assertEqual(result["unit"], "mg")
        self.assertEqual(result["per_weight_unit"], "kg")
        self.assertEqual(result["weight_reference"], 1)
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "relative_weight")

    def test_no_unit(self):
        # "100"
        result = extract_dosages("100")
        self.assertEqual(result["min"], 100)
        self.assertEqual(result["max"], 100)
        self.assertIsNone(result["unit"])
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")

    def test_starting_with_dot(self):
        # ".5 mg / kg"
        result = extract_dosages(".5 mg / kg")
        self.assertEqual(result["min"], 0.5)
        self.assertEqual(result["max"], 0.5)
        self.assertEqual(result["unit"], "mg")
        self.assertEqual(result["per_weight_unit"], "kg")
        self.assertEqual(result['weight_reference'], 1)
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "relative_weight")

    def test_unit_spelling(self):
        # 0.25 mg kg(-1 ) hr(-1 )
        result = extract_dosages("0.25 mg kg(-1 ) hr(-1 )")
        self.assertEqual(result["min"], 0.25)
        self.assertEqual(result["max"], 0.25)
        self.assertEqual(result["unit"], "mg")
        self.assertEqual(result["per_weight_unit"], "kg")
        self.assertEqual(result["weight_reference"], 1)
        self.assertEqual(result["per_time_unit"], "h")
        self.assertEqual(result["dose_type"], "relative_weight_time")

    def test_unit_spelling_microg(self):
        # 1.4 microg kg(-1 ) min(-1 )
        result = extract_dosages("1.4 microg kg(-1 ) min(-1 )")
        self.assertEqual(result["min"], 1.4)
        self.assertEqual(result["max"], 1.4)
        self.assertEqual(result["unit"], "µg")
        self.assertEqual(result["per_weight_unit"], "kg")
        self.assertEqual(result["weight_reference"], 1)
        self.assertEqual(result["per_time_unit"], "min")

    def test_dosage_per_weight_per_time(self):
        # 2μg / kg / min
        result = extract_dosages("2μg / kg / min")
        self.assertEqual(result["min"], 2)
        self.assertEqual(result["max"], 2)
        self.assertEqual(result["unit"], "μg")
        self.assertEqual(result["per_weight_unit"], "kg")
        self.assertEqual(result["weight_reference"], 1)
        self.assertEqual(result["per_time_unit"], "min")

    def test_range_with_weight_and_dose(self):
        # 0.1‐0.2 mg / kg / dose
        result = extract_dosages("0.1‐0.2 mg / kg / dose")
        self.assertEqual(result["min"], 0.1)
        self.assertEqual(result["max"], 0.2)
        self.assertEqual(result["unit"], "mg")
        self.assertEqual(result["per_weight_unit"], "kg")
        self.assertEqual(result["weight_reference"], 1)
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "relative_weight")

    def test_range_dash(self):
        # 5 - 20 µg
        result = extract_dosages("5 - 20 µg")
        self.assertEqual(result["min"], 5)
        self.assertEqual(result["max"], 20)
        self.assertEqual(result["unit"], "µg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")

    def test_range_with_to(self):
        # '80 mg to 180'
        result = extract_dosages("80 mg to 180")
        self.assertEqual(result["min"], 80)
        self.assertEqual(result["max"], 180)
        self.assertEqual(result["unit"], "mg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")

    def test_or(self):
        # 40 or 60 mg
        result = extract_dosages("40 or 60 mg")
        self.assertEqual(result["min"], 40)
        self.assertEqual(result["max"], 60)
        self.assertEqual(result["unit"], "mg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")

    def test_weird_decimal_character(self):
        # '0·5 mg/kg '
        result = extract_dosages("0·5 mg/kg")
        self.assertEqual(result["min"], 0.5)
        self.assertEqual(result["max"], 0.5)
        self.assertEqual(result["unit"], "mg")
        self.assertEqual(result["per_weight_unit"], "kg")
        self.assertEqual(result["weight_reference"], 1)
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "relative_weight")

    def test_per_weight(self):
        # '98 mg per 70 kg '
        result = extract_dosages("98 mg per 70 kg")
        self.assertEqual(result["min"], 98)
        self.assertEqual(result["max"], 98)
        self.assertEqual(result["unit"], "mg")
        self.assertEqual(result["per_weight_unit"], "kg")
        self.assertEqual(result["weight_reference"], 70)
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "relative_weight")

    def test_mg_kg(self):
        # "20 mg/70 kg "
        result = extract_dosages("20 mg/70 kg")
        self.assertEqual(result["min"], 20)
        self.assertEqual(result["max"], 20)
        self.assertEqual(result["unit"], "mg")
        self.assertEqual(result["per_weight_unit"], "kg")
        self.assertEqual(result["weight_reference"], 70)
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "relative_weight")

    def test_weird_decimal(self):
        # 25 and 125. mg
        result = extract_dosages("25 and 125. mg")
        self.assertEqual(result["min"], 25)
        self.assertEqual(result["max"], 125)
        self.assertEqual(result["unit"], "mg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")

    def test_dosage_twice(self):
        # '56 mg or 84 mg'
        result = extract_dosages("56 mg or 84 mg")
        self.assertEqual(result["min"], 56)
        self.assertEqual(result["max"], 84)
        self.assertEqual(result["unit"], "mg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")

    def test_missing_unit_trailing_whitespace(self):
        # '100 μg and 200 '
        result = extract_dosages("100 μg and 200 ")
        self.assertEqual(result["min"], 100)
        self.assertEqual(result["max"], 200)
        self.assertEqual(result["unit"], "μg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")

    def test_with_slash(self):
        # 56/84 mg
        result = extract_dosages("56/84 mg")
        self.assertEqual(result["min"], 56)
        self.assertEqual(result["max"], 84)
        self.assertEqual(result["unit"], "mg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")

    def test_with_slash_several(self):
        # 28/56/84 mg
        result = extract_dosages("28/56/84 mg")
        self.assertEqual(result["min"], 28)
        self.assertEqual(result["max"], 84)
        self.assertEqual(result["unit"], "mg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")

    def test_with_slash_and_or(self):
        # "1, 2, or 3 ml/kg"
        result = extract_dosages("1, 2, or 3 ml/kg")
        self.assertEqual(result["min"], 1)
        self.assertEqual(result["max"], 3)
        self.assertEqual(result["unit"], "ml")
        self.assertEqual(result["per_weight_unit"], "kg")
        self.assertEqual(result["weight_reference"], 1)
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "relative_weight")

    def test_with_slash(self):
        # "56/84 mg"
        result = extract_dosages("56/84 mg")
        self.assertEqual(result["min"], 56)
        self.assertEqual(result["max"], 84)
        self.assertEqual(result["unit"], "mg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")

        # 28/56/84 mg
        result = extract_dosages("28/56/84 mg")
        self.assertEqual(result["min"], 28)
        self.assertEqual(result["max"], 84)
        self.assertEqual(result["unit"], "mg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")

    def test_relative_weight_time(self):
        # "0.25 mg/kg/h "
        result = extract_dosages("0.25 mg kg(-1 ) hr(-1 )")
        self.assertEqual(result["min"], 0.25)
        self.assertEqual(result["max"], 0.25)
        self.assertEqual(result["unit"], "mg")
        self.assertEqual(result["per_weight_unit"], "kg")
        self.assertEqual(result["weight_reference"], 1)
        self.assertEqual(result["per_time_unit"], "h")
        self.assertEqual(result["dose_type"], "relative_weight_time")

    def test_relative_time_2(self):
        # 0.6 mg/min
        result = extract_dosages("0.6 mg/min")
        self.assertEqual(result["min"], 0.6)
        self.assertEqual(result["max"], 0.6)
        self.assertEqual(result["unit"], "mg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertEqual(result["per_time_unit"], "min")
        self.assertEqual(result["dose_type"], "relative_time")

    def test_relative_time_several(self):
        # 0.6 or 1 mg/min
        result = extract_dosages("0.6 or 1 mg/min")
        self.assertEqual(result["min"], 0.6)
        self.assertEqual(result["max"], 1)
        self.assertEqual(result["unit"], "mg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertEqual(result["per_time_unit"], "min")
        self.assertEqual(result["dose_type"], "relative_time")

    def test_relative_weight_minus_one(self):
        # 2.5 mg.kg(-1)
        result = extract_dosages("2.5 mg.kg(-1)")
        self.assertEqual(result["min"], 2.5)
        self.assertEqual(result["max"], 2.5)
        self.assertEqual(result["unit"], "mg")
        self.assertEqual(result["per_weight_unit"], "kg")
        self.assertEqual(result["weight_reference"], 1)
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "relative_weight")

    def test_absolute_with_slash(self):
        # 56/84 mg
        result = extract_dosages("56/84 mg")
        self.assertEqual(result["min"], 56)
        self.assertEqual(result["max"], 84)
        self.assertEqual(result["unit"], "mg")
        self.assertIsNone(result["per_weight_unit"])
        self.assertIsNone(result["weight_reference"])
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "absolute")


class DosageRelativeWeightNormTest(unittest.TestCase):
    def test_normalize_relative_weight_dosages(self):
        minv = 0.5
        maxv = 0.5
        dosage = 1
        per_weight_unit = "kg"
        factor = 70

        expected_min = 35.0
        expected_max = 35.0

        min_val, max_val = normalize_relative_weight_dosages(
            minv, maxv, dosage, per_weight_unit, factor)

        self.assertEqual(min_val, expected_min)
        self.assertEqual(max_val, expected_max)

    def test_normalize_relative_weight_dosages_with_range(self):
        minv = 0.5
        maxv = 1.0
        dosage = 1
        per_weight_unit = "kg"
        factor = 70

        expected_min = 35.0
        expected_max = 70.0

        min_val, max_val = normalize_relative_weight_dosages(
            minv, maxv, dosage, per_weight_unit, factor)

        self.assertEqual(min_val, expected_min)
        self.assertEqual(max_val, expected_max)


class ToMgTest(unittest.TestCase):
    def test_to_mg(self):
        self.assertEqual(to_mg(1, "mg"), 1)
        self.assertEqual(to_mg(1, "g"), 1000)
        self.assertEqual(to_mg(1, "kg"), 1000000)
        self.assertEqual(to_mg(1, "µg"), 0.001)
        self.assertEqual(to_mg(1, "μg"), 0.001)

    def test_liquid_units(self):
        self.assertEqual(to_mg(1, "ml"), None)
        self.assertEqual(to_mg(1, "l"), None)


if __name__ == '__main__':
    unittest.main()
