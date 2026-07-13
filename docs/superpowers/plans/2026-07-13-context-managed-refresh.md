# Context Managed Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add safe, section-managed context refresh that preserves user text and file format while preventing `scan` and `--force` from replacing existing context files.

**Architecture:** Add `context/managed.py` for marker parsing, format-preserving I/O, managed-block merge, and atomic writes. Keep repository detection and rendering in `context/cli.py`; templates declare stable managed block IDs, while CLI routes `scan` and `refresh` through separate write policies.

**Tech Stack:** Python 3 standard library, `dataclasses`, `hashlib`, `tempfile`, `unittest`, Markdown templates.

## Global Constraints

- Work directly on the current branch; do not create a Git worktree.
- Use TDD for every behavior change and verify RED before implementation.
- Never replace an existing context file as a whole.
- `scan --force` cannot overwrite existing files.
- `refresh --force` can update valid managed blocks only.
- Text outside managed blocks remains user-owned.
- Preserve UTF-8, UTF-8 BOM, UTF-16 BOM, CRLF/LF, final-newline state, and file mode.
- Reject mixed line endings, undecodable text, malformed markers, duplicate IDs, nested markers, and unsupported marker versions.
- Complete and commit this Context phase before starting Git Workflow changes.

---

### Task 1: Managed document parser and format-preserving I/O

**Files:**
- Create: `context/managed.py`
- Create: `tests/test_managed_context.py`

**Interfaces:**
- Produces: `DocumentFormat`, `ManagedBlock`, `ManagedDocumentError`, `decode_document`, `encode_document`, `parse_managed_blocks`, `merge_managed_blocks`, `atomic_write_document`.
- Consumes: normalized generated Markdown containing marker pairs.

- [ ] **Step 1: Write failing format and parser tests**

Create `tests/test_managed_context.py` with tests that import the interfaces above and verify:

```python
class ManagedContextTests(unittest.TestCase):
    def test_round_trips_utf8_bom_crlf_without_final_newline(self) -> None:
        raw = codecs.BOM_UTF8 + "A\r\nB".encode("utf-8")
        text, document_format = decode_document(raw)
        self.assertEqual(text, "A\nB")
        self.assertEqual(document_format.newline, "\r\n")
        self.assertFalse(document_format.final_newline)
        self.assertEqual(encode_document(text, document_format), raw)

    def test_rejects_mixed_line_endings(self) -> None:
        with self.assertRaisesRegex(ManagedDocumentError, "mixed line endings"):
            decode_document(b"A\r\nB\n")

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

    def test_rejects_duplicate_nested_and_unclosed_blocks(self) -> None:
        invalid_documents = (
            "<!-- dev-harness:managed:start id=x version=1 -->\na\n<!-- dev-harness:managed:end id=x -->\n<!-- dev-harness:managed:start id=x version=1 -->\nb\n<!-- dev-harness:managed:end id=x -->\n",
            "<!-- dev-harness:managed:start id=x version=1 -->\n<!-- dev-harness:managed:start id=y version=1 -->\n<!-- dev-harness:managed:end id=y -->\n<!-- dev-harness:managed:end id=x -->\n",
            "<!-- dev-harness:managed:start id=x version=1 -->\nunclosed\n",
        )
        for text in invalid_documents:
            with self.subTest(text=text):
                with self.assertRaises(ManagedDocumentError):
                    parse_managed_blocks(text)
```

- [ ] **Step 2: Run the new module tests and verify RED**

Run:

```bash
python -m unittest tests.test_managed_context -v
```

Expected: import failure because `context.managed` does not exist.

- [ ] **Step 3: Implement document format detection**

Create these exact public types and behaviors in `context/managed.py`:

```python
@dataclass(frozen=True)
class DocumentFormat:
    encoding: str
    bom: bytes
    newline: str
    final_newline: bool

class ManagedDocumentError(ValueError):
    pass

def decode_document(raw: bytes) -> tuple[str, DocumentFormat]:
    # Detect UTF-8/UTF-16 BOM first, otherwise require strict UTF-8.
    # Reject lone CR and simultaneous CRLF plus LF.
    # Return text normalized to LF.

def encode_document(text: str, document_format: DocumentFormat) -> bytes:
    # Convert normalized LF to the original newline and restore BOM/encoding.
```

Use `codecs.BOM_UTF8`, `codecs.BOM_UTF16_LE`, and `codecs.BOM_UTF16_BE`. Convert `UnicodeDecodeError` into `ManagedDocumentError("unsupported or undecodable text encoding")`.

