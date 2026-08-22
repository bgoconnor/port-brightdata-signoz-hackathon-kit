import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from brightdata.enrich import enrich
from brightdata.score import score_paper, score_records
from brightdata.scrape import extract_records, normalize_record, write_sqlite


class PipelineTests(unittest.TestCase):
    def test_extracts_nested_cli_envelope(self):
        records = [{"arxiv_id": "2608.1"}]
        self.assertEqual(extract_records({"data": {"results": records}}), records)

    def test_normalizes_aliases_and_lists(self):
        paper = normalize_record(
            {
                "id": "arXiv:2608.1",
                "title": " Example ",
                "authors": "Ada, Grace",
                "summary": "We propose a toy algorithm.",
                "categories": "cs.AI, cs.LG",
            },
            "2026-08-22T00:00:00Z",
        )
        self.assertEqual(paper["authors"], ["Ada", "Grace"])
        self.assertEqual(paper["arxiv_id"], "2608.1")
        self.assertEqual(paper["subjects"], ["cs.AI", "cs.LG"])
        self.assertEqual(paper["html_url"], "https://arxiv.org/html/2608.1")

    def test_rejects_incomplete_paper(self):
        with self.assertRaisesRegex(ValueError, "missing required fields"):
            normalize_record({"title": "Incomplete"}, "2026-08-22T00:00:00Z")

    def test_scores_reproducible_signal(self):
        paper = {"title": "Toy algorithm", "abstract": "We propose a synthetic experiment."}
        self.assertGreaterEqual(score_paper(paper), 0.5)
        self.assertTrue(score_records([paper])[0]["reproducible"])

    def test_writes_sqlite(self):
        paper = {
            "arxiv_id": "2608.1", "title": "Example", "authors": ["Ada"],
            "abstract": "Toy algorithm", "subjects": ["cs.AI"], "score": 0.6,
            "reproducible": True, "scraped_at": "2026-08-22T00:00:00Z",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "papers.db"
            write_sqlite([paper], path)
            self.assertTrue(path.exists())

    def test_enrichment_records_full_text_provenance(self):
        def fake_run(command, check):
            Path(command[command.index("--output") + 1]).write_text("methods and results\n" * 100)

        with tempfile.TemporaryDirectory() as directory, patch("brightdata.enrich.subprocess.run", side_effect=fake_run):
            destination = enrich("2608.12345v2", Path(directory))
            provenance = json.loads((destination / "provenance.json").read_text())
            self.assertEqual(provenance["paper_version"], "2")
            self.assertEqual(provenance["acquired_via"], "brightdata-web-unlocker")
            self.assertEqual(len(provenance["sha256"]), 64)

    def test_enrichment_rejects_invalid_identifier(self):
        with self.assertRaisesRegex(ValueError, "invalid arXiv"):
            enrich("https://example.com", Path("unused"))


if __name__ == "__main__":
    unittest.main()
