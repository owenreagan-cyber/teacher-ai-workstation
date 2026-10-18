# Phase F Application Metadata Intelligence Pilot

## Scope

The sole approved application is `/Users/owen/Applications/Grade 4 Writing.app`.
The runner accepts no application path and performs no application discovery.
Output remains beneath the ignored `.local/chief-of-staff/workspace/` root.

## Identity separation

| Identity | Meaning |
| --- | --- |
| `application-concept:grade-4-writing-launcher` | Stable tool concept |
| `application-instance:grade-4-writing-local` | One installed copy |
| `observation:<run>:grade-4-writing-application` | One physical observation |
| `representation:grade-4-writing:installed-bundle` | Installed bundle representation |

These identities remain independent and non-authoritative.

## Metadata boundary

The observer verifies the exact bundle with `lstat`, then queries only these
Spotlight metadata attributes:

- `kMDItemDisplayName`
- `kMDItemCFBundleIdentifier`
- `kMDItemVersion`
- `kMDItemContentType`

It does not enumerate the bundle, read `Info.plist`, launch or execute the
application, inspect signing or dependencies, access app containers,
preferences, caches, databases, documents, credentials, tokens, history,
embedded resources, or screenshots.

## Relationship candidates

Two candidates are derived from the existing static Application Registry:

- The application concept is used by `project:grade-4-writing`.
- The application concept is related to `registry-system:writing`.

Both use `declared_application_mapping`, high confidence, unreviewed state,
`authority_claim: none`, and `automatic_linking: false`. They do not constitute
a relationship engine or action authority.
