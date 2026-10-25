#!/usr/bin/env ts-node
import * as fs from 'fs';
import * as path from 'path';

/**
 * Canonical Context Pack 2026 - Static Validator
 *
 * Objective: Verify "Weekly Pacing Data" against the business logic and rules extracted in Step 1.
 * Rules enforced:
 * 1. Friday Constraints: Throw FAIL if a Friday has standard homework scheduled (at_home is non-empty), unless it's a Test.
 * 2. Together Logic: Throw FAIL if Reading and Spelling subjects target different Canvas Course IDs.
 * 3. Math Assessment Family: Throw FAIL if a Math Test is scheduled but does not include both "Study Guide Blank" and "Study Guide Completed" in its resources.
 */

// Interface Definitions
interface PacingEntry {
  date: string;         // YYYY-MM-DD
  weekday: string;      // Monday, Tuesday, Wednesday, Thursday, Friday
  subject: string;      // math, reading, spelling, language-arts, history, science
  entry_type: string;   // lesson, test, study-guide, checkout, review
  title: string;        // Descriptive title
  lesson?: number;      // Lesson number
  test?: number;        // Test number
  in_class: string;     // In-class activities
  at_home: string;      // Homework instructions (must be empty on Friday, unless a Test)
  resources: string[];  // Resource names/IDs
}

interface CourseMapping {
  subjectId: string;
  courseId: number;
}

interface WeeklyPacingData {
  weekCode: string;
  startDate: string;
  endDate: string;
  courseMappings: CourseMapping[];
  entries: PacingEntry[];
}

// Validation Functions
class ContextPackValidator {
  private data: WeeklyPacingData;

  constructor(data: WeeklyPacingData) {
    this.data = data;
  }

  public validate(): { success: boolean; errors: string[] } {
    const errors: string[] = [];

    // Rule 1: Friday Constraints (No standard homework on Friday unless it's a test)
    this.validateFridayHomework(errors);

    // Rule 2: Together Logic (Reading and Spelling must target the same Course ID)
    this.validateReadingSpellingCourseId(errors);

    // Rule 3: Math Assessment Family (Math Test requires Study Guide Blank and Completed)
    this.validateMathTestStudyGuide(errors);

    return {
      success: errors.length === 0,
      errors
    };
  }

  private validateFridayHomework(errors: string[]): void {
    const fridayEntries = this.data.entries.filter(
      (e) => e.weekday.toLowerCase() === 'friday'
    );

    for (const entry of fridayEntries) {
      const isTest = entry.entry_type.toLowerCase() === 'test';
      const hasHomework = entry.at_home && entry.at_home.trim().toLowerCase() !== 'none' && entry.at_home.trim() !== '';

      if (hasHomework && !isTest) {
        errors.push(
          `FAIL [Friday Constraint]: Friday entry for "${entry.subject}" has homework scheduled ("${entry.at_home}"), but it is not a Test.`
        );
      }
    }
  }

  private validateReadingSpellingCourseId(errors: string[]): void {
    const readingMap = this.data.courseMappings.find((m) => m.subjectId === 'reading');
    const spellingMap = this.data.courseMappings.find((m) => m.subjectId === 'spelling');

    if (!readingMap) {
      errors.push(`FAIL [Course Mapping]: Course mapping is missing for Reading.`);
      return;
    }
    if (!spellingMap) {
      errors.push(`FAIL [Course Mapping]: Course mapping is missing for Spelling.`);
      return;
    }

    if (readingMap.courseId !== spellingMap.courseId) {
      errors.push(
        `FAIL [Together Logic]: Reading Course ID (${readingMap.courseId}) and Spelling Course ID (${spellingMap.courseId}) must target the same Canvas course.`
      );
    }
  }

  private validateMathTestStudyGuide(errors: string[]): void {
    const mathTests = this.data.entries.filter(
      (e) => e.subject.toLowerCase() === 'math' && e.entry_type.toLowerCase() === 'test'
    );

    for (const testEntry of mathTests) {
      const testNum = testEntry.test || testEntry.lesson;
      if (!testNum) {
        errors.push(`FAIL [Math Test]: Math test entry "${testEntry.title}" is missing a test or lesson number.`);
        continue;
      }

      // Check if resources list contains both Blank and Completed Study Guides for this test number
      const resources = testEntry.resources || [];
      const hasBlank = resources.some((r) => r.toLowerCase().includes(`study guide ${testNum} blank`));
      const hasCompleted = resources.some((r) => r.toLowerCase().includes(`study guide ${testNum} completed`));

      if (!hasBlank || !hasCompleted) {
        const missing: string[] = [];
        if (!hasBlank) missing.push(`"Study Guide ${testNum} Blank"`);
        if (!hasCompleted) missing.push(`"Study Guide ${testNum} Completed"`);
        errors.push(
          `FAIL [Math Test Family]: Math Test ${testNum} ("${testEntry.title}") is missing required Study Guide resources: ${missing.join(' and ')}.`
        );
      }
    }
  }
}

