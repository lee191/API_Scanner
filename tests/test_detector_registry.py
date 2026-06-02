import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from route_api_discovery import (
    Candidate,
    CONFIDENCE_RANK,
    merge_confidence,
    add_candidate_with_confidence,
    Detector,
    DETECTOR_REGISTRY,
    collect_path_candidates,
    build_url_scope,
)
from route_api_discovery import (
    extract_openapi_paths,
    extract_vue_router_paths,
    extract_state_blob_urls,
)


class ConfidenceModelTests(unittest.TestCase):
    def test_confidence_rank_orders_levels(self):
        self.assertTrue(CONFIDENCE_RANK["high"] > CONFIDENCE_RANK["medium"])
        self.assertTrue(CONFIDENCE_RANK["medium"] > CONFIDENCE_RANK["low"])

    def test_merge_confidence_keeps_higher(self):
        self.assertEqual(merge_confidence("low", "high"), "high")
        self.assertEqual(merge_confidence("high", "low"), "high")
        self.assertEqual(merge_confidence("medium", "medium"), "medium")

    def test_candidate_defaults(self):
        candidate = Candidate(url="https://x/a", path="/a", kind="api")
        self.assertEqual(candidate.confidence, "low")
        self.assertEqual(candidate.detectors, set())


class AddCandidateWithConfidenceTests(unittest.TestCase):
    def test_adds_new_candidate_with_confidence_and_detector(self):
        bucket = {}
        add_candidate_with_confidence(
            bucket, "https://x/a", "html:https://x", "page", "high", "fetch"
        )
        candidate = next(iter(bucket.values()))
        self.assertEqual(candidate.confidence, "high")
        self.assertIn("fetch", candidate.detectors)
        self.assertIn("html:https://x", candidate.sources)

    def test_merges_confidence_to_max_and_unions_detectors(self):
        bucket = {}
        add_candidate_with_confidence(
            bucket, "https://x/a", "src1", "page", "low", "quoted_path"
        )
        add_candidate_with_confidence(
            bucket, "https://x/a", "src2", "page", "high", "fetch"
        )
        candidate = next(iter(bucket.values()))
        self.assertEqual(candidate.confidence, "high")
        self.assertEqual(candidate.detectors, {"quoted_path", "fetch"})
        self.assertEqual(candidate.sources, {"src1", "src2"})


class DetectorRegistryTests(unittest.TestCase):
    def test_registry_is_nonempty_and_well_formed(self):
        self.assertTrue(len(DETECTOR_REGISTRY) > 0)
        for detector in DETECTOR_REGISTRY:
            self.assertIsInstance(detector, Detector)
            self.assertIn(detector.confidence, {"low", "medium", "high"})
            self.assertIn(detector.kind, {"api", "page", "auto"})
            has_pattern = detector.pattern is not None
            has_extractor = detector.extractor is not None
            self.assertTrue(has_pattern != has_extractor, detector.name)

    def test_registry_names_unique(self):
        names = [d.name for d in DETECTOR_REGISTRY]
        self.assertEqual(len(names), len(set(names)))

    def test_registry_contains_core_detectors(self):
        names = {d.name for d in DETECTOR_REGISTRY}
        self.assertIn("fetch", names)
        self.assertIn("quoted_path", names)


class CollectPathCandidatesConfidenceTests(unittest.TestCase):
    def _scope(self, url):
        return build_url_scope(url, include_subdomains=True, excluded_hostnames=())

    def test_fetch_call_is_high_confidence(self):
        page_bucket = {}
        api_bucket = {}
        collect_path_candidates(
            text="fetch('/api/users')",
            base_url="https://example.com",
            source_label="html:https://example.com",
            scope=self._scope("https://example.com"),
            page_bucket=page_bucket,
            api_bucket=api_bucket,
        )
        candidate = api_bucket[next(iter(api_bucket))]
        self.assertEqual(candidate.confidence, "high")
        self.assertIn("fetch", candidate.detectors)

    def test_generic_quoted_path_is_low_confidence(self):
        page_bucket = {}
        api_bucket = {}
        collect_path_candidates(
            text="const link = '/dashboard/profile';",
            base_url="https://example.com",
            source_label="html:https://example.com",
            scope=self._scope("https://example.com"),
            page_bucket=page_bucket,
            api_bucket=api_bucket,
        )
        candidate = page_bucket[next(iter(page_bucket))]
        self.assertEqual(candidate.confidence, "low")


