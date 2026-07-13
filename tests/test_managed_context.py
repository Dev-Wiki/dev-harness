import codecs
import os
import stat
import tempfile
import unittest
from pathlib import Path

from context.managed import (
    ManagedDocumentError,
    atomic_write_document,
    decode_document,
    encode_document,
    merge_managed_blocks,
    parse_managed_blocks,
)


class ManagedContextTests(unittest.TestCase):
    def test_round_trips_utf8_bom_crlf_without_final_newline(self) -> None:
        raw = codecs.BOM_UTF8 + "A\r\nB".encode("utf-8")

        text, document_format = decode_document(raw)

        self.assertEqual(text, "A\nB")
        self.assertEqual(document_format.encoding, "utf-8")
        self.assertEqual(document_format.bom, codecs.BOM_UTF8)
        self.assertEqual(document_format.newline, "\r\n")
        self.assertFalse(document_format.final_newline)
        self.assertEqual(encode_document(text, document_format), raw)

    def test_round_trips_utf16_bom_and_final_newline(self) -> None:
        raw = codecs.BOM_UTF16_LE + "A\nB\n".encode("utf-16-le")

        text, document_format = decode_document(raw)

        self.assertEqual(text, "A\nB\n")
        self.assertEqual(document_format.encoding, "utf-16-le")
        self.assertEqual(document_format.bom, codecs.BOM_UTF16_LE)
        self.assertTrue(document_format.final_newline)
        self.assertEqual(encode_document(text, document_format), raw)

    def test_rejects_mixed_line_endings(self) -> None:
        with self.assertRaisesRegex(ManagedDocumentError, "mixed line endings"):
            decode_document(b"A\r\nB\n")

    def test_rejects_undecodable_text(self) -> None:
        with self.assertRaisesRegex(ManagedDocumentError, "unsupported or undecodable"):
            decode_document(b"\xff\xfe\x00")

    def test_parses_unique_non_nested_blocks(self) -> None:
        text = (
            "before\n"
            "<!-- dev-harness:managed:start id=demo version=1 -->\n"
            "value\n"
            "<!-- dev-harness:managed:end id=demo -->\n"
            "after\n"
        )

        blocks = parse_managed_blocks(text)

        self.assertEqual(list(blocks), ["demo"])
        self.assertEqual(blocks["demo"].body, "value\n")

    def test_rejects_invalid_blocks(self) -> None:
        invalid_documents = (
            (
                "<!-- dev-harness:managed:start id=x version=1 -->\n"
                "a\n"
                "<!-- dev-harness:managed:end id=x -->\n"
                "<!-- dev-harness:managed:start id=x version=1 -->\n"
                "b\n"
                "<!-- dev-harness:managed:end id=x -->\n"
            ),
            (
                "<!-- dev-harness:managed:start id=x version=1 -->\n"
                "<!-- dev-harness:managed:start id=y version=1 -->\n"
                "<!-- dev-harness:managed:end id=y -->\n"
                "<!-- dev-harness:managed:end id=x -->\n"
            ),
            "<!-- dev-harness:managed:start id=x version=1 -->\nunclosed\n",
            (
                "<!-- dev-harness:managed:start id=x version=1 -->\n"
                "value\n"
                "<!-- dev-harness:managed:end id=y -->\n"
            ),
            (
                "<!-- dev-harness:managed:start id=x version=2 -->\n"
                "value\n"
                "<!-- dev-harness:managed:end id=x -->\n"
            ),
        )
        for text in invalid_documents:
            with self.subTest(text=text):
                with self.assertRaises(ManagedDocumentError):
                    parse_managed_blocks(text)

    def test_merge_replaces_matching_blocks_and_preserves_user_text(self) -> None:
        existing = (
            "user before\n"
            "<!-- dev-harness:managed:start id=demo version=1 -->\n"
            "old\n"
            "<!-- dev-harness:managed:end id=demo -->\n"
            "user after\n"
        )
        generated = (
            "generated title\n"
            "<!-- dev-harness:managed:start id=demo version=1 -->\n"
            "new\n"
            "<!-- dev-harness:managed:end id=demo -->\n"
        )

        merged, changed_ids = merge_managed_blocks(existing, generated)

        self.assertEqual(changed_ids, ["demo"])
        self.assertIn("user before\n", merged)
        self.assertIn("new\n", merged)
        self.assertIn("user after\n", merged)
        self.assertNotIn("generated title", merged)

    def test_atomic_write_preserves_file_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            path.write_bytes(b"before\n")
            path.chmod(0o640)
            _, document_format = decode_document(path.read_bytes())

            atomic_write_document(path, "after\n", document_format)

            self.assertEqual(path.read_bytes(), b"after\n")
            self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o640)


if __name__ == "__main__":
    unittest.main()