// Dummy JSON Payloads for Testing
const PERFECTLY_VALID_PAYLOAD: WeeklyPacingData = {
  weekCode: "Q1W5",
  startDate: "2026-08-17",
  endDate: "2026-08-21",
  courseMappings: [
    { subjectId: "math", courseId: 26404 },
    { subjectId: "reading", courseId: 26442 },
    { subjectId: "spelling", courseId: 26442 }, // Matching Reading course ID
    { subjectId: "language-arts", courseId: 26495 }
  ],
  entries: [
    {
      date: "2026-08-17",
      weekday: "Monday",
      subject: "math",
      entry_type: "lesson",
      title: "Saxon Math Lesson 17: Fractions",
      lesson: 17,
      in_class: "Introduce fractions concept, practice problems 1-10.",
      at_home: "SM5: Lesson 17 Odds",
      resources: ["Power Up C", "Lesson 17 Practice Sheet"]
    },
    {
      date: "2026-08-21",
      weekday: "Friday",
      subject: "math",
      entry_type: "test", // Math test scheduled on Friday is allowed to have assessment info
      title: "Saxon Math Test 3",
      test: 3,
      in_class: "Complete Written Test 3 and Fact Test 3.",
      at_home: "None", // Friday has no homework
      resources: ["Study Guide 3 Blank", "Study Guide 3 Completed", "Power Up B"] // Includes both Study Guide blank/completed
    },
    {
      date: "2026-08-21",
      weekday: "Friday",
      subject: "reading",
      entry_type: "review",
      title: "Reading Lesson 5 Review",
      lesson: 5,
      in_class: "Review comprehension letter C page 21",
      at_home: "", // No homework scheduled on Friday for standard entry
      resources: []
    }
  ]
};

const INVALID_FRIDAY_HOMEWORK_PAYLOAD: WeeklyPacingData = {
  ...PERFECTLY_VALID_PAYLOAD,
  entries: [
    ...PERFECTLY_VALID_PAYLOAD.entries,
    {
      date: "2026-08-21",
      weekday: "Friday",
      subject: "language-arts",
      entry_type: "lesson",
      title: "Shurley English Lesson 5: Pronouns",
      lesson: 5,
      in_class: "Pronoun practice in classroom",
      at_home: "Complete page 12 of Workbook", // VIOLATION: Homework scheduled on Friday for a non-test entry
      resources: []
    }
  ]
};

const INVALID_DIFFERENT_COURSE_IDS_PAYLOAD: WeeklyPacingData = {
  ...PERFECTLY_VALID_PAYLOAD,
  courseMappings: [
    { subjectId: "math", courseId: 26404 },
    { subjectId: "reading", courseId: 26442 },
    { subjectId: "spelling", courseId: 99999 }, // VIOLATION: Spelling targets a different Course ID than Reading
    { subjectId: "language-arts", courseId: 26495 }
  ]
};

const INVALID_MATH_TEST_NO_STUDY_GUIDE_PAYLOAD: WeeklyPacingData = {
  ...PERFECTLY_VALID_PAYLOAD,
  entries: [
    {
      date: "2026-08-21",
      weekday: "Friday",
      subject: "math",
      entry_type: "test",
      title: "Saxon Math Test 3",
      test: 3,
      in_class: "Written Test 3",
      at_home: "None",
      resources: ["Power Up B"] // VIOLATION: Missing Study Guide 3 Blank and Study Guide 3 Completed
    }
  ]
};

// Orchestrator Runner
function runValidationSuite(): void {
  console.log("==================================================================");
  console.log("Teacher AI Workstation — Context Pack Pacing Validator");
  console.log("==================================================================\n");

  const suites = [
    { name: "Perfect Payload (Should Pass)", payload: PERFECTLY_VALID_PAYLOAD, expectedToPass: true },
    { name: "Friday Homework Violation (Should Fail)", payload: INVALID_FRIDAY_HOMEWORK_PAYLOAD, expectedToPass: false },
    { name: "Spelling/Reading Course ID Mismatch (Should Fail)", payload: INVALID_DIFFERENT_COURSE_IDS_PAYLOAD, expectedToPass: false },
    { name: "Math Test Missing Study Guide (Should Fail)", payload: INVALID_MATH_TEST_NO_STUDY_GUIDE_PAYLOAD, expectedToPass: false }
  ];

  let overallPass = true;

  for (const suite of suites) {
    console.log(`Running Suite: ${suite.name}`);
    console.log("-".repeat(50));

    const validator = new ContextPackValidator(suite.payload);
    const result = validator.validate();

    if (result.success === suite.expectedToPass) {
      console.log(`\x1b[32mPASS\x1b[0m: Suite behaved as expected (Validation Success: ${result.success})`);
    } else {
      console.log(`\x1b[31mFAIL\x1b[0m: Suite did NOT behave as expected! (Validation Success: ${result.success}, Expected: ${suite.expectedToPass})`);
      overallPass = false;
    }

    if (!result.success) {
      console.log("Validation Errors Detected:");
      result.errors.forEach((err) => console.log(`  \x1b[31m${err}\x1b[0m`));
    } else {
      console.log("  No validation errors detected.");
    }
    console.log("\n");
  }

  console.log("=".repeat(66));
  if (overallPass) {
    console.log("\x1b[32mOVERALL VALIDATOR SELF-TEST: PASS\x1b[0m");
  } else {
    console.log("\x1b[31mOVERALL VALIDATOR SELF-TEST: FAIL\x1b[0m");
    throw new Error("Static validator self-test failed.");
  }
  console.log("=".repeat(66));
}

// Run if called directly
runValidationSuite();
