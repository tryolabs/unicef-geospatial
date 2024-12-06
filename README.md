# Repo Template

Kick off a project with the right foot.

A repository template for easily setting up a well behaved development environment for a smooth
collaboration experience.

This template takes care of setting up and configuring:

- A **virtual environment**
- **Formatting and linting** tools
- Some shared default **VSCode settings**
- A **Pull Request template**
- A **GitHub Action** that runs formatting and linting checks
- **Dependabot** for keeping your dependencies up to date
- A **Test Coverage Check** that runs your test suite.
- A **Pre-commit Hook** that runs ruff formatting, checks for large files and detects secrets

Any of these configurations and features can be disabled/modified freely after set up if the team
chooses to.

Note: [pyenv](https://github.com/pyenv/pyenv#installation) and
[poetry](https://python-poetry.org/docs/#installation) are used for setting up a virtual environment
with the correct python version. Make sure both of those are installed correctly in your machine.

# Usage

1. Click the `Use this template` button at the top of this repo's home page to spawn a new repo
   from this template.

2. Clone the new repo to your local environment.

3. Run `sh init.sh <your_project_name> <python version>`.

   Note that:

   - the project's accepted python versions will be set to `^<python version>` - feel free
     to change this manually in the `pyproject.toml` file after running the script.
   - your project's source code should be placed in the newly-created folder with your project's
     name, so that absolute imports (`from my_project.my_module import func`) work everywhere.

4. Nuke the `init.sh` file.

5. Add to git the changes made by the init script, such as the newly created `poetry.toml`,
   `poetry.lock`, `.python-version` and `.secrets-baseline` files.

6. Commit and push your changes - your project is all set up.

7. [Recommended] Set up the following in your GitHub project's `Settings` tab:
   - Follow the guidelines suggested in the **Branch Management** section.
   - Go to `Code security and analysis`, and enable the Dependency Graph and all
     desired functionalities of Dependabot. This includes version updates, security updates,
     and more. All alerts will be shown in the `Security` tab, inside Dependabot. Go to the
     **Dependabot Summary** for more information regarding Dependabot.

# For ongoing projects

If you want to improve the current configs of an existing project, these files are the ones you'll
probably want to steal some content from:

- [VSCode settings](.vscode/settings.json)
- [Dependabot config](.github/dependabot.yml)
- [Ruffconfigs](pyproject.toml)
- [Style check GitHub Action](.github/workflows/style-checks.yaml)
- [Pytest coverage Github Action](.github/workflows/test-coverage.yaml)
- [Pre-commit hook](.pre-commit-config.yaml)
- [Detect-secrets](.pre-commit-config.yaml)

Additionally, you might want to check the
[project's source code is correctly installed via Poetry](https://stackoverflow.com/questions/66586856/how-can-i-make-my-project-available-in-the-poetry-environment)
for intra-project imports to work as expected across the board.

# For developers of this template

To test new changes made to this template:

1. Run the template in test mode with `test=true sh init.sh <your_project_name> <python version>`,
   which will not delete the [project_base/test.py](project_base/test.py) file from the source
   directory.

2. Use that file to check everything works as expected (see details in its docstring).

3. Make sure not to version any of the files created by the script. `git reset --hard` + manually
   deleting the created files not yet added to versioning works, for example.

# Issues and suggestions

Feel free to report issues or propose improvements to this template via GitHub issues or through the
`#team-tech-meta` channel in Slack.

# Can I use it without Poetry?

This template currently sets up your virtual environment via poetry only.

If you want to use a different dependency manager, you'll have to manually do the following:

1. Remove the `.venv` environment and the `pyproject.toml` and `poetry.lock` files.
2. Create a new environment with your dependency manager of choice.
3. Install ruff and docstr-coverage as dev dependencies.
4. Install the current project's source.
5. Set the path to your new environment's python in the `python.pythonPath` and
   `python.defaultInterpreterPath` in [vscode settings](.vscode/settings.json).

Disclaimer: this has not been tested, additional steps may be needed.

# Troubleshooting

### pyenv not picking up correct python version from .python-version

Make sure the `PYENV_VERSION` env var isn't set in your current shell
(and if it is, run `unset PYENV_VERSION`).

# Tools

## Dependabot Summary

**Dependabot** is a GitHub tool that helps keep dependencies up-to-date by automatically checking for and creating pull requests for dependency updates. It enhances security and stability by ensuring that dependencies are not outdated or vulnerable.

### Key Parts of `dependabot.yml`

1. **Updates**:
   This section defines the dependencies to be checked and updated.

   ```yaml
   updates:
     - package-ecosystem: "pip"
       directory: "/" # Root directory of the project
       schedule:
         interval: "daily" # or "weekly", "monthly"
   ```

2. **Target Branch**:

   ```yaml
   target-branch: "main"
   ```

   Specifies the branch where Dependabot will create pull requests.

3. **Ignore**:
   To ignore specific dependencies or versions:

   ```yaml
   ignore:
     - dependency-name: "example-dependency"
       versions: ["1.x"]
   ```

4. **Pull Request Limit**:
   Controls the maximum number of open pull requests Dependabot will create.
   ```yaml
   open-pull-requests-limit: 5
   ```
   Important: If set to 0, this prevents Dependabot from opening PRs and from running any non-security analysis. This means you won't get any version bump notifications until you allow Dependabot to open PRs.

### Dependabot Secrets

Dependabot secrets are used to provide sensitive information (like authentication tokens) that Dependabot needs to access private repositories or registries. They are stored securely in GitHub's repository settings.

**Setting Dependabot Secrets**:

1. Navigate to the repository on GitHub.
2. Go to **Settings** > **Secrets and variables** > **Dependabot**.
3. Click **New repository secret**.
4. Add the secret name and value, then click **Add secret**.

For more information, go to https://docs.github.com/en/code-security/dependabot

## Detect-secrets

detect-secrets helps identify and manage secrets in your codebase. It runs automatically as a pre-commit hook to prevent accidental commits of sensitive information, such as API keys, passwords, credentials and tokens

### Handling False Positives

If a false positive or acceptable key is flagged, update the baseline with:

```sh
poetry run detect-secrets scan --baseline .secrets.baseline
```

or recreate the secrets-baseline with:

```sh
poetry run detect-secrets scan > .secrets.baseline
```

This ensures the specific secret won't trigger future alerts.

# Branch Management (Recommended)

## Why Use `dev` and `main` Branches?

Using separate `dev` and `main` branches helps maintain a clean and stable codebase. Here are the key reasons:

1. **Stability**: The `main` branch remains stable and production-ready, containing only thoroughly tested and approved changes.
2. **Isolation**: Development happens in the `dev` branch, allowing for continuous integration and testing without affecting the main codebase.
3. **Controlled Releases**: Changes are promoted from `dev` to `main` only after they meet quality standards, ensuring reliable releases.

### Setting Up the Workflow

1. **Create the Branches**:

   ```bash
   git switch --create dev
   git push origin dev
   ```

2. **Set Up Branch Protection Rules**:

   - Navigate to **Settings** > **Branches**.
   - Under "Branch protection rules", click **Add classic branch protection rule**.
   - Specify `*` as the branch name pattern.
   - Check the following options to enforce rules:
     - **Require a pull request before merging**
       - **Require pull request reviews before merging**
     - **Require status checks to pass before merging**
       - **Require branches to be up to date before merging**
   - Save changes.

3. **Set Up Branch Protection Rules for `main`**:
    - Under "Branch protection rules", click **Add classic branch protection rule**.
    - Specify `main` as the branch name pattern.
    - Check the following options to enforce rules:
      - **Require a pull request before merging**
        - **Require pull request reviews before merging**
      - **Require status checks to pass before merging**
        - **Require branches to be up to date before merging**
      - Additionally, check:
        - **Dismiss stale pull request approvals when new commits are pushed**
    - Save changes.

4. **General Configurations**:

   - Navigate to **Settings**
   - Under **Pull Requests**, check:
     - **Automatically delete head branches**

5. **Merge Workflow**:
   - Develop features and fixes in feature branches branched off from `dev`.
   - Merge feature branches into `dev` via pull requests. We recommend using **rebase and merge** for these merges to maintain a linear history.
   - Once `dev` is stable and tested, create a pull request to merge `dev` into `main`.
   - Review and approve the pull request, then merge it to main using squash and merge for a cleaner history, atomic changes, reduced noise and easier backporting.

## Branch Naming Conventions

Adopting a consistent branch naming convention improves the clarity and manageability of your repository. Here are some recommended conventions:

1. **Feature Branches**:

   - Naming: `feature/<short-description>`
   - Example: `feature/user-authentication`
   - Use for new features or enhancements.

2. **Bug Fixes**:

   - Naming: `bugfix/<short-description>`
   - Example: `bugfix/login-error`
   - Use for fixing bugs or issues.

3. **Hotfixes**:

   - Naming: `hotfix/<short-description>`
   - Example: `hotfix/critical-security-patch`
   - Use for urgent fixes that need to be applied to the `main` branch immediately.

4. **Release Branches**:

   - Naming: `release/<version-number>`
   - Example: `release/1.0.0`
   - Use for preparing a new production release.

5. **Chore/Documentation**:
   - Naming: `chore/<short-description>` or `docs/<short-description>`
   - Example: `chore/cleanup-scripts` or `docs/update-readme`
   - Use for maintenance tasks or documentation updates.

### Bonus: Commit Naming Conventions:

The description contains a concise description of the change.

- Use the imperative, present tense: "change" not "changed" nor "changes"
- Think of "This commit will..." or "This commit should..."
- Don't capitalize the first letter
- No dot (.) at the end
- Ideally, wrap your first line to 50 characters.
- Add more context! Add a blank line after the first summary line, and then write all details below (wrapped to 72 characters if possible, though URLs and things like that can obviously go past this limit).
