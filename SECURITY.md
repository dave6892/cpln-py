# Security Policy

## Supported Versions

We currently support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of `cpln-py` seriously. If you believe you have found a security vulnerability, please follow these steps:

1. **Do Not** disclose the vulnerability publicly
2. Email the details to dave6892@gmail.com
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (if available)

We will:
- Acknowledge receipt of your report within 48 hours
- Provide a more detailed response within 7 days
- Keep you informed of our progress
- Credit you in the security advisory (if you wish)

## Security Best Practices

### API Token Management

1. **Never commit API tokens to version control**
   - Store tokens in environment variables
   - Use `.env` files locally (ensure they are in `.gitignore`)
   - Use secure secret management in production

2. **Token Rotation**
   - Regularly rotate your Control Plane API tokens
   - Revoke compromised tokens immediately
   - Use the minimum required permissions for tokens

### Environment Setup

1. **Required Environment Variables**
   ```env
   CPLN_TOKEN=your_service_account_key_here
   CPLN_ORG=your_organization_name
   CPLN_BASE_URL=https://api.cpln.io  # Optional
   ```

2. **Security Considerations**
   - Keep your `.env` file secure and never share it
   - Use different tokens for development and production
   - Regularly audit token usage and permissions

### Code Security

1. **Input Validation**
   - Always validate input parameters
   - Sanitize user-provided data
   - Use type hints and validation

2. **Error Handling**
   - Never expose sensitive information in error messages
   - Log errors securely
   - Handle API errors gracefully

### Development Security

1. **Dependencies**
   - Keep dependencies up to date
   - Use `pdm install` to install dependencies
   - Regularly check for security vulnerabilities

2. **Code Quality**
   - Run security linters (`ruff`)
   - Use type checking (`mypy`)
   - Follow security best practices in code reviews

## Security Features

The library implements several security features:

1. **Authentication**
   - Bearer token authentication
   - Secure token handling
   - Environment-based configuration

2. **API Security**
   - HTTPS by default
   - Proper error handling
   - Input validation

3. **Development Tools**
   - Security-focused linting
   - Type checking
   - Pre-commit hooks

## Updates and Notifications

- Security updates will be released as patch versions
- Critical security fixes will be backported to supported versions
- Security advisories will be published in the repository's security tab

## Additional Resources

- [Control Plane Security Documentation](https://docs.controlplane.com/security)
- [Python Security Best Practices](https://docs.python.org/3/security/index.html)
- [OWASP Python Security](https://owasp.org/www-project-python-security/)