- [ ] **Step 4: Implement strict managed-block parsing**

Use line-anchored regular expressions:

```python
START_RE = re.compile(
    r"^<!-- dev-harness:managed:start id=(?P<id>[a-z0-9][a-z0-9._-]*) version=(?P<version>\d+) -->$"
)
END_RE = re.compile(r"^<!-- dev-harness:managed:end id=(?P<id>[a-z0-9][a-z0-9._-]*) -->$")

@dataclass(frozen=True)
class ManagedBlock:
    block_id: str
    version: int
    start: int
    body_start: int
    body_end: int
    end: int
    body: str

def parse_managed_blocks(text: str) -> dict[str, ManagedBlock]:
    # Scan lines with retained offsets; reject malformed marker-like lines,
    # nesting, duplicate IDs, mismatched end IDs, missing ends, and version != 1.
```

- [ ] **Step 5: Implement managed merge and atomic write**

```python
def merge_managed_blocks(existing: str, generated: str) -> tuple[str, list[str]]:
    # Require at least one existing marker.
    # Replace matching block spans from end to start.
    # Insert generated-only blocks before the next known block or at EOF.
    # Preserve existing-only blocks and all text outside markers.
    # Return merged text and changed block IDs.

def atomic_write_document(path: Path, text: str, document_format: DocumentFormat) -> None:
    # Write encoded bytes to NamedTemporaryFile in path.parent,
    # fsync, restore existing stat.S_IMODE, and os.replace into place.
```

- [ ] **Step 6: Run module tests and verify GREEN**

Run:

```bash
python -m unittest tests.test_managed_context -v
```

Expected: all parser and format tests pass.

- [ ] **Step 7: Commit the managed document foundation**

```bash
git add context/managed.py tests/test_managed_context.py
git commit -m "feat(context): add managed document primitives"
```

### Task 2: Managed templates and safe scan semantics

**Files:**
- Modify: `context/templates/README.template.md`
- Modify: `context/templates/AGENTS.template.md`
- Modify: `context/templates/ARCHITECTURE.template.md`
- Modify: `context/templates/HARNESS.template.md`
- Modify: `context/cli.py`
- Modify: `tests/test_context_cli.py`

**Interfaces:**
- Consumes: existing `generate_context_files` rendering.
- Produces: four initialized files with stable marker IDs and `scan` that creates only missing files.

- [ ] **Step 1: Write failing scan tests**

Add tests asserting:

```python
def test_scan_creates_managed_context_files(self) -> None:
    # Scan a package.json repository.
    # Every generated file contains at least one managed:start marker.
    # AGENTS contains id=agents.contract-index.
    # HARNESS contains id=harness.detected-context.

def test_scan_never_overwrites_existing_files_even_with_force(self) -> None:
    # Seed README.md with '# Human README\n'.
    # Run scan and scan --force.
    # Both retain exact bytes and return 2 because an existing context file differs.
```

Update the old `test_force_overwrites_existing_files` expectation to the safe scan contract.

- [ ] **Step 2: Run focused scan tests and verify RED**

```bash
python -m unittest \
  tests.test_context_cli.ContextCliTests.test_scan_creates_managed_context_files \
  tests.test_context_cli.ContextCliTests.test_scan_never_overwrites_existing_files_even_with_force -v
```

Expected: markers are absent and `scan --force` overwrites the seeded file.

- [ ] **Step 3: Add stable managed markers to all templates**

Use these IDs:

```text
README.md:       readme.detected-context
AGENTS.md:       agents.contract-index, agents.detected-context,
                 agents.detected-rules, agents.detected-candidates
ARCHITECTURE.md: architecture.detected-context
HARNESS.md:      harness.contract, harness.detected-context,
                 harness.detected-commands, harness.detected-boundaries
```

Each marker must contain its heading as well as body so a missing block can be inserted without reconstructing static headings. Add this lightweight AGENTS block:

```markdown
<!-- dev-harness:managed:start id=agents.contract-index version=1 -->
## 项目规范索引

- 构建与验证：`HARNESS.md`
- Git 工作流：Unknown
- 代码规范：Unknown
- 发布规范：Unknown
<!-- dev-harness:managed:end id=agents.contract-index -->
```

Keep LESSONS, manual constraints, and retro tables outside managed markers. In HARNESS, label detected commands as candidates and add an unmarked `## 已确认命令（人工维护）` section whose initial values are `Unknown`.

