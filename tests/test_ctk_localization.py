import unittest

from route_api_discovery_ctk import CtkDiscoveryApp, _t


class CtkLocalizationTests(unittest.TestCase):
    def test_runtime_status_labels_are_localized(self) -> None:
        self.assertEqual(_t("ko", "req_count", n=0), "요청: 0")
        self.assertEqual(_t("ko", "rate_label", r="0.0"), "속도: 0.0 req/s")
        self.assertEqual(_t("ko", "workers_label", n=0), "작업자: 0")
        self.assertEqual(_t("ko", "dissimilar", n=0), "표시 행: 0")

        self.assertEqual(_t("en", "req_count", n=0), "Requests: 0")
        self.assertEqual(_t("en", "rate_label", r="0.0"), "Rate: 0.0 req/s")
        self.assertEqual(_t("en", "workers_label", n=0), "Workers: 0")
        self.assertEqual(_t("en", "dissimilar", n=0), "Rows: 0")

    def test_api_tab_rows_are_built_from_current_result_schema(self) -> None:
        app = CtkDiscoveryApp.__new__(CtkDiscoveryApp)
        rows = app._build_rows(
            {
                "all_apis": [
                    {
                        "status_code": 200,
                        "probe_method": "GET",
                        "path": "/api/users",
                        "url": "https://example.com/api/users",
                        "sources": ["script.js"],
                    }
                ],
                "accessible_apis": [
                    {
                        "status_code": 200,
                        "path": "/api/users",
                        "url": "https://example.com/api/users",
                    },
                    {
                        "status_code": 204,
                        "path": "/api/session",
                        "url": "https://example.com/api/session",
                    },
                ],
                "accessible_pages": [
                    {
                        "status_code": 200,
                        "path": "/about",
                        "url": "https://example.com/about",
                        "sources": "sitemap",
                    }
                ],
            }
        )

        api_rows = [row for row in rows if row["kind"] == "api"]
        page_rows = [row for row in rows if row["kind"] == "page"]
        self.assertEqual([row["endpoint"] for row in api_rows], ["/api/users", "/api/session"])
        self.assertEqual(api_rows[0]["method"], "GET")
        self.assertEqual(api_rows[0]["source"], "script.js")
        self.assertEqual(page_rows[0]["endpoint"], "/about")
        self.assertEqual(page_rows[0]["source"], "sitemap")


if __name__ == "__main__":
    unittest.main()
