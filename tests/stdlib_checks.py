"""Dependency-free checks: python -m unittest discover -s tests -p stdlib_checks.py -v"""
import unittest
from decimal import Decimal
from pathlib import Path
from core.money import units,amount,percentage,money
from localization.strings import tr


class ArithmeticAndAssets(unittest.TestCase):
    def test_exact_decimal(self):self.assertEqual(units('0.1')+units('0.2'),units('0.3'))
    def test_half_up(self):self.assertEqual(units('1.2345'),1235)
    def test_amount(self):self.assertEqual(amount(12345),Decimal('12.345'))
    def test_percent(self):self.assertEqual(percentage(units('10000'),'7.5'),units('750'))
    def test_invalid_numbers(self):
        for number in ('NaN','Infinity','bad'):
            with self.assertRaises(ValueError):units(number)
    def test_invalid_rate(self):
        for rate in ('-1','101'):
            with self.assertRaises(ValueError):percentage(1000,rate)
    def test_iqd_format(self):self.assertEqual(money(units('12500')),'12,500 IQD')
    def test_sorani(self):self.assertEqual(tr('Point of sale'),'کاشێر');self.assertEqual(tr('Products','ar'),'المنتجات')
    def test_icon_and_font(self):
        root=Path(__file__).resolve().parents[1]/'assets'
        self.assertEqual((root/'gas-hunar.ico').read_bytes()[:4],b'\x00\x00\x01\x00')
        self.assertTrue((root/'DejaVuSans.ttf').stat().st_size>100000)
    def test_required_navigation_translations(self):
        for key in ('Dashboard','Point of sale','Products','Tables','Kitchen','Inventory','Expenses','Settings','Backups','Orders'):
            self.assertNotEqual(key,tr(key,'ckb'))
