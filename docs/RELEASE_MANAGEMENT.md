# FoodFleet Release Management

## Overview

This document provides detailed information about the release management process for FoodFleet, including automated workflows, manual procedures, and troubleshooting guidelines.

## Release Please Configuration

FoodFleet uses Google's Release Please tool for automated semantic versioning and release management.

### Configuration Files

#### release-please-config.json

The main configuration file that defines:

- **Release Type**: `node` - Optimized for Node.js projects
- **Package Configuration**: Root package settings
- **Changelog Sections**: Organized commit categorization
- **Version Bump Rules**: Pre-major version handling

Key settings:
```json
{
  "release-type": "node",
  "bump-minor-pre-major": true,
  "bump-patch-for-minor-pre-major": true,
  "draft": false,
  "prerelease": false,
  "initial-version": "0.0.0"
}
```

#### release-please-manifest.json

Tracks current version state:
```json
{
  ".": "0.0.0"
}
```

## Release Workflow

### Automated Process

1. **Continuous Integration**: Commits trigger automated analysis
2. **Version Calculation**: Release Please analyzes commit messages
3. **Release PR Generation**: Automated pull request creation
4. **Manual Review**: Team reviews proposed changes
5. **Merge and Release**: Merging triggers tag creation and release publication

### Manual Process Steps

#### Step 1: Prepare Release Pull Request

```bash
npm run release
```

This command:
- Analyzes commits since last release
- Calculates appropriate version bump
- Generates changelog entries
- Creates pull request with version updates

#### Step 2: Review Release Pull Request

Review the generated PR for:
- Correct version increment
- Accurate changelog entries
- Complete feature documentation
- Breaking change notifications

#### Step 3: Merge Release Pull Request

After approval, merge the release PR to trigger:
- Version update in package.json
- Changelog update
- Git tag preparation

#### Step 4: Create GitHub Release

```bash
npm run release:tag
```

This command:
- Creates Git tag with new version
- Publishes GitHub release
- Includes generated changelog
- Notifies subscribers

## Changelog Management

### Automated Generation

Release Please automatically generates changelogs from commit messages using conventional commit format.

### Section Organization

#### Visible Sections

**Features**
- Type: `feat:`
- Contains: New functionality and enhancements
- Version Impact: Minor increment

**Bug Fixes**
- Type: `fix:`
- Contains: Bug fixes and patches
- Version Impact: Patch increment

**Documentation**
- Type: `docs:`
- Contains: Documentation updates
- Version Impact: No increment

**Code Refactoring**
- Type: `refactor:`
- Contains: Code improvements without functional changes
- Version Impact: Patch increment

**Styling**
- Type: `style:`
- Contains: Code formatting and style changes
- Version Impact: No increment

**Miscellaneous**
- Type: `chore:`
- Contains: Maintenance tasks and dependency updates
- Version Impact: No increment

#### Hidden Sections

**Tests**
- Type: `test:`
- Contains: Test additions and modifications
- Visibility: Hidden from public changelog

**Build System**
- Type: `build:`
- Contains: Build configuration changes
- Visibility: Hidden from public changelog

**Continuous Integration**
- Type: `ci:`
- Contains: CI/CD pipeline updates
- Visibility: Hidden from public changelog

## Version Strategy

### Pre-1.0.0 Development

Current phase characteristics:
- Version format: `0.MINOR.PATCH`
- Breaking changes increment MINOR version
- New features increment MINOR version
- Bug fixes increment PATCH version

### Post-1.0.0 Stable

Future phase characteristics:
- Version format: `MAJOR.MINOR.PATCH`
- Breaking changes increment MAJOR version
- New features increment MINOR version
- Bug fixes increment PATCH version

## Release Types

### Regular Release

Standard release process for stable features:
- Complete feature set
- Comprehensive testing
- Full documentation
- Backwards compatibility (when possible)

### Hotfix Release

Emergency release for critical issues:
- Security vulnerabilities
- Critical bug fixes
- Production system failures

Process:
1. Create hotfix branch from latest release tag
2. Apply minimal fix
3. Fast-track through release process
4. Deploy immediately

### Pre-release

Testing releases for early feedback:
- Alpha: Internal testing
- Beta: Limited user testing
- Release Candidate: Final validation

Versioning format: `MAJOR.MINOR.PATCH-PRERELEASE.NUMBER`

Examples:
- `1.0.0-alpha.1`
- `1.0.0-beta.2`
- `1.0.0-rc.1`

## Release Validation

### Pre-Release Checklist

