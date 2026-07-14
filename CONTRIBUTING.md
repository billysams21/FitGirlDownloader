# Contributing to SilverSpoon

First off, thank you for considering contributing to SilverSpoon! It's people like you that make such tools better.

## How to Contribute

### 1. Branching Strategy
* **Always branch off the `dev` branch.** The `main` branch is reserved for stable releases.
* Create a descriptive branch name for your feature or bug fix (e.g., `feature/add-new-host`, `bugfix/fix-extraction-error`).

### 2. Making Changes
* Ensure your code follows the existing style and conventions of the project.
* Keep your commits atomic and write clear, concise commit messages.
* Do not introduce new dependencies unless absolutely necessary. If you do, make sure to update `requirements.txt`.

### 3. Testing
* **Carefully test your changes.** Since this tool interacts with external websites and file systems, manual testing is crucial.
* Test the core functionalities (adding links, pausing, resuming, extraction, UI behavior, persistent settings) to ensure your changes haven't broken anything else.
* If you are fixing a specific bug, verify that the issue is fully resolved before submitting.

### 4. Submitting a Pull Request
* Push your branch to your fork on GitHub.
* Open a Pull Request targeting the **`dev`** branch of the main repository.
* Provide a clear description of the problem you solved or the feature you added in the PR description. Include screenshots if you made UI changes!

### 5. Reporting Bugs & Requesting Features
If you're not ready to write code but found a bug or have a great idea:
* Please check the existing Issues to see if it has already been reported.
* Open a new Issue providing as much detail as possible (steps to reproduce, expected behavior, OS version, etc.).

Thank you for your help in improving SilverSpoon!