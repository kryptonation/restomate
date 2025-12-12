# Documentation Index - FoodFleet

## Overview

This directory contains comprehensive documentation for the FoodFleet project, covering semantic versioning, release management, and development guidelines.

## Documentation Structure

### Core Documentation

#### [Semantic Versioning Guide](./SEMANTIC_VERSIONING.md)
Complete guide to semantic versioning implementation in FoodFleet, including:
- Version number format and meaning
- Current project configuration
- Version increment rules
- Pre-major version behavior
- Best practices for contributors and maintainers

#### [Release Management](./RELEASE_MANAGEMENT.md)
Detailed documentation of the release management process:
- Release Please configuration and workflow
- Automated and manual release procedures
- Changelog management and organization
- Release validation and rollback procedures
- Environment management and security considerations

#### [Conventional Commits Guide](./CONVENTIONAL_COMMITS.md)
Comprehensive guide to conventional commit messages:
- Commit message structure and components
- Breaking change notation
- Detailed examples and patterns
- Integration with automated versioning
- Validation tools and troubleshooting

## Quick Reference

### Current Version Status
- **Current Version**: 0.0.1 (package.json)
- **Manifest Version**: 0.0.0 (release-please-manifest.json)
- **Release Type**: Node.js project
- **Pre-major Behavior**: Enabled

### Key Commit Types

| Type | Version Impact | Example |
|------|----------------|---------|
| `feat:` | Minor | `feat(auth): add OAuth login` |
| `fix:` | Patch | `fix(api): resolve validation error` |
| `feat!:` | Major | `feat!: redesign user API` |
| `chore:` | None | `chore(deps): update dependencies` |

### Release Commands

```bash
# Create release pull request
npm run release

# Create GitHub release and tag  
npm run release:tag
```

## Project Structure Context

### Configuration Files
- `package.json` - Contains current version and release scripts
- `release-please-config.json` - Release Please configuration
- `release-please-manifest.json` - Version state tracking

### Release Integration
- Automated PR generation based on conventional commits
- Semantic version calculation from commit history
- Changelog generation with organized sections
- GitHub release creation with tags

## Getting Started

### For New Contributors

1. Read the [Conventional Commits Guide](./CONVENTIONAL_COMMITS.md)
2. Understand the commit message format requirements
3. Review the [Semantic Versioning Guide](./SEMANTIC_VERSIONING.md) for version impact
4. Follow the guidelines for your contribution type

### For Maintainers

1. Review the [Release Management](./RELEASE_MANAGEMENT.md) documentation
2. Understand the automated release workflow
3. Set up necessary GitHub tokens and permissions
4. Establish team processes for release validation

### For Project Setup

1. Ensure Release Please is configured correctly
2. Validate GitHub integration and permissions
3. Set up commit message validation (optional)
4. Configure CI/CD pipeline for automated releases

## Best Practices Summary

### Commit Messages
- Use conventional commit format strictly
- Include clear, descriptive messages
- Reference issues and pull requests
- Document breaking changes thoroughly

### Version Management
- Follow semantic versioning principles
- Review generated changelogs carefully
- Validate version increments before release
- Communicate breaking changes to users

### Release Process
- Use automated workflows when possible
- Perform thorough testing before releases
- Maintain comprehensive documentation
- Monitor releases for issues post-deployment

## Troubleshooting Resources

### Common Issues
- Version mismatch between files
- Missing changelog entries
- Incorrect version bumps
- Failed release creation

### Support Contacts
- Technical issues: Development team
- Process questions: Project maintainers
- Documentation updates: Technical writers

## Additional Resources

### External Documentation
- [Semantic Versioning Specification](https://semver.org/)
- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Release Please Documentation](https://github.com/googleapis/release-please)

### Project Resources
- [GitHub Repository](https://github.com/Sriditha-Technologies/FoodFleet)
- [Issue Tracker](https://github.com/Sriditha-Technologies/FoodFleet/issues)
- [Pull Requests](https://github.com/Sriditha-Technologies/FoodFleet/pulls)

## Document Maintenance

### Update Schedule
- Review quarterly for accuracy
- Update after major process changes
- Revise based on team feedback
- Validate against current configuration

### Version History
- Initial documentation: October 2024
- Last updated: October 18, 2024
- Next review: January 2025

### Contributing to Documentation
- Follow conventional commits for documentation changes
- Use `docs:` prefix for documentation updates
- Include clear descriptions of changes
- Review with team before merging

For questions about this documentation or suggestions for improvements, please create an issue in the project repository.
