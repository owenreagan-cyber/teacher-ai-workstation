# Non-Traditional Lesson Doctrine

## Purpose

Some lesson planner entries are not traditional textbook lessons.

Examples:

```text
Science Lab: Earthquakes
Writing Activity on Expository Writing Unit
```

When Owen writes a non-traditional lesson entry like this, the app should preserve the exact wording as the `In Class` lesson entry.

## Exact Text Rule

The app must not rewrite, normalize, expand, or replace Owen's exact phrase unless Owen explicitly asks.

Examples:

```text
Science Lab: Earthquakes -> In Class: Science Lab: Earthquakes
Writing Activity on Expository Writing Unit -> In Class: Writing Activity on Expository Writing Unit
```

## Resource Rule

The app must not automatically pull resources for a non-traditional lesson.

The app must not infer a textbook/resource match unless Owen explicitly adds one in the lesson planner or approves a suggested resource.

## Assignment Rule

The app must not automatically create a Canvas assignment for a non-traditional lesson.

The app may create or attach an assignment only if Owen explicitly does so in the lesson planner page or approves the action.

## Classification

The app should classify these entries as:

```text
nontraditional_lesson
exact_text_in_class_entry
no_auto_resource_pull
no_auto_assignment_creation
```

## Examples

```text
Science Lab: Earthquakes
Writing Activity on Expository Writing Unit
Class Discussion: Character Motivation
Review Game: Fractions
Project Work Day
Conference Prep
```

## Safety Rule

When in doubt, preserve Owen's exact input as the In Class entry and mark resource/assignment generation as blocked until explicitly approved.
