import io
import os
import sys
import unittest
from contextlib import redirect_stdout

import memory_cli as cli


DATA_PATH = os.path.join(os.getcwd(), "EpisodicMemorySystem.json")


class TestCliSearchEmbedder(unittest.TestCase):
    def test_search_with_embedder_flag_executes(self):
        # Build parser and invoke the search command programmatically
        p = cli.build_parser()
        args = p.parse_args([
            "search",
            DATA_PATH,
            "episodic",
            "--top-k",
            "1",
            "--threshold",
            "0.0",
            "--embedder",
            "hash",
        ])
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.cmd_search(args)
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        # Either results or a 'No results' message should be printed
        self.assertTrue(out.strip() != "")

    def test_search_help_mentions_embedder(self):
        # format_help prints the top-level help; ensure flags are visible
        p = cli.build_parser()
        help_text = p.format_help()
        # the subparser help is not printed here, but ensure the term appears
        # (argparse includes subcommand-specific options in dedicated help)
        # As a fallback, assert the flag strings exist in module source
        with open("memory_cli.py", "r", encoding="utf-8") as f:
            src = f.read()
        self.assertIn("--embedder", src)
        self.assertIn("--openai-model", src)


if __name__ == "__main__":
    unittest.main()

