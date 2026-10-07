import unittest

from apache_config import config


class ApacheQueryRobotsTests(unittest.TestCase):
    def test_indexable_mode_noindexes_functional_queries(self):
        output = config(True, [])
        self.assertIn('(q|search|sort|brand|filter|page|category)', output)
        self.assertIn('Header always set X-Robots-Tag "noindex, follow" env=seo_search', output)
        self.assertNotIn('Header always set X-Robots-Tag "noindex, nofollow"', output)

    def test_preview_mode_remains_sitewide_noindex(self):
        output = config(False, [])
        self.assertIn('Header always set X-Robots-Tag "noindex, nofollow"', output)


if __name__ == '__main__':
    unittest.main()