- [ ] **Step 4: Restrict scan writes in `context/cli.py`**

Replace whole-file overwrite behavior with:

```python
def write_initial_context_files(repo_root: Path, generated_files: dict[str, str]) -> int:
    created_files = []
    existing_files = []
    for file_name, content in generated_files.items():
        path = repo_root / file_name
        if path.exists():
            existing_files.append(file_name)
            continue
        path.write_bytes((content + "\n").encode("utf-8"))
        created_files.append(file_name)
    # Print created/existing lists. Return 2 if any existing file differs from
    # generated content; otherwise return 0. Never overwrite an existing path.
```

Keep `--force` accepted for backward CLI compatibility but print that it cannot overwrite existing context files.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run the focused command from Step 2. Expected: both tests pass.

- [ ] **Step 6: Run all context tests and repair assertions for renamed candidate headings**

```bash
python -m unittest tests.test_context_cli -v
```

Expected: all context tests pass without weakening command-content assertions.

- [ ] **Step 7: Commit initialized managed templates**

```bash
git add context/templates context/cli.py tests/test_context_cli.py
git commit -m "feat(context): generate managed context blocks"
```

### Task 3: Refresh valid managed files without touching user content

**Files:**
- Modify: `context/cli.py`
- Modify: `tests/test_context_cli.py`

**Interfaces:**
- Consumes: `decode_document`, `merge_managed_blocks`, `atomic_write_document` from `context.managed`.
- Produces: `refresh` parser command and `refresh_context_files(repo_root, generated_files, force=False)`.

- [ ] **Step 1: Write failing refresh preservation tests**

Add tests that:

```python
def test_refresh_updates_managed_blocks_and_preserves_user_text(self) -> None:
    # Initial scan; append '\n## Team Rules\nNever edit vendor/.\n'.
    # Change package.json/project evidence.
    # Patch sys.stdin.isatty to True and input to 'all'.
    # Refresh; assert managed content changed and Team Rules remained byte-identical.

def test_refresh_force_preserves_utf8_bom_crlf_and_file_mode(self) -> None:
    # Convert generated AGENTS to UTF-8 BOM + CRLF, chmod 0o640, append user text.
    # Change repository evidence and run refresh --force.
    # Assert BOM, CRLF-only, trailing-newline state, mode, and user text survive.

def test_noninteractive_refresh_with_differences_returns_two(self) -> None:
    # Run refresh without force under non-TTY after repository evidence changes.
    # Assert return 2 and bytes unchanged.
```

- [ ] **Step 2: Run refresh tests and verify RED**

Run the three exact unittest names. Expected: argparse rejects `refresh`.

- [ ] **Step 3: Add the refresh subcommand**

In `build_parser` add:

```python
refresh_parser = subparsers.add_parser("refresh", help="refresh managed context blocks")
refresh_parser.add_argument("repo_path", type=Path, help="target repository root path")
refresh_parser.add_argument("--force", action="store_true", help="update valid managed blocks without prompting")
```

Route both `scan` and `refresh` through the same repository validation, then call `write_initial_context_files` or `refresh_context_files`.

- [ ] **Step 4: Implement managed refresh policy**

```python
def refresh_context_files(repo_root: Path, generated_files: dict[str, str], force: bool = False) -> int:
    # Missing paths: create using UTF-8/LF.
    # Existing paths: read bytes, decode format, require valid markers,
    # merge blocks, and collect block-level unified diffs.
    # Non-TTY without force: print previews, do not write, return 2.
    # Interactive: retain y/n/all/none/quit behavior per file.
    # Force: atomic-write changed valid managed files.
    # Aggregate structural/encoding errors and return 1 after previews.
```

Generate diff labels as `<file>:<block-id> (existing/generated)` so review is block-scoped.

- [ ] **Step 5: Run refresh tests and verify GREEN**

Expected: all three refresh tests pass.

- [ ] **Step 6: Commit safe managed refresh**

```bash
git add context/cli.py tests/test_context_cli.py
git commit -m "feat(context): refresh managed blocks safely"
```

### Task 4: Legacy migration and malformed-document safety

**Files:**
- Modify: `context/managed.py`
- Modify: `context/cli.py`
- Modify: `tests/test_managed_context.py`
- Modify: `tests/test_context_cli.py`

