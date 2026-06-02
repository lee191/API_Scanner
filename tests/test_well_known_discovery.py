import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from route_api_discovery import parse_robots_txt, parse_sitemap_xml


class RobotsParsingTests(unittest.TestCase):
    def test_extracts_disallow_allow_and_sitemap(self):
        text = (
            "User-agent: *\n"
            "Disallow: /admin/\n"
            "Allow: /public/data\n"
            "Disallow: /search/*?q=\n"
            "Sitemap: https://example.com/sitemap.xml\n"
        )
        paths, sitemaps = parse_robots_txt(text)
        self.assertIn("/admin/", paths)
        self.assertIn("/public/data", paths)
        self.assertNotIn("/search/*?q=", paths)  # wildcard excluded
        self.assertIn("https://example.com/sitemap.xml", sitemaps)


class SitemapParsingTests(unittest.TestCase):
    def test_extracts_loc_urls(self):
        text = (
            '<?xml version="1.0"?>'
            '<urlset><url><loc>https://example.com/p/1</loc></url>'
            '<url><loc>https://example.com/p/2</loc></url></urlset>'
        )
        locs, nested = parse_sitemap_xml(text)
        self.assertIn("https://example.com/p/1", locs)
        self.assertIn("https://example.com/p/2", locs)
        self.assertEqual(nested, [])

    def test_detects_nested_sitemapindex(self):
        text = (
            '<sitemapindex><sitemap><loc>https://example.com/sub.xml</loc></sitemap>'
            '</sitemapindex>'
        )
        locs, nested = parse_sitemap_xml(text)
        self.assertIn("https://example.com/sub.xml", nested)


from unittest.mock import patch

from route_api_discovery import (
    discover_well_known,
    build_url_scope,
    FetchResult,
    Candidate,
)


class DiscoverWellKnownTests(unittest.TestCase):
    def _scope(self, url):
        return build_url_scope(url, include_subdomains=True, excluded_hostnames=())

    def test_collects_sitemap_locs_and_robots_paths(self):
        robots = "Disallow: /admin/\nSitemap: https://example.com/sitemap.xml\n"
        sitemap = "<urlset><url><loc>https://example.com/p/1</loc></url></urlset>"

        def fake_fetch(url, **kwargs):
            if url.endswith("/robots.txt"):
                return FetchResult(url=url, status_code=200, text=robots, success=True, length=len(robots))
            if url.endswith("/sitemap.xml"):
                return FetchResult(url=url, status_code=200, text=sitemap, success=True, length=len(sitemap))
            return FetchResult(url=url, status_code=404, text="", success=False, length=0)

        page_bucket = {}
        with patch("route_api_discovery.fetch_text", side_effect=fake_fetch):
            discover_well_known(
                target_url="https://example.com",
                scope=self._scope("https://example.com"),
                timeout=5.0,
                headers={},
                header_origin_url="https://example.com",
                verify_ssl=True,
                proxy_url="",
                page_bucket=page_bucket,
            )

        urls = {c.url for c in page_bucket.values()}
        self.assertIn("https://example.com/admin/", urls)
        self.assertIn("https://example.com/p/1", urls)

    def test_respects_out_of_scope_filter(self):
        robots = "Disallow: /ok/\n"
        sitemap = "<urlset><url><loc>https://evil.com/p/1</loc></url></urlset>"

        def fake_fetch(url, **kwargs):
            if url.endswith("/robots.txt"):
                return FetchResult(url=url, status_code=200, text=robots, success=True, length=len(robots))
            if url.endswith("/sitemap.xml"):
                return FetchResult(url=url, status_code=200, text=sitemap, success=True, length=len(sitemap))
            return FetchResult(url=url, status_code=404, text="", success=False, length=0)

        page_bucket = {}
        with patch("route_api_discovery.fetch_text", side_effect=fake_fetch):
            discover_well_known(
                target_url="https://example.com",
                scope=self._scope("https://example.com"),
                timeout=5.0,
                headers={},
                header_origin_url="https://example.com",
                verify_ssl=True,
                proxy_url="",
                page_bucket=page_bucket,
            )

        urls = {c.url for c in page_bucket.values()}
        self.assertNotIn("https://evil.com/p/1", urls)
        self.assertIn("https://example.com/ok/", urls)


if __name__ == "__main__":
    unittest.main()
