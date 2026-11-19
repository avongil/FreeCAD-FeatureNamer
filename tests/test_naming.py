"""Tests for the pure naming rules (run with pytest or python -m unittest)."""

import unittest

from freecad.FeatureNamer.core import naming as n

PF = [pf for _, pf in n.DEFAULT_POSTFIXES]


class DefaultLabel(unittest.TestCase):
    def test_same_as_name(self):
        self.assertTrue(n.is_default_label("Pad003", "Pad003"))

    def test_copy_counter(self):
        self.assertTrue(n.is_default_label("Pad", "Pad003"))
        self.assertTrue(n.is_default_label("Pad007", "Pad003"))

    def test_custom(self):
        self.assertFalse(n.is_default_label("Pad base plate", "Pad003"))
        self.assertFalse(n.is_default_label("OutsideMoat_SKT", "Sketch"))


class Postfix(unittest.TestCase):
    def test_added(self):
        self.assertEqual(n.add_postfix("OutsideMoat", "_SKT"), "OutsideMoat_SKT")

    def test_not_doubled(self):
        self.assertEqual(n.add_postfix("Boss_skt", "_SKT"), "Boss_skt")

    def test_empty(self):
        self.assertEqual(n.add_postfix("  ", "_SKT"), "")
        self.assertEqual(n.add_postfix("Boss", ""), "Boss")

    def test_strip_longest(self):
        # _SSWP must win over _SWP
        self.assertEqual(n.strip_postfix("Cut_SSWP", PF), "Cut")
        self.assertEqual(n.strip_postfix("OutsideMoat_SKT", PF), "OutsideMoat")
        self.assertEqual(n.strip_postfix("_SKT", PF), "_SKT")
        self.assertEqual(n.strip_postfix("Plain", PF), "Plain")


class Derive(unittest.TestCase):
    def test_pad_from_sketch(self):
        self.assertEqual(n.derive_label("OutsideMoat_SKT", PF, "_PAD"), "OutsideMoat_PAD")

    def test_fillet_from_pad(self):
        self.assertEqual(n.derive_label("Lid_PAD", PF, "_FIL"), "Lid_FIL")

    def test_base_without_postfix(self):
        self.assertEqual(n.derive_label("Lid", PF, "_PKT"), "Lid_PKT")

    def test_no_postfix_means_no_name(self):
        self.assertIsNone(n.derive_label("Lid_PAD", PF, ""))


class Storage(unittest.TestCase):
    def test_round_trip(self):
        raw = n.format_postfixes(n.DEFAULT_POSTFIXES)
        self.assertEqual(n.parse_postfixes(raw), n.DEFAULT_POSTFIXES)

    def test_skips_junk(self):
        self.assertEqual(n.parse_postfixes("junk\n=_X\n A = _B \n"), [("A", "_B")])


if __name__ == "__main__":
    unittest.main()