**Interfaces:**
- Produces: `migrate_legacy_document(existing, generated) -> LegacyMigration` and safe refresh behavior for marker-free files.

- [ ] **Step 1: Write failing legacy and malformed tests**

Cover:

```python
def test_legacy_refresh_requires_interactive_confirmation(self) -> None:
    # A marker-free existing README is unchanged in non-TTY and with --force.

def test_legacy_migration_preserves_conflicting_sections(self) -> None:
    # Existing human project description remains outside markers;
    # identical generated sections become managed after interactive approval.

def test_refresh_rejects_duplicate_nested_unclosed_and_unknown_version_markers(self) -> None:
    # For each malformed AGENTS file, refresh returns 1 and bytes are unchanged.

def test_refresh_rejects_mixed_line_endings_and_unknown_encoding(self) -> None:
    # Mixed CRLF/LF and invalid UTF-8 return 1 without writes.
```

- [ ] **Step 2: Verify the legacy tests fail for the expected reasons**

Run the four exact tests. Expected: legacy migration is not implemented and malformed errors are not aggregated correctly.

- [ ] **Step 3: Implement conservative legacy migration**

```python
@dataclass(frozen=True)
class LegacyMigration:
    merged_text: str
    safe_section_ids: tuple[str, ...]
    conflict_headings: tuple[str, ...]

def migrate_legacy_document(existing: str, generated: str) -> LegacyMigration:
    # Split both documents by level-1/level-2 Markdown headings.
    # Exact matching known sections become their generated managed blocks.
    # Differing or unknown sections stay byte-for-byte user-owned.
    # Do not duplicate headings or content.
```

Only interactive `refresh` may apply this migration. `refresh --force` reports “legacy file requires interactive migration” and returns `2`.

- [ ] **Step 4: Run legacy/malformed tests and verify GREEN**

Expected: all four tests pass.

- [ ] **Step 5: Commit legacy safety**

```bash
git add context/managed.py context/cli.py tests/test_managed_context.py tests/test_context_cli.py
git commit -m "feat(context): migrate legacy context conservatively"
```

### Task 5: Skill documentation, command ownership, packaging, and full verification

**Files:**
- Modify: `install.py`
- Modify: `context/SKILL.md`
- Modify: `commands/SKILL.md`
- Modify: `docs/HARNESS_GUIDE.md`
- Modify: `tests/test_install.py`

**Interfaces:**
- Consumes: final `scan` and `refresh` behavior.
- Produces: installed skill bundle containing `context/managed.py` and instructions that write confirmed commands outside managed blocks.

- [ ] **Step 1: Write the failing installed-refresh test**

Extend `tests/test_install.py`:

```python
def test_installed_context_launcher_can_refresh_managed_files(self) -> None:
    # Install bundle, run launcher scan, append user text to AGENTS,
    # mutate package evidence, run launcher refresh --force,
    # assert return 0 and user text remains.
```

- [ ] **Step 2: Run installed-refresh test and verify RED**

Expected: installed bundle lacks `context/managed.py` or launcher refresh support.

- [ ] **Step 3: Package the managed module and update instructions**

Append `"managed.py"` to `CONTEXT_RUNTIME_FILES` in `install.py` so it is copied with `cli.py`, `repo_walk.py`, and `platform_profiles.py`.

Document:

- `scan` is initialization-only;
- `refresh` updates managed blocks;
- legacy migration requires interaction;
- force never replaces user content;
- encoding and newline failures stop writes;
- `dev-harness-commands` writes confirmed commands only in `## 已确认命令（人工维护）`, never inside detected candidate markers.

- [ ] **Step 4: Run installed-refresh test and verify GREEN**

Expected: installed launcher refreshes and preserves user text.

- [ ] **Step 5: Run full verification**

```bash
python -m unittest discover -s tests -v
git -c core.whitespace=cr-at-eol diff --check
git status --short
```

Expected: all tests pass, no whitespace errors, and only intended Task 5 files are uncommitted.

- [ ] **Step 6: Commit Context managed refresh documentation and packaging**

```bash
git add install.py context/SKILL.md commands/SKILL.md docs/HARNESS_GUIDE.md tests/test_install.py
git commit -m "docs(context): document managed refresh workflow"
```

- [ ] **Step 7: Final Context phase audit**

Re-run the full suite after the commit, verify `git status --short` is empty, and check every requirement in `docs/superpowers/specs/2026-07-13-context-managed-refresh-design.md`. Do not start Git Workflow work until this audit passes.
