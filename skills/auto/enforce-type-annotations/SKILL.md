---
name: enforce-type-annotations
description: Use this skill to ensure that all public functions have type annotations for parameters and return values.
---
1. Review all public functions in the codebase for missing type annotations.
2. Define a standard for type annotations (e.g., use `Optional` for nullable types).
3. Use a static type checker (e.g., mypy) to identify functions without type annotations.
4. Implement a pre-commit hook to check for type annotations before code is committed.
5. Document the importance of type annotations in the project README.
6. Provide examples of correctly annotated functions in the documentation.
7. Encourage team members to add type annotations when modifying or adding functions.
8. Regularly audit the codebase to ensure compliance with type annotation standards.