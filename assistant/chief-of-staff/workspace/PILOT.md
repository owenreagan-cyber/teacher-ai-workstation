# Phase D Controlled Metadata Observation Pilot

## Approved scope

- Source: `/Users/owen/Projects/history`
- Source identity: `history-project-local`
- Registered parent source: `projects-local`
- Subtree: project root only
- Maximum depth: 2
- Maximum observations: 500, including the root
- Maximum duration: 60 seconds
- Output: `.local/chief-of-staff/workspace/`

The source and output are fixed constants. The runner accepts no alternate path
or scope argument.

## Collection behavior

The collector uses directory enumeration and non-following stat metadata. It
records relative paths, item type, size, modification time, extension hint,
availability, and symlink presence. Hidden entries are skipped before metadata
collection. Symlinks are recorded as unavailable evidence and never followed.
Cross-filesystem entries are not traversed.

The collector does not open source files, read `.git`, invoke Git, calculate
hashes, parse content, inspect environment variables, generate recommendations,
or mutate the source.

## Local artifacts

Each successful run writes exactly one JSON document to each of:

- `inventory-runs/`
- `observations/`
- `audit/`

The observation document also contains one unreviewed, non-authoritative
relationship-preparation record. It does not create a relationship.

## Validation

Run the static gate before observation:

```bash
python3 validate_pilot.py
python3 -m unittest discover -v -s tests -p 'test_*.py'
```

Validate one explicit local run afterward:

```bash
python3 validate_pilot.py --run-id RUN_ID
```

The live runner itself is intentionally not documented as a general-purpose
scanner. A new source or broader scope requires a new approved phase.
