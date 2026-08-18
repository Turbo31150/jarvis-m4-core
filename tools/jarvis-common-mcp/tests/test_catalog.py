import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import catalog  # noqa: E402


class CatalogTests(unittest.TestCase):
    def test_private_sources_are_not_resolvable(self):
        with self.assertRaises(catalog.CatalogError):
            catalog.resolve("admin_prive")

    def test_escape_is_rejected(self):
        with self.assertRaises(catalog.CatalogError):
            catalog.resolve("exports_html", "../../_admin-prive")

    def test_secrets_are_redacted(self):
        self.assertIn("[REDACTED]", catalog.redact("token=very-secret-value"))


if __name__ == "__main__":
    unittest.main()
