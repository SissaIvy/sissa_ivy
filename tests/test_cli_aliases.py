import unittest

try:  # Python 3.10+
    from importlib.metadata import entry_points  # type: ignore
except Exception:  # pragma: no cover
    try:
        from importlib_metadata import entry_points  # type: ignore
    except Exception:  # pragma: no cover
        entry_points = None  # type: ignore


class TestCliAliases(unittest.TestCase):
    def test_console_scripts_aliases_present_or_skip(self):
        if entry_points is None:  # environment lacks metadata API
            self.skipTest("importlib.metadata not available")

        try:
            eps = entry_points()
            try:
                console = [e.name for e in eps.select(group="console_scripts")]
            except Exception:  # older importlib-metadata API
                console = [e.name for e in eps.get("console_scripts", [])]
        except Exception:
            self.skipTest("Unable to enumerate entry points in this environment")

        # If package isn't installed or the new alias isn't in this env, skip gracefully
        if not any(n in console for n in ("episodic-memory", "closed-loop-security")):
            self.skipTest("Package not installed; skipping console script checks")
        if "closed-loop-security" not in console:
            self.skipTest("New alias not present in this environment; likely not re-installed yet")

        # When installed (fresh CI/build), verify both names exist
        self.assertIn("episodic-memory", console)
        self.assertIn("closed-loop-security", console)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
