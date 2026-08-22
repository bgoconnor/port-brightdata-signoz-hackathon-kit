import unittest

from factory.validate_candidate import PolicyError, validate_source
from factory.report_to_port import next_state


class CandidatePolicyTests(unittest.TestCase):
    def test_allows_small_standard_library_program(self):
        validate_source("import math\nprint(math.sqrt(9))\n")

    def test_rejects_filesystem_access(self):
        with self.assertRaisesRegex(PolicyError, "disallowed call: open"):
            validate_source("print(open('/etc/passwd').read())\n")

    def test_rejects_unapproved_import(self):
        with self.assertRaisesRegex(PolicyError, "disallowed imports: os"):
            validate_source("import os\nprint(os.getcwd())\n")

    def test_rejects_more_than_one_hundred_lines(self):
        with self.assertRaisesRegex(PolicyError, "100-line"):
            validate_source("\n".join("x = 1" for _ in range(101)))

    def test_execution_result_maps_to_durable_factory_state(self):
        self.assertEqual(next_state(True, 0), ("passed", "pending_review"))
        self.assertEqual(next_state(False, 0), ("failed", "repairing"))
        self.assertEqual(next_state(False, 1), ("failed", "repairing"))
        self.assertEqual(next_state(False, 2), ("failed", "failed"))


if __name__ == "__main__":
    unittest.main()
