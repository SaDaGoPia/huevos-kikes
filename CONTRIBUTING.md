# Contributing

Thanks for your interest in improving this project. Follow these guidelines to keep contributions consistent.

## Getting started
- Fork and clone the repo.
- Create a virtual environment and install dependencies: `pip install -r requirements.txt`.
- Copy `.env.example` to `.env` and set `SECRET_KEY`, `DEBUG=True`. For SMTP, set `EMAIL_HOST_USER/PASSWORD` if needed.
- Run migrations: `python manage.py migrate`.
- Create a superuser: `python manage.py createsuperuser`.
- Run the app: `python manage.py runserver`.

## Branching and commits
- Use feature branches: `feat/<short-desc>` or `fix/<short-desc>`.
- Write clear commit messages.
- Keep PRs focused and small.

## Checks before opening a PR
- `python manage.py check`
- (Optional) `python -m compileall .` to catch syntax errors.

## Pull request guidelines
- Describe the change, motivation, and testing steps.
- Link related issues.
- If you modify UI, add a brief before/after summary.

## Code style
- Prefer readability and explicitness.
- Keep templates and views consistent with existing patterns.

## Security
- Do not commit secrets. Use environment variables.
- For new endpoints, ensure authentication/authorization is enforced.

## Reporting issues
- Use the issue templates (bug/feature) and provide reproduction steps when possible.
