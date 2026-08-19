import codecs
import os
import stat
import tempfile
import unittest
from pathlib import Path

from context.managed import (
    ManagedDocumentError,
    SectionSpec,
    atomic_write_document,
    decode_document,
    encode_document,
    merge_markdown_sections,
    parse_markdown_sections,
    strip_legacy_managed_markers,
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

    def test_parses_fixed_heading_and_ignores_heading_inside_fence(self) -> None:
        text = (
            "# Demo\n\n"
            "```markdown\n## Managed\n```\n\n"
            "## Managed\nvalue\n\n"
            "## Human\nafter\n"
        )
        specs = (SectionSpec("demo", 2, "Managed"),)

        sections = parse_markdown_sections(text, specs)

        self.assertEqual(list(sections), ["demo"])
        self.assertEqual(sections["demo"].body, "value\n\n")

    def test_rejects_missing_duplicate_and_wrong_level_headings(self) -> None:
        invalid_documents = (
            "# Demo\n",
            "## Managed\na\n## Managed\nb\n",
            "### Managed\na\n",
        )
        specs = (SectionSpec("demo", 2, "Managed"),)
        for text in invalid_documents:
            with self.subTest(text=text):
                with self.assertRaises(ManagedDocumentError):
                    parse_markdown_sections(text, specs)

    def test_merge_replaces_matching_sections_and_preserves_user_text(self) -> None:
        existing = (
            "# Demo\n\n## Managed\nold\n\n## Human\nuser after\n"
        )
        generated = (
            "# Generated title\n\n## Managed\nnew\n\n## Human\ngenerated text\n"
        )
        specs = (SectionSpec("demo", 2, "Managed"),)

        merged, changed_ids, legacy_ids = merge_markdown_sections(existing, generated, specs)

        self.assertEqual(changed_ids, ["demo"])
        self.assertEqual(legacy_ids, ())
        self.assertIn("# Demo\n", merged)
        self.assertIn("new\n", merged)
        self.assertIn("## Human\nuser after\n", merged)
        self.assertNotIn("Generated title", merged)

    def test_merge_migrates_legacy_heading_to_natural_title(self) -> None:
        existing = "# Demo\n\n## 代码风格锚点\nold\n"
        generated = "# Demo\n\n## 代码风格示例\nnew\n"
        specs = (
            SectionSpec(
                "agents.style-anchors",
                2,
                "代码风格示例",
                ("代码风格锚点",),
            ),
        )

        merged, changed_ids, legacy_ids = merge_markdown_sections(
            existing, generated, specs
        )

        self.assertEqual(changed_ids, ["agents.style-anchors"])
        self.assertEqual(legacy_ids, ())
        self.assertIn("## 代码风格示例\nnew\n", merged)
        self.assertNotIn("代码风格锚点", merged)

    def test_atomic_write_preserves_file_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            path.write_bytes(b"before\n")
            path.chmod(0o640)
            _, document_format = decode_document(path.read_bytes())

            atomic_write_document(path, "after\n", document_format)

            self.assertEqual(path.read_bytes(), b"after\n")
            self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o640)

    def test_legacy_marker_migration_removes_markers_and_preserves_body(self) -> None:
        legacy = (
            "# Demo\n\n"
            "<!-- dev-harness:managed:start id=demo.detected version=1 -->\n"
            "## Detected\nPython\n"
            "<!-- dev-harness:managed:end id=demo.detected -->\n"
        )

        cleaned, legacy_ids = strip_legacy_managed_markers(legacy)

        self.assertEqual(legacy_ids, ("demo.detected",))
        self.assertEqual(cleaned, "# Demo\n\n## Detected\nPython\n")

    def test_legacy_marker_text_inside_fence_is_not_removed(self) -> None:
        example = (
            "```markdown\n"
            "<!-- dev-harness:managed:start id=example version=1 -->\n"
            "content\n"
            "<!-- dev-harness:managed:end id=example -->\n"
            "```\n"
        )

        cleaned, legacy_ids = strip_legacy_managed_markers(example)

        self.assertEqual(legacy_ids, ())
        self.assertEqual(cleaned, example)


if __name__ == "__main__":
    unittest.main()
