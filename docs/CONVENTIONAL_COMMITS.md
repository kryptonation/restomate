# Conventional Commits Guide for FoodFleet

## Overview

FoodFleet follows the Conventional Commits specification for standardized commit messages. This ensures consistent version bumping, automated changelog generation, and clear project history.

## Commit Message Structure

### Basic Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Components

#### Type (Required)

The commit type determines the version increment and changelog section:

| Type | Purpose | Version Impact | Changelog Section |
|------|---------|----------------|-------------------|
| `feat` | New feature | Minor | Features |
| `fix` | Bug fix | Patch | Bug Fixes |
| `docs` | Documentation changes | None | Documentation |
| `style` | Code formatting changes | None | Styling |
| `refactor` | Code refactoring | Patch | Code Refactoring |
| `test` | Adding or updating tests | None | Hidden |
| `chore` | Maintenance tasks | None | Miscellaneous |
| `build` | Build system changes | None | Hidden |
| `ci` | CI/CD changes | None | Hidden |

#### Scope (Optional)

The scope provides additional context about the area of change:

Examples:
- `feat(auth): add OAuth2 login`
- `fix(api): resolve validation error`
- `docs(readme): update installation guide`

Common scopes in FoodFleet:
- `auth` - Authentication and authorization
- `api` - API endpoints and middleware
- `ui` - User interface components
- `db` - Database operations
- `config` - Configuration files
- `test` - Testing utilities
- `ci` - Continuous integration

#### Description (Required)

Brief description of the change:
- Use imperative mood ("add" not "added")
- Start with lowercase letter
- No period at the end
- Maximum 50 characters recommended

#### Body (Optional)

Detailed explanation of the change:
- Explain what and why, not how
- Use imperative mood
- Wrap at 72 characters
- Separate from description with blank line

#### Footer (Optional)

Additional information:
- Breaking changes
- Issue references
- Co-authored commits
- Signed-off information

## Breaking Changes

### Indicating Breaking Changes

Breaking changes trigger major version increments and require special notation:

#### Method 1: Exclamation Mark

```
feat!: redesign user authentication API

BREAKING CHANGE: Authentication endpoints have been restructured
```

#### Method 2: Footer Only

```
feat(auth): add new login endpoint

BREAKING CHANGE: Old login endpoint /auth/login is deprecated
```

### Breaking Change Guidelines

- Always include `BREAKING CHANGE:` in footer
- Explain the change and impact
- Provide migration instructions
- Consider deprecation warnings first

## Detailed Examples

### Feature Addition

```
feat(user): add user profile management

Implement CRUD operations for user profiles including:
- Create new user profile
- Update existing profile information  
- Delete user profile
- Retrieve profile data with privacy settings

Closes #123
```

### Bug Fix

```
fix(api): resolve null pointer exception in user lookup

Handle cases where user ID is not found in database to prevent
application crashes during authentication flow.

The fix adds proper validation and returns appropriate error
responses instead of throwing uncaught exceptions.

Fixes #456
```

### Documentation Update

```
docs(api): add authentication flow diagrams

Include sequence diagrams showing OAuth2 and JWT authentication
flows to help developers understand the authentication process.

- Add OAuth2 flow diagram
- Add JWT refresh token flow
- Update API endpoint documentation
```

### Code Refactoring

```
refactor(auth): extract validation logic into separate module

Move user input validation from controller to dedicated validation
service for better code organization and reusability.

- Create UserValidationService class
- Update AuthController to use validation service
- Add comprehensive unit tests for validation logic
```

### Breaking Change Example

```
feat!: redesign REST API structure

BREAKING CHANGE: API endpoints have been restructured for better
consistency and RESTful design.

Changes:
- `/api/users/get` -> `/api/users` (GET)
- `/api/users/create` -> `/api/users` (POST)
- `/api/users/update/{id}` -> `/api/users/{id}` (PUT)
- `/api/users/delete/{id}` -> `/api/users/{id}` (DELETE)

Migration guide available at: docs/MIGRATION.md
```

### Multiple Changes

```
feat(api): implement user role management

Add comprehensive role-based access control system:

- Create Role and Permission entities
- Implement role assignment for users
- Add middleware for permission checking
- Update user authentication to include roles
- Create admin endpoints for role management

This enables fine-grained access control throughout the application
and provides foundation for future authorization features.

Closes #234, #235, #236
```

## Scope Guidelines

### Recommended Scopes

#### Backend/API Scopes
- `auth` - Authentication and authorization
- `api` - General API changes
- `db` - Database schema, migrations, queries
- `middleware` - Express middleware functions
- `validation` - Input validation logic
- `security` - Security-related changes
- `config` - Configuration management

