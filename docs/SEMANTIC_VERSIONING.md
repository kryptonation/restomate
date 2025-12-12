# Semantic Versioning Guide for FoodFleet

## Overview

FoodFleet follows Semantic Versioning (SemVer) specification version 2.0.0 for version management. This document explains how versioning works in this project and provides guidelines for contributors.

## What is Semantic Versioning

Semantic Versioning is a versioning scheme that uses a three-part version number: **MAJOR.MINOR.PATCH**

### Version Number Format

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: Incremented when making incompatible API changes
- **MINOR**: Incremented when adding functionality in a backwards compatible manner  
- **PATCH**: Incremented when making backwards compatible bug fixes

### Pre-release and Build Metadata

Additional labels for pre-release and build metadata are available as extensions:

```
MAJOR.MINOR.PATCH-PRERELEASE+BUILD
```

Examples:
- `1.0.0-alpha.1`
- `1.0.0-beta.2+20240101`
- `1.0.0-rc.1`

## Current Project Configuration

### Current Version
The project is currently at version **0.0.1** as defined in `package.json`.

### Release Please Integration

FoodFleet uses Google's Release Please tool for automated semantic versioning and changelog generation.

#### Key Configuration Files

1. **package.json**
   - Contains the current version number
   - Includes release scripts for automation

2. **release-please-config.json**
   - Defines release configuration
   - Specifies changelog sections and commit types

3. **release-please-manifest.json**
   - Tracks the current version state
   - Currently set to "0.0.0"

### Version Increment Rules

The project follows these rules for version increments:

#### Major Version (Breaking Changes)
- API changes that break backwards compatibility
- Removal of deprecated features
- Significant architectural changes

#### Minor Version (New Features)
- New features that maintain backwards compatibility
- New API endpoints or methods
- Enhanced functionality

#### Patch Version (Bug Fixes)
- Bug fixes that don't change functionality
- Security patches
- Performance improvements

### Pre-Major Version Behavior

The current configuration includes special handling for pre-1.0.0 versions:

- `bump-minor-pre-major`: true - Minor version bumps are allowed before 1.0.0
- `bump-patch-for-minor-pre-major`: true - Patch bumps for minor changes before 1.0.0

## Commit Message Conventions

FoodFleet uses Conventional Commits specification for determining version increments:

### Commit Types and Version Impact

| Commit Type | Version Impact | Example |
|-------------|----------------|---------|
| `feat:` | MINOR | `feat: add user authentication` |
| `fix:` | PATCH | `fix: resolve login validation issue` |
| `BREAKING CHANGE:` | MAJOR | `feat!: redesign user API` |
| `chore:` | No version change | `chore: update dependencies` |
| `docs:` | No version change | `docs: update API documentation` |
| `style:` | No version change | `style: fix code formatting` |
| `refactor:` | PATCH | `refactor: improve error handling` |
| `test:` | No version change | `test: add unit tests for auth` |
| `build:` | No version change | `build: update webpack config` |
| `ci:` | No version change | `ci: update GitHub Actions` |

### Commit Message Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Examples

#### Feature Addition (Minor Version)
```
feat(auth): add OAuth2 integration

Implement OAuth2 authentication flow with Google and GitHub providers.
Includes new middleware for token validation.
```

#### Bug Fix (Patch Version)
```
fix(api): handle null values in user profile endpoint

Prevents server crashes when user profile data contains null values.
Adds proper validation and default value handling.
```

#### Breaking Change (Major Version)
```
feat!: redesign user management API

BREAKING CHANGE: User API endpoints have been restructured.
- `/users` endpoint now returns paginated results
- User ID format changed from integer to UUID
- Removed deprecated `/user/profile` endpoint

Migration guide available in MIGRATION.md
```

## Changelog Management

Release Please automatically generates changelogs based on commit messages:

### Changelog Sections

The following sections are included in generated changelogs:

- **Features**: New functionality and enhancements
- **Bug Fixes**: Bug fixes and patches
- **Documentation**: Documentation updates
- **Code Refactoring**: Code improvements without functional changes
- **Styling**: Code style and formatting changes
- **Miscellaneous**: General maintenance and chores

### Hidden Sections

The following commit types are tracked but hidden from user-facing changelogs:

- **Tests**: Test additions and modifications
- **Build System**: Build configuration changes
- **Continuous Integration**: CI/CD pipeline updates

## Release Process

### Automated Release Workflow

1. **Commit Changes**: Use conventional commit messages
2. **Release PR Creation**: Run `npm run release` to create release pull request
3. **Review and Merge**: Review the generated changelog and version bump
4. **Automatic Tagging**: Run `npm run release:tag` to create GitHub release

### Manual Release Commands

```bash
# Create release pull request
npm run release

# Create GitHub release and tag
npm run release:tag
```

## Version Strategy

### Development Phase (0.x.x)

During the initial development phase:
- PATCH versions for bug fixes
- MINOR versions for new features
- Breaking changes increment MINOR version (not MAJOR)
- First stable release will be 1.0.0

### Stable Phase (1.x.x+)

After reaching 1.0.0:
- PATCH versions for backwards compatible fixes
- MINOR versions for backwards compatible features
- MAJOR versions for breaking changes

## Best Practices

### For Contributors

1. **Use Conventional Commits**: Follow the commit message format strictly
2. **Describe Breaking Changes**: Clearly document any breaking changes
3. **Update Documentation**: Include relevant documentation updates
4. **Test Thoroughly**: Ensure changes don't break existing functionality

### For Maintainers

1. **Review Release PRs**: Carefully review generated changelogs and version bumps
2. **Validate Version Increments**: Ensure version changes match the impact of changes
3. **Communicate Breaking Changes**: Provide migration guides for major version changes
4. **Tag Releases Promptly**: Create releases shortly after merging release PRs

## Troubleshooting

### Common Issues

#### Version Mismatch
If `package.json` and `release-please-manifest.json` versions don't match:
1. Update `release-please-manifest.json` to match `package.json`
2. Commit the change with a `chore:` message

#### Missing Changelog Entries
If commits aren't appearing in changelog:
1. Verify commit messages follow conventional format
2. Check if commit type is hidden in configuration
3. Ensure commits are on the main branch

#### Incorrect Version Bump
If version increment is wrong:
1. Review commit messages for breaking change indicators
2. Check for `!` suffix in commit type (indicates breaking change)
3. Verify configuration in `release-please-config.json`

## Additional Resources

- [Semantic Versioning Specification](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Release Please Documentation](https://github.com/googleapis/release-please)
- [FoodFleet Release Configuration](../release-please-config.json)
