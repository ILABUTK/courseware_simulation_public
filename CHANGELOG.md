# Changelog

One entry per tagged release (see `docs/dist_plan.md` §6 for the versioning
scheme). Newest first.

## Unreleased

- Adopted the single-repo distribution model: this private repo now builds an
  instructor package and a public package via `bash cli.sh dist-instructor` /
  `dist-public` (`scripts/build_dist.py`); the former four-repo split
  (`simdes-book` / `simdes-course` / `simdes-solutions`) is retired.
  See `docs/dist_plan.md`.
