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

    def test_markdown_is_utf8_and_noindex_follow_in_both_modes(self):
        for indexable in (True, False):
            output = config(indexable, [])
            self.assertIn('AddType text/markdown .md', output)
            self.assertIn('AddCharset UTF-8 .md', output)
            self.assertIn('SetEnvIf Request_URI "\\.md$" seo_markdown', output)
            self.assertIn('Header always set X-Robots-Tag "noindex, follow" env=seo_markdown', output)


if __name__ == '__main__':
    unittest.main()