class NewPatternDetectorTests(unittest.TestCase):
    def _collect(self, text):
        page_bucket = {}
        api_bucket = {}
        scope = build_url_scope("https://example.com", include_subdomains=True, excluded_hostnames=())
        collect_path_candidates(
            text=text,
            base_url="https://example.com",
            source_label="html:https://example.com",
            scope=scope,
            page_bucket=page_bucket,
            api_bucket=api_bucket,
        )
        return page_bucket, api_bucket

    def _all(self, page_bucket, api_bucket):
        return list(page_bucket.values()) + list(api_bucket.values())

    def test_jquery_shorthand_get(self):
        _, api = self._collect("$.getJSON('/api/items', cb)")
        urls = {c.url for c in api.values()}
        self.assertIn("https://example.com/api/items", urls)

    def test_htmx_attribute(self):
        page, api = self._collect('<button hx-get="/api/load/widget">go</button>')
        urls = {c.url for c in self._all(page, api)}
        self.assertIn("https://example.com/api/load/widget", urls)

    def test_form_action_is_page_medium(self):
        page, _ = self._collect('<form action="/submit/contact" method="post">')
        candidate = page[next(iter(page))]
        self.assertEqual(candidate.url, "https://example.com/submit/contact")
        self.assertEqual(candidate.confidence, "medium")

    def test_service_client_ky(self):
        _, api = self._collect("ky.post('/api/orders', {json: data})")
        urls = {c.url for c in api.values()}
        self.assertIn("https://example.com/api/orders", urls)

    def test_socket_io_connect(self):
        page, api = self._collect("const s = io('/realtime/chat');")
        urls = {c.url for c in self._all(page, api)}
        self.assertIn("https://example.com/realtime/chat", urls)




class ExtractorDetectorTests(unittest.TestCase):
    def test_openapi_paths(self):
        text = '{"openapi":"3.0.0","paths":{"/api/users":{"get":{}},"/api/orders":{"post":{}}}}'
        result = extract_openapi_paths(text, "https://example.com", allow_disallowed_host=False)
        self.assertIn("/api/users", result)
        self.assertIn("/api/orders", result)

    def test_vue_router_paths(self):
        text = "const routes = [{ path: '/home' }, { path: '/users/list' }];"
        result = extract_vue_router_paths(text, "https://example.com", allow_disallowed_host=False)
        self.assertIn("/home", result)
        self.assertIn("/users/list", result)

    def test_state_blob_urls(self):
        text = 'window.__INITIAL_STATE__ = {"apiBase":"https://example.com/api/v2/data"};'
        result = extract_state_blob_urls(text, "https://example.com", allow_disallowed_host=False)
        self.assertIn("https://example.com/api/v2/data", result)

class ExtractorRegistryWiringTests(unittest.TestCase):
    def test_openapi_detector_registered(self):
        names = {d.name for d in DETECTOR_REGISTRY}
        self.assertIn("openapi_paths", names)
        self.assertIn("vue_router", names)
        self.assertIn("state_blob", names)

    def test_openapi_paths_collected_as_api(self):
        page_bucket = {}
        api_bucket = {}
        scope = build_url_scope("https://example.com", include_subdomains=True, excluded_hostnames=())
        collect_path_candidates(
            text='{"paths":{"/api/widgets":{"get":{}}}}',
            base_url="https://example.com",
            source_label="js:https://example.com/spec.json",
            scope=scope,
            page_bucket=page_bucket,
            api_bucket=api_bucket,
        )
        urls = {c.url for c in api_bucket.values()}
        self.assertIn("https://example.com/api/widgets", urls)


if __name__ == "__main__":
    unittest.main()
