"""Canvas grade-entry capability (disabled by default).

This package adds the minimum capability to read a course roster, read an
assignment, read current submission grades, and write a grade for one
explicitly approved (student, assignment) pair.

Nothing here runs unless ``GRADE_ENTRY_ENABLED=1`` is set *and* a signed
approval packet matching the exact proposed changes is supplied.
"""
