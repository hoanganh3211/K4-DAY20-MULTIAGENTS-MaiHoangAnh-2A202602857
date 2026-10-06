---
name: prevent-file-modification
description: Use this skill to ensure that original test files are not modified during development.
---
1. Identify all test files in the project directory.
2. Create a backup of each test file before making any changes.
3. Implement a version control system (e.g., Git) to track changes.
4. Use a linter or static analysis tool to check for modifications in test files.
5. Establish a review process to ensure that changes to test files are approved.
6. Document the policy of not modifying original test files in the project README.
7. Create a checklist for new features that includes a reminder to add new tests instead of modifying existing ones.
8. Regularly review the test files to ensure compliance with the no-modification rule.