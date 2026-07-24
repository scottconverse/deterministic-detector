# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-07-24

### Added

- Codex plugin manifest, hook adapter, and repository marketplace catalog.
- Behavioral coverage for Claude and Codex hook payloads and package wiring.

### Changed

- The shared Ruff hook now recognizes edited Python files from both Claude
  `file_path` payloads and Codex `apply_patch` payloads.
- Installation and smoke-test guidance now covers Claude Code and Codex from
  the same repository.

[0.3.0]: https://github.com/scottconverse/deterministic-detector/compare/v0.2.1...v0.3.0
