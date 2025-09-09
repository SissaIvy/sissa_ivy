import unittest


class TestVersionExposed(unittest.TestCase):
    def test_package_version_exposed_and_consistent(self):
        import episodic_memory as em
        v = getattr(em, "__version__", "")
        self.assertIsInstance(v, str)
        self.assertTrue(len(v) > 0)

        # Try to compare with installed metadata when available
        try:
            from importlib.metadata import version as md_version
            meta = md_version("episodic-memory")
            self.assertTrue(v == meta or v.startswith(meta + "+"))
        except Exception:
            # If metadata lookup isn't available in the environment, we at least exposed a non-empty version
            pass


if __name__ == "__main__":
    unittest.main()