#### Frontend Scopes (if applicable)
- `ui` - User interface components
- `routing` - Application routing
- `state` - State management
- `forms` - Form components and validation
- `layout` - Layout and styling
- `components` - Reusable components

#### Infrastructure Scopes
- `ci` - Continuous integration
- `deploy` - Deployment scripts
- `docker` - Docker configuration
- `build` - Build system changes
- `deps` - Dependency updates

#### Documentation Scopes
- `readme` - README file updates
- `api-docs` - API documentation
- `guides` - User guides and tutorials
- `comments` - Code comments and inline docs

### Scope Best Practices

1. **Be Consistent**: Use established scope names
2. **Be Specific**: Choose the most specific applicable scope
3. **Avoid Overlap**: Don't use multiple scopes that mean the same thing
4. **Document Scopes**: Maintain list of approved scopes in team guidelines

## Commit Message Rules

### Do's

- Use imperative mood in description
- Keep description under 50 characters
- Capitalize the first letter of type
- Include scope when change affects specific area
- Reference issues in body or footer
- Explain "why" in body, not "how"
- Use present tense ("add" not "added")

### Don'ts

- Don't end description with period
- Don't use past tense ("added", "fixed")
- Don't be vague ("update stuff", "fix bug")
- Don't include implementation details in description
- Don't forget breaking change notation
- Don't use capital letters in scope
- Don't exceed 72 characters in body lines

## Common Patterns

### Dependency Updates

```
chore(deps): update express to version 4.18.2

Update Express framework to latest version for security fixes
and performance improvements.
```

### Test Additions

```
test(auth): add unit tests for JWT token validation

Increase test coverage for authentication module by adding
comprehensive tests for token validation scenarios.
```

### Configuration Changes

```
config(eslint): update linting rules for TypeScript

Add stricter TypeScript linting rules to improve code quality
and consistency across the project.
```

### Performance Improvements

```
perf(db): optimize user query with database indexes

Add database indexes on frequently queried user fields to
improve query performance by 60%.

- Add index on email field
- Add composite index on status and created_date
- Update query execution plans
```

### Security Fixes

```
fix(security): prevent SQL injection in user search

Sanitize user input in search functionality to prevent SQL
injection attacks. Replace string concatenation with
parameterized queries.

CVE-2024-XXXX
```

## Integration with Release Process

### Automated Version Bumping

Commit types automatically determine version increments:

- `feat:` → Minor version increment (0.1.0 → 0.2.0)
- `fix:` → Patch version increment (0.1.0 → 0.1.1)
- `feat!:` or `BREAKING CHANGE:` → Major version increment (0.1.0 → 1.0.0)

### Changelog Generation

Commits are automatically organized into changelog sections based on type:

```markdown
## [1.2.0] - 2024-10-18

### Features
- feat(auth): add OAuth2 authentication
- feat(api): implement user role management

### Bug Fixes  
- fix(db): resolve connection timeout issues
- fix(validation): handle edge case in email validation

### Documentation
- docs(readme): update installation instructions
- docs(api): add endpoint examples
```

## Validation Tools

### Pre-commit Hooks

Consider using tools like:
- `commitizen` - Interactive commit message builder
- `commitlint` - Lint commit messages
- `husky` - Git hooks management

### Example commitlint Configuration

```javascript
// commitlint.config.js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', [
      'feat', 'fix', 'docs', 'style', 'refactor', 
      'test', 'chore', 'build', 'ci'
    ]],
    'scope-case': [2, 'always', 'lower-case'],
    'subject-case': [2, 'never', ['start-case', 'pascal-case']],
    'subject-full-stop': [2, 'never', '.'],
    'header-max-length': [2, 'always', 50]
  }
};
```

## Troubleshooting

### Common Issues

#### Version Not Incrementing

Problem: Commits not triggering version bumps

Solutions:
- Verify commit message format
- Check if commit type triggers version increment
- Ensure commits are on main branch
- Review release-please configuration

#### Missing Changelog Entries

Problem: Commits not appearing in changelog

Solutions:
- Confirm conventional commit format
- Check if commit type is hidden in configuration
- Verify commit is after last release

#### Wrong Version Increment

Problem: Incorrect version bump level

Solutions:
- Review commit messages for breaking change indicators
- Check for `!` suffix or `BREAKING CHANGE:` footer
- Validate commit type selection

### Best Practices for Teams

1. **Team Training**: Ensure all team members understand conventional commits
2. **Consistent Scopes**: Maintain documented list of approved scopes
3. **Review Process**: Include commit message review in pull request process
4. **Automation**: Use tools to validate commit messages
5. **Documentation**: Keep examples and guidelines easily accessible
