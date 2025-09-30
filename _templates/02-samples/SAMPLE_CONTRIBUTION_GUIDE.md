# Sample Contribution Guide

Thank you for contributing samples to the Strands Agents repository!

## General Contribution Guidelines

Please review the repository [CONTRIBUTING.md](../../CONTRIBUTING.md) which covers:

- **Reporting Bugs/Feature Requests** - Use GitHub issue tracker
- **Contributing via Pull Requests** - Fork, modify, test, and submit PRs
- **Code of Conduct** - [Amazon Open Source Code of Conduct](https://aws.github.io/code-of-conduct)
- **Security Issues** - Report via [AWS vulnerability reporting](http://aws.amazon.com/security/vulnerability-reporting/)
- **Licensing** - See [LICENSE](../../LICENSE) file

### Pull Request Workflow

1. Fork the repository
2. Work against the latest source on the *main* branch
3. Check existing PRs to avoid duplicate work
4. Open an issue to discuss significant work
5. Modify source, focusing on specific changes
6. Ensure local tests pass
7. Commit with clear messages
8. Submit PR and include `Fixes #<issue-number>` if applicable
9. Respond to automated CI failures and stay engaged

## Required Reading for Sample Contributors

Before submitting a sample, please review these template files:

1. **[readme.md](./readme.md)** - Documentation standards and README structure
2. **[structure.md](./structure.md)** - Directory organization and file templates

## Pre-Submission Checklist

Before submitting your sample:

- [ ] Review [readme.md](./readme.md) for documentation requirements
- [ ] Review [structure.md](./structure.md) for proper directory structure
- [ ] All features and dependencies exist and are documented
- [ ] Sample works end-to-end with fresh installation
- [ ] No hardcoded credentials, API keys, or AWS Account IDs
- [ ] Documentation accurately reflects implementation
- [ ] All README examples tested and work
- [ ] Architecture diagrams included
- [ ] Cleanup scripts tested (if AWS resources used)

## What Reviewers Check

### Functionality
- Sample runs without errors
- All features work as documented
- Examples execute successfully

### Documentation
- Accurate and complete
- Clear setup instructions
- Working code examples
- Follows [readme.md](./readme.md) standards

### Code Quality
- Follows best practices
- Proper error handling
- No security issues
- Follows [structure.md](./structure.md) organization

### Consistency
- Matches repository patterns
- Uses correct terminology ("Strands Agents")
- Directory structure follows templates

## Iterating on Feedback

When reviewers request changes:

1. Review feedback carefully
2. Ask questions if unclear
3. Make requested changes
4. Test thoroughly after changes
5. Update documentation to match code changes

## Quick Links

- [Main CONTRIBUTING.md](../../CONTRIBUTING.md) - General contribution guidelines
- [readme.md](./readme.md) - Documentation standards
- [structure.md](./structure.md) - Directory structure templates
- [Strands Agents Documentation](https://strandsagents.com) - Official documentation

---

Thank you for your contribution! Your samples help developers learn and build with Strands Agents.
