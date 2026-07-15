import os
import unittest
from data.dosage_norm import normalize_dosage, extract_dosages, normalize_relative_weight_dosages, to_mg
from data.populate import build_entities, ner_tags_from_row


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

    def test_with_additional_tokens(self):
        # 0.75 mg dmt/kg
        result = extract_dosages("0.75 mg dmt/kg")
        self.assertEqual(result["min"], 0.75)
        self.assertEqual(result["max"], 0.75)
        self.assertEqual(result["unit"], "mg")
        self.assertEqual(result["per_weight_unit"], "kg")
        self.assertEqual(result["weight_reference"], 1)
        self.assertIsNone(result["per_time_unit"])
        self.assertEqual(result["dose_type"], "relative_weight")


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

class TestBuildEntities(unittest.TestCase):

    def test_valid_single_dosage_entity(self):
        tokens = ["0", ".", "75", "mg"]
        tags = ["B-Dosage", "I-Dosage", "I-Dosage", "I-Dosage"]
        probs = [0.9, 0.8, 0.7, 0.6]

        entities = build_entities(tokens, tags, probs)

        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0]["tag"], "Dosage")
        self.assertEqual(entities[0]["start_i"], 0)
        self.assertEqual(entities[0]["span_tokens"], ["0", ".", "75", "mg"])
        self.assertEqual(entities[0]["probs"], probs)

    def test_invalid_i_dosage_after_one_o_is_merged(self):
        tokens = ["0", ".", "75", "mg", "dmt", "/", "kg"]
        tags = [
            "B-Dosage", "I-Dosage", "I-Dosage", "I-Dosage",
            "O",
            "I-Dosage", "I-Dosage"
        ]
        probs = [1.0] * len(tokens)

        entities = build_entities(tokens, tags, probs, max_o_gap=2)

        self.assertEqual(len(entities), 1)
        self.assertEqual(
            entities[0]["span_tokens"],
            ["0", ".", "75", "mg", "dmt", "/", "kg"]
        )


    def test_several_interruptions(self):
        tokens = ["0", ",", "75", "or", "0", ".", "85", "mg"]
        tags = [
            "B-Dosage", "O", "I-Dosage",
            "O", "I-Dosage",
            "O", "I-Dosage", "I-Dosage"]
        probs = [1.0] * len(tokens)
        entities = build_entities(tokens, tags, probs, max_o_gap=2)
        print(entities)
        # check only 1 entity
        self.assertEqual(len(entities), 1)
        self.assertEqual(
            entities[0]["span_tokens"],
            ["0", ",", "75", "or", "0", ".", "85", "mg"]
        )

    def test_invalid_number_of_tags_tokens(self):
        tokens = ["0", ".", "75", "mg"]
        tags = ["B-Dosage", "I-Dosage", "I-Dosage"]
        probs = [1.0] * len(tokens)

        with self.assertRaises(ValueError):
            build_entities(tokens, tags, probs)

    def test_invalid_i_dosage_after_three_o_tokens_is_not_merged(self):
        tokens = ["0", ".", "75", "mg", "of", "dmt", "base", "/", "kg"]
        tags = [
            "B-Dosage", "I-Dosage", "I-Dosage", "I-Dosage",
            "O", "O", "O",
            "I-Dosage", "I-Dosage"
        ]
        probs = [1.0] * len(tokens)

        entities = build_entities(tokens, tags, probs, max_o_gap=2)

        self.assertEqual(len(entities), 2)

        self.assertEqual(
            entities[0]["span_tokens"],
            ["0", ".", "75", "mg"]
        )

        self.assertEqual(
            entities[1]["span_tokens"],
            ["/", "kg"]
        )

    def test_invalid_i_at_sequence_start_becomes_new_entity(self):
        tokens = ["/", "kg"]
        tags = ["I-Dosage", "I-Dosage"]
        probs = [0.4, 0.5]

        entities = build_entities(tokens, tags, probs)

        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0]["tag"], "Dosage")
        self.assertEqual(entities[0]["start_i"], 0)
        self.assertEqual(entities[0]["span_tokens"], ["/", "kg"])
        self.assertEqual(entities[0]["probs"], probs)

    def test_invalid_i_other_label_not_merged_into_dosage(self):
        tokens = ["0", ".", "75", "mg", "dmt", "foo"]
        tags = [
            "B-Dosage", "I-Dosage", "I-Dosage", "I-Dosage",
            "O",
            "I-Drug"
        ]
        probs = [1.0] * len(tokens)

        entities = build_entities(tokens, tags, probs, max_o_gap=2)

        self.assertEqual(len(entities), 2)
        self.assertEqual(entities[0]["tag"], "Dosage")
        self.assertEqual(entities[0]["span_tokens"], ["0", ".", "75", "mg"])

        self.assertEqual(entities[1]["tag"], "Drug")
        self.assertEqual(entities[1]["span_tokens"], ["foo"])

    def test_valid_two_separate_dosages(self):
        tokens = ["0", ".", "6", "and", "0", ".", "85", "mg"]
        tags = [
            "B-Dosage", "I-Dosage", "I-Dosage",
            "O",
            "B-Dosage", "I-Dosage", "I-Dosage", "I-Dosage"
        ]
        probs = [1.0] * len(tokens)

        entities = build_entities(tokens, tags, probs)

        self.assertEqual(len(entities), 2)

        self.assertEqual(
            entities[0]["span_tokens"],
            ["0", ".", "6"]
        )
        self.assertEqual(
            entities[1]["span_tokens"],
            ["0", ".", "85", "mg"]
            
        )

    def test_remove_title_abstract_delimiter(self):
        tokens = ['treatment', '-', 'resistant', 'depression', '.', '^']
        tags = ['B-Application', 'I-Application', 'I-Application', 'I-Application', 'I-Application', 'I-Application ']

        probs = [1.0] * len(tokens)

        entities = build_entities(tokens, tags, probs)
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0]["span_tokens"], ['treatment', '-', 'resistant', 'depression'])


    def test_real_example(self):
        tokens = ['ketamine', 'as', 'an', 'adjunctive', 'therapy', 'for', 'major', 'depression', '-', 'a', 'randomised', 'controlled', 'pragmatic', 'pilot', 'trial', '(', 'karma', '-', 'dep', 'trial', ')', '.', '^', 'background', ':', 'depression', 'is', 'a', 'common', 'psychiatric', 'disorder', 'that', 'has', 'become', 'the', 'leading', 'cause', 'of', 'disability', 'worldwide', '.', 'the', 'standard', 'medical', 'care', 'for', 'depression', 'over', 'the', 'past', '50', 'years', 'has', 'focused', 'on', 'monoamine', 'neurotransmitters', '.', 'these', 'treatments', 'can', 'take', 'weeks', 'to', 'take', 'effect', ',', 'highlighting', 'the', 'need', 'for', 'novel', 'treatment', 'strategies', '.', 'one', 'such', 'approach', 'may', 'be', 'ketamine', '.', 'ketamine', 'acts', 'as', 'an', 'antagonist', 'of', 'the', 'n', '-', 'methyl', '-', 'd', '-', 'asparate', 'receptor', 'and', 'thus', 'targets', 'the', 'excitatory', 'amino', 'acid', 'neurotransmitter', 'glutamate', '.', 'interestingly', ',', 'at', 'sub', '-', 'anaesthetic', 'doses', ',', 'a', 'single', 'infusion', 'of', 'ketamine', 'can', 'elicit', 'a', 'rapid', ',', 'though', 'transient', ',', 'antidepressant', 'response', '.', 'methods', ':', 'the', 'aim', 'of', 'this', 'study', 'was', 'to', 'conduct', 'a', 'pragmatic', 'randomised', 'controlled', 'pilot', 'trial', 'of', 'four', 'once', '-', 'weekly', 'ketamine', 'infusions', 'as', 'an', 'adjunctive', 'therapy', 'for', 'depression', '.', 'the', 'main', 'objective', 'was', 'to', 'assess', 'trial', 'procedures', 'to', 'inform', 'a', 'future', 'definitive', 'trial', '.', 'the', 'primary', 'clinical', 'outcome', 'was', 'the', '24', '-', 'item', 'hamilton', 'rating', 'scale', 'for', 'depression', '(', 'hrsd', '-', '24', ')', '.', 'trial', 'participants', 'were', 'patients', 'admitted', 'to', 'st', 'patrick', "'", 's', 'mental', 'health', 'services', 'for', 'treatment', 'of', 'a', 'depressive', 'episode', '.', 'they', 'underwent', 'usual', 'inpatient', 'care', 'as', 'prescribed', 'by', 'their', 'treating', 'team', '.', 'consented', 'participants', 'were', 'randomly', 'allocated', 'to', 'a', 'four', '-', 'week', 'course', 'of', 'either', 'once', '-', 'weekly', 'ketamine', '(', '0', '.', '5mg', '/', 'kg', ')', 'or', 'midazolam', '(', '0', '.', '045mg', '/', 'kg', ')', 'infusions', 'given', 'over', '40', 'minutes', 'and', 'with', '12', 'weeks', 'follow', '-', 'up', '.', 'results', ':', 'in', 'total', ',', '1581', 'admissions', 'to', 'st', 'patrick', "'", 's', 'hospital', 'were', 'assessed', 'for', 'eligibility', 'over', 'nine', 'months', ',', 'with', '125', '(', '8', '%', ')', 'meeting', 'criteria', ',', 'with', '25', '(', '20', '%', ')', 'providing', 'consent', '.', 'in', 'total', ',', '13', 'were', 'randomly', 'assigned', 'to', 'the', 'ketamine', 'arm', 'and', '12', 'to', 'the', 'midazolam', 'arm', '.', 'there', 'were', 'no', 'major', 'differences', 'in', 'hrsd', '-', '24', 'scores', 'between', 'the', 'two', 'groups', '.', 'the', 'infusions', 'were', 'generally', 'safe', 'and', 'well', 'tolerated', '.', 'conclusions', ':', 'this', 'is', 'the', 'first', 'pragmatic', 'pilot', 'trial', 'of', 'adjunctive', 'serial', 'ketamine', 'infusions', 'for', 'hospitalised', 'depression', ',', 'an', 'important', 'possible', 'use', 'of', 'ketamine', '.', 'this', 'study', 'suggests', 'that', 'a', 'definitive', 'trial', 'of', 'adjunctive', 'ketamine', 'is', 'feasible', '.', 'trial', 'registration', ':', 'clinicaltrials', '.', 'gov', 'nct03256162', '21', '/', '08', '/', '2017', ';', 'eudract', '2016', '-', '004764', '-', '18', '30', '/', '11', '/', '2016', '.']
        tags = ['O', 'O', 'O', 'O', 'O', 'O', 'B-Application area', 'I-Application area', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'B-Application area', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'B-Application area', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'B-Dosage', 'I-Dosage', 'I-Dosage', 'I-Dosage', 'I-Dosage', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O']
        probs = [1.0] * len(tokens)
        entities = build_entities(tokens, tags, probs)
        self.assertEqual(len(entities), 4)
        self.assertEqual(entities[3]["span_tokens"], ['0', '.', '5mg', '/', 'kg'])
    
    def realt_data_2(self):
        tokens = ['ketamine', ':', 'behavioral', 'effects', 'of', 'subanesthetic', 'doses', '.', '^', 'effects', 'of', 'subanesthetic', 'doses', 'of', 'ketamine', '(', '0', '.', '25', 'and', '0', '.', '5', 'mg', '/', 'kg', ')', 'on', 'memory', ',', 'cognition', ',', 'psychomotor', 'function', ',', 'subjective', 'moods', ',', 'and', 'incidence', 'of', 'adverse', 'reactions', 'were', 'investigated', 'in', '34', 'healthy', 'young', 'volunteers', '.', 'the', 'drug', 'caused', 'impairment', 'of', 'immediate', 'and', 'delayed', 'recall', '.', 'most', 'of', 'the', 'impairment', 'was', 'due', 'to', 'interference', 'with', 'retrieval', 'processes', '.', 'recovery', 'was', 'virtually', 'complete', '60', 'minutes', 'after', 'administration', '.', 'the', 'incidence', 'of', 'adverse', 'reactions', 'was', 'high', '.', 'benzodiazepines', 'need', 'to', 'be', 'administered', 'even', 'when', 'ketamine', 'is', 'used', 'in', 'subanesthetic', 'doses', '.']
        tags = ['O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'B-Dosage', 'I-Dosage', 'I-Dosage', 'I-Dosage', 'I-Dosage', 'I-Dosage', 'I-Dosage', 'I-Dosage', 'I-Dosage', 'I-Dosage', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O']
        entities = build_entities(tokens, tags, [1.0] * len(tokens))
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0]["span_tokens"], ['0', '.', '25', 'and', '0', '.', '5', 'mg', '/', 'kg'])
        

        
class TestNerTagsFromRow(unittest.TestCase):
    def test_csv_offsets_single_entity(self):
        row = {
            "tokens": ["0", ".", "75", "mg", "ketamine"],
            "offsets": [[0, 1], [1, 2], [2, 4], [5, 7], [8, 16]],
            "ner_tags": ["B-Dosage", "I-Dosage", "I-Dosage", "I-Dosage", "O"],
            "probabilities": [0.9, 0.8, 0.7, 0.6, 0.99],
            "text": "0.75 mg ketamine",
        }

        results = ner_tags_from_row(
            row=row,
            pred_text='',
            manual=False,
            use_offsets=True,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["tag"], "Dosage")
        self.assertEqual(results[0]["start_id"], 0)
        self.assertEqual(results[0]["end_id"], 7)
        self.assertEqual(results[0]["text"], "0.75 mg")
        self.assertAlmostEqual(results[0]["probability"], 0.75)
        self.assertEqual(results[0]["span_tokens"], ["0", ".", "75", "mg"])

    def test_csv_offsets_two_entities(self):
        row = {
            "tokens": ["ketamine", "0", ".", "75", "mg"],
            "offsets": [[0, 8], [9, 10], [10, 11], [11, 13], [14, 16]],
            "ner_tags": ["B-Drug", "B-Dosage", "I-Dosage", "I-Dosage", "I-Dosage"],
            "probabilities": [0.95, 0.9, 0.8, 0.7, 0.6],
            "text": "ketamine 0.75 mg",
        }

        results = ner_tags_from_row(
            row=row,
            pred_text='',
            manual=False,
            use_offsets=True,
        )

        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]["tag"], "Drug")
        self.assertEqual(results[0]["start_id"], 0)
        self.assertEqual(results[0]["end_id"], 8)
        self.assertEqual(results[0]["text"], "ketamine")
        self.assertAlmostEqual(results[0]["probability"], 0.95)

        self.assertEqual(results[1]["tag"], "Dosage")
        self.assertEqual(results[1]["start_id"], 9)
        self.assertEqual(results[1]["end_id"], 16)
        self.assertEqual(results[1]["text"], "0.75 mg")
        self.assertAlmostEqual(results[1]["probability"], 0.75)

    def test_csv_offsets_with_dosage_gap_tokens(self):
        row = {
            "tokens": ["0", ".", "75", "mg", "dmt", "/", "kg"],
            "offsets": [[0, 1], [1, 2], [2, 4], [5, 7], [8, 11], [11, 12], [12, 14]],
            "ner_tags": [
                "B-Dosage", "I-Dosage", "I-Dosage", "I-Dosage",
                "O",
                "I-Dosage", "I-Dosage",
            ],
            "probabilities": [1.0] * 7,
            "text": "0.75 mg dmt/kg",
        }

        results = ner_tags_from_row(
            row=row,
            pred_text='',
            manual=False,
            use_offsets=True,
            max_o_gap=2,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["tag"], "Dosage")
        self.assertEqual(results[0]["start_id"], 0)
        self.assertEqual(results[0]["end_id"], 14)
        self.assertEqual(results[0]["text"], "0.75 mg dmt/kg")
        self.assertEqual(
            results[0]["span_tokens"],
            ["0", ".", "75", "mg", "dmt", "/", "kg"],
        )

    def test_manual_probabilities_are_all_one(self):
        row = {
            "tokens": ["ketamine"],
            "offsets": [[0, 8]],
            "ner_tags": ["B-Drug"],
            "probabilities": [0.2],
            "text": "ketamine",
        }

        results = ner_tags_from_row(
            row=row,
            pred_text='',
            manual=True,
            use_offsets=True,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["tag"], "Drug")
        self.assertEqual(results[0]["probability"], 1.0)

    def test_stringified_csv_columns_are_parsed(self):
        row = {
            "tokens": "['ketamine']",
            "offsets": "[[0, 8]]",
            "ner_tags": "['B-Drug']",
            "probabilities": "[0.42]",
            "text": "ketamine",
        }

        results = ner_tags_from_row(
            row=row,
            pred_text='',
            manual=False,
            use_offsets=True,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["tag"], "Drug")
        self.assertEqual(results[0]["start_id"], 0)
        self.assertEqual(results[0]["end_id"], 8)
        self.assertEqual(results[0]["text"], "ketamine")
        self.assertAlmostEqual(results[0]["probability"], 0.42)

    def test_jsonl_without_offsets_uses_find_pos(self):
        pred_text = "ketamine 0.75 mg"
        row = {
            "tokens": ["ketamine", "0", ".", "75", "mg"],
            "ner_tags": ["O", "B-Dosage", "I-Dosage", "I-Dosage", "I-Dosage"],
            "probabilities": [0.99, 0.9, 0.8, 0.7, 0.6],
        }

        results = ner_tags_from_row(
            row=row,
            pred_text=pred_text,
            manual=False,
            use_offsets=False,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["tag"], "Dosage")
        self.assertEqual(results[0]["start_id"], 9)
        self.assertEqual(results[0]["end_id"], 16)
        self.assertEqual(results[0]["text"], "0.75 mg")
        self.assertAlmostEqual(results[0]["probability"], 0.75)

    def test_no_entities_returns_empty_list(self):
        pred_text = "no dosage here"
        row = {
            "tokens": ["no", "dosage", "here"],
            "offsets": [[0, 2], [3, 9], [10, 14]],
            "ner_tags": ["O", "O", "O"],
            "probabilities": [1.0, 1.0, 1.0],
        }

        results = ner_tags_from_row(
            row=row,
            pred_text=pred_text,
            manual=False,
            use_offsets=True,
        )

        self.assertEqual(results, [])

    def test_real_data(self):
        pred_text = 'Ketamine: behavioral effects of subanesthetic doses.^ Effects of subanesthetic doses of ketamine (0.25 and 0.5 mg/kg) on memory, cognition, psychomotor function, subjective moods, and incidence of adverse reactions were investigated in 34 healthy young volunteers. The drug caused impairment of immediate and delayed recall. Most of the impairment was due to interference with retrieval processes. Recovery was virtually complete 60 minutes after administration. The incidence of adverse reactions was high. Benzodiazepines need to be administered even when ketamine is used in subanesthetic doses.'
        row = {'id': 3988972, 'text': 'Ketamine: behavioral effects of subanesthetic doses.^\nEffects of subanesthetic doses of ketamine (0.25 and 0.5 mg/kg) on memory, cognition, psychomotor function, subjective moods, and incidence of adverse reactions were investigated in 34 healthy young volunteers. The drug caused impairment of immediate and delayed recall. Most of the impairment was due to interference with retrieval processes. Recovery was virtually complete 60 minutes after administration. The incidence of adverse reactions was high. Benzodiazepines need to be administered even when ketamine is used in subanesthetic doses.', 'tokens': "['ketamine', ':', 'behavioral', 'effects', 'of', 'subanesthetic', 'doses', '.', '^', 'effects', 'of', 'subanesthetic', 'doses', 'of', 'ketamine', '(', '0', '.', '25', 'and', '0', '.', '5', 'mg', '/', 'kg', ')', 'on', 'memory', ',', 'cognition', ',', 'psychomotor', 'function', ',', 'subjective', 'moods', ',', 'and', 'incidence', 'of', 'adverse', 'reactions', 'were', 'investigated', 'in', '34', 'healthy', 'young', 'volunteers', '.', 'the', 'drug', 'caused', 'impairment', 'of', 'immediate', 'and', 'delayed', 'recall', '.', 'most', 'of', 'the', 'impairment', 'was', 'due', 'to', 'interference', 'with', 'retrieval', 'processes', '.', 'recovery', 'was', 'virtually', 'complete', '60', 'minutes', 'after', 'administration', '.', 'the', 'incidence', 'of', 'adverse', 'reactions', 'was', 'high', '.', 'benzodiazepines', 'need', 'to', 'be', 'administered', 'even', 'when', 'ketamine', 'is', 'used', 'in', 'subanesthetic', 'doses', '.']", 'offsets': '[[0, 8], [8, 9], [10, 20], [21, 28], [29, 31], [32, 45], [46, 51], [51, 52], [52, 53], [54, 61], [62, 64], [65, 78], [79, 84], [85, 87], [88, 96], [97, 98], [98, 99], [99, 100], [100, 102], [103, 106], [107, 108], [108, 109], [109, 110], [111, 113], [113, 114], [114, 116], [116, 117], [118, 120], [121, 127], [127, 128], [129, 138], [138, 139], [140, 151], [152, 160], [160, 161], [162, 172], [173, 178], [178, 179], [180, 183], [184, 193], [194, 196], [197, 204], [205, 214], [215, 219], [220, 232], [233, 235], [236, 238], [239, 246], [247, 252], [253, 263], [263, 264], [265, 268], [269, 273], [274, 280], [281, 291], [292, 294], [295, 304], [305, 308], [309, 316], [317, 323], [323, 324], [325, 329], [330, 332], [333, 336], [337, 347], [348, 351], [352, 355], [356, 358], [359, 371], [372, 376], [377, 386], [387, 396], [396, 397], [398, 406], [407, 410], [411, 420], [421, 429], [430, 432], [433, 440], [441, 446], [447, 461], [461, 462], [463, 466], [467, 476], [477, 479], [480, 487], [488, 497], [498, 501], [502, 506], [506, 507], [508, 523], [524, 528], [529, 531], [532, 534], [535, 547], [548, 552], [553, 557], [558, 566], [567, 569], [570, 574], [575, 577], [578, 591], [592, 597], [597, 598]]', 'ner_tags': "['O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'B-Dosage', 'I-Dosage', 'I-Dosage', 'I-Dosage', 'I-Dosage', 'I-Dosage', 'I-Dosage', 'I-Dosage', 'I-Dosage', 'I-Dosage', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O']", 'probabilities': '[0.9994262456893921, 0.9996126294136047, 0.9996404647827148, 0.9996852874755859, 0.9998235106468201, 0.9997062087059021, 0.9996581077575684, 0.9995179176330566, 0.98326575756073, 0.9997742772102356, 0.9997884631156921, 0.9996727705001831, 0.9993488192558289, 0.9996181726455688, 0.9989672899246216, 0.9931127429008484, 0.9831900596618652, 0.9759194254875183, 0.9660006761550903, 0.9521774649620056, 0.6867673993110657, 0.9782046675682068, 0.9736621975898743, 0.9749865531921387, 0.9795274138450623, 0.9797530174255371, 0.9993625283241272, 0.9998542070388794, 0.9994394183158875, 0.9997987151145935, 0.9995531439781189, 0.9998345375061035, 0.9997779726982117, 0.9997755885124207, 0.9998387098312378, 0.999761164188385, 0.999457061290741, 0.999832034111023, 0.9998365640640259, 0.9997848868370056, 0.9998370409011841, 0.9997350573539734, 0.9997475743293762, 0.9998434782028198, 0.9998651742935181, 0.9997836947441101, 0.9994879961013794, 0.9996469020843506, 0.9996607303619385, 0.999774158000946, 0.9998786449432373, 0.9998445510864258, 0.999799907207489, 0.999846339225769, 0.9997984766960144, 0.9998798370361328, 0.9997269511222839, 0.9997872710227966, 0.9997995495796204, 0.9998219609260559, 0.999881386756897, 0.9998352527618408, 0.9998049139976501, 0.9998726844787598, 0.9998452663421631, 0.9998531341552734, 0.9998037219047546, 0.9998281002044678, 0.9998382329940796, 0.9998593330383301, 0.9997856020927429, 0.9998132586479187, 0.9998754262924194, 0.999836802482605, 0.999872088432312, 0.9998102784156799, 0.9998531341552734, 0.9997172951698303, 0.9997332692146301, 0.9998124241828918, 0.9998127818107605, 0.9998818635940552, 0.9998958110809326, 0.9998511075973511, 0.9998514652252197, 0.9997958540916443, 0.9998137354850769, 0.9998654127120972, 0.9998346567153931, 0.9998706579208374, 0.9998051524162292, 0.9998377561569214, 0.9998369216918945, 0.9998608827590942, 0.9998602867126465, 0.999806821346283, 0.9998284578323364, 0.9996910095214844, 0.9996597766876221, 0.9997379183769226, 0.9997093081474304, 0.9997031092643738, 0.9996907711029053, 0.9997428059577942]', 'model': 'vera-bernhard'}
        
        ner_tags = ner_tags_from_row(
            row=row,
            pred_text=pred_text,
            manual=False,
            use_offsets=True,
        )
        self.assertEqual(len(ner_tags), 1)
        self.assertEqual(ner_tags[0]["tag"], "Dosage")
        self.assertEqual(ner_tags[0]["text"], "0.25 and 0.5 mg/kg")
        self.assertEqual(ner_tags[0]["span_tokens"], ["0", ".", "25", "and", "0", ".", "5", "mg", "/", "kg"])
        print(ner_tags[0]["start_id"], ner_tags[0]["end_id"])
        self.assertEqual(pred_text[ner_tags[0]["start_id"]:ner_tags[0]["end_id"]], "0.25 and 0.5 mg/kg")
        self.assertEqual(row['text'][ner_tags[0]["start_id"]:ner_tags[0]["end_id"]], "0.25 and 0.5 mg/kg")
        
        
if __name__ == "__main__":
    unittest.main()
