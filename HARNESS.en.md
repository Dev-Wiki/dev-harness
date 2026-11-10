# HARNESS — dev-harness repository verification contract

[English](HARNESS.en.md) | [简体中文](HARNESS.md)

Run commands from the repository root, with Python 3 and Git installed. Verification entry points come from [Testing](docs/TESTING.en.md); this repository's Python source and Skill documents do not require a separate compilation step.

## Confirmed commands (manually maintained)

| Purpose | Command | Meaning | Status |
|---|---|---|---|
| test | `python3 -m unittest discover -s tests -v` | Full Python regression, including installation, export, and cross-Skill contracts | confirmed |
| full | `python3 -m unittest discover -s tests -v` | Full regression; run a separate diff check before release | confirmed |
| quick | `git diff --check` | Check whitespace errors in the new diff | confirmed |
| bugfix | `python3 -m unittest discover -s tests -v` | Bug regression; existing test modules may be selected for focused debugging | confirmed |

## Execution boundaries

- Tests build and install synthetic skills in temporary directories; they do not authorize changes to real host Skill directories.
- Installation, export, and release use `install.py` and `release.py`; publishing and committing require separate authorization.
- Do not change file encodings, overwrite manually maintained confirmed commands, or overwrite existing user changes.
