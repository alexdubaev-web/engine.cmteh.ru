import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import import_stock
from pipeline_io import pipeline_lock


class StockPairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'data').mkdir()
        self.stock_path = self.root / 'data/stock.json'
        self.commerce_path = self.root / 'data/commerce.json'
        self.stock_path.write_text(json.dumps({'items': {'a': {'quantity': 1}}}), encoding='utf-8')
        self.commerce_path.write_text(json.dumps({'availability': {'a': 'InStock'}}), encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def test_second_replace_failure_restores_both_stock_artifacts(self):
        stock = {'items': {'a': {'quantity': 0}}}
        commerce = {'availability': {'a': 'OutOfStock'}}
        original = os.replace
        def fail_commerce(source, target):
            if Path(target) == self.commerce_path:
                raise OSError('injected second artifact failure')
            return original(source, target)
        with pipeline_lock(self.root):
            with self.assertRaises(OSError):
                import_stock.publish_stock_pair(self.root, stock, commerce, replace=fail_commerce)
        self.assertEqual(json.loads(self.stock_path.read_text(encoding='utf-8'))['items']['a']['quantity'], 1)
        self.assertEqual(json.loads(self.commerce_path.read_text(encoding='utf-8'))['availability']['a'], 'InStock')

    def test_build_reader_waits_until_pair_publish_is_complete(self):
        first_replaced = threading.Event()
        reader_started = threading.Event()
        reader_done = threading.Event()
        errors = []
        original = os.replace
        def pause_after_stock(source, target):
            result = original(source, target)
            if Path(target) == self.stock_path:
                first_replaced.set()
                if not reader_started.wait(2):
                    raise TimeoutError('reader did not start')
                if reader_done.wait(0.05):
                    raise AssertionError('reader passed the pipeline lock during pair publication')
            return result
        def writer():
            try:
                with pipeline_lock(self.root):
                    import_stock.publish_stock_pair(self.root, {'items': {'a': {'quantity': 0}}},
                                                    {'availability': {'a': 'OutOfStock'}},replace=pause_after_stock)
            except BaseException as error:
                errors.append(error)
        def reader():
            first_replaced.wait(2)
            reader_started.set()
            try:
                with pipeline_lock(self.root):
                    quantity = json.loads(self.stock_path.read_text(encoding='utf-8'))['items']['a']['quantity']
                    availability = json.loads(self.commerce_path.read_text(encoding='utf-8'))['availability']['a']
                    self.assertEqual((quantity, availability), (0, 'OutOfStock'))
            except BaseException as error:
                errors.append(error)
            finally:
                reader_done.set()
        writer_thread = threading.Thread(target=writer)
        reader_thread = threading.Thread(target=reader)
        writer_thread.start();reader_thread.start()
        writer_thread.join(5);reader_thread.join(5)
        self.assertFalse(writer_thread.is_alive() or reader_thread.is_alive())
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