#### Code Quality
- [ ] All tests passing
- [ ] Code coverage maintained
- [ ] Linting rules satisfied
- [ ] Security scan completed

#### Documentation
- [ ] API documentation updated
- [ ] User guides current
- [ ] Migration guides (for breaking changes)
- [ ] Changelog accurate

#### Testing
- [ ] Unit tests comprehensive
- [ ] Integration tests passing
- [ ] End-to-end tests successful
- [ ] Performance benchmarks met

#### Dependencies
- [ ] Dependencies up to date
- [ ] Security vulnerabilities resolved
- [ ] License compliance verified
- [ ] Third-party compatibility confirmed

### Post-Release Verification

#### Deployment Validation
- [ ] Release published successfully
- [ ] Git tags created correctly
- [ ] Package registry updated
- [ ] Documentation deployed

#### Monitoring
- [ ] Error rates normal
- [ ] Performance metrics stable
- [ ] User feedback collected
- [ ] Issue tracker monitored

## Rollback Procedures

### Immediate Rollback

For critical issues requiring immediate action:

1. **Identify Issue**: Confirm problem scope and impact
2. **Assess Options**: Rollback vs. hotfix evaluation
3. **Execute Rollback**: Revert to previous stable version
4. **Communicate**: Notify stakeholders immediately
5. **Investigate**: Analyze root cause
6. **Plan Recovery**: Develop fix and re-release strategy

### Rollback Commands

```bash
# Revert to previous version
git revert <release-commit-hash>

# Create emergency hotfix
git checkout -b hotfix/emergency-fix <previous-stable-tag>

# Fast-track release
npm run release
npm run release:tag
```

## Environment Management

### Development Environment

- Continuous integration on feature branches
- Automated testing and validation
- Pre-commit hooks for code quality
- Development dependencies isolated

### Staging Environment

- Release candidate deployment
- Integration testing environment
- Performance benchmarking
- User acceptance testing

### Production Environment

- Stable release deployment
- Monitoring and alerting
- Backup and recovery procedures
- Performance optimization

## Security Considerations

### Dependency Management

- Regular security audits
- Automated vulnerability scanning
- Dependency update strategy
- License compliance monitoring

### Release Security

- Code signing for releases
- Secure token management
- Access control for release process
- Audit trail maintenance

## Troubleshooting

### Common Release Issues

#### Release PR Not Created

Possible causes:
- No conventional commits since last release
- Configuration file errors
- Token permissions insufficient

Solutions:
1. Verify commit message format
2. Check release-please-config.json syntax
3. Validate GitHub token permissions

#### Incorrect Version Bump

Possible causes:
- Incorrect commit message format
- Missing breaking change indicators
- Configuration mismatch

Solutions:
1. Review commit history for conventional format
2. Check for `!` suffix or `BREAKING CHANGE:` footer
3. Validate configuration settings

#### Changelog Missing Entries

Possible causes:
- Commits on wrong branch
- Hidden commit types
- Date range issues

Solutions:
1. Ensure commits are on main branch
2. Review hidden sections configuration
3. Check release date ranges

#### Failed GitHub Release

Possible causes:
- Network connectivity issues
- Permission problems
- Tag conflicts

Solutions:
1. Verify network connection
2. Check GitHub token permissions
3. Resolve tag naming conflicts

### Emergency Procedures

#### Critical Security Issue

1. **Immediate Response**
   - Assess vulnerability scope
   - Implement temporary mitigations
   - Coordinate with security team

2. **Hotfix Development**
   - Create isolated fix branch
   - Minimal code changes only
   - Expedited review process

3. **Emergency Release**
   - Fast-track release process
   - Skip non-critical validations
   - Immediate deployment

4. **Post-Incident**
   - Conduct security review
   - Update security procedures
   - Communicate with stakeholders

## Best Practices

### Release Planning

- Regular release schedule
- Feature freeze periods
- Stakeholder communication
- Risk assessment and mitigation

### Quality Assurance

- Comprehensive testing strategy
- Automated quality gates
- Manual validation procedures
- Performance benchmarking

### Communication

- Release notes for users
- Technical documentation for developers
- Breaking change migration guides
- Stakeholder notifications

## Monitoring and Metrics

### Release Metrics

- Release frequency
- Lead time for changes
- Mean time to recovery
- Change failure rate

### Quality Metrics

- Test coverage percentage
- Bug escape rate
- Performance regression count
- Security vulnerability count

### Process Metrics

- Release process duration
- Manual intervention frequency
- Rollback occurrence rate
- Stakeholder satisfaction
