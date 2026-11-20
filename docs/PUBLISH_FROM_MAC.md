# Publish From The Validated Source

No Git was initialized and nothing was committed, pushed, or published during
authoring. The following is a later user workflow, not execution permission here.

## Establish One Authority

First complete manifest metadata and validate on the Ubuntu ARM64 target. Record
the exact source identity, build/test commands, real outputs, environment, and date.
Choose one authoritative source repository: either maintain it in the VM, or
publish a reviewed Mac copy synchronized from the actual tested VM source tree.
Do not independently edit Mac and VM copies and assume they remain equivalent.

Recommended first publication: copy only the tested sources and documentation
from Ubuntu into a fresh Mac staging directory, compare them with the tested tree,
then make that the authority. Exclude build/install/log, recordings, caches, keys,
.env files, and transfer archives. A --symlink-install output is not portable source.
If tests led to changes only in the VM, publish those changes, not the older ZIP.

## Publication Gates

- License: Apache-2.0, chosen by the maintainer. LICENSE holds the full text;
  package.xml and setup.py declare it consistently.
- Provide genuine maintainer metadata and review any public contact exposure.
- Ensure no personal recordings, author-path leaks, secrets, binaries, or generated
  dependencies are staged. Ignore rules alone are not a privacy/security guarantee.
- Keep NOT RUN for every unsupported claim, including optional visualization and
  CI. Passing one unit test is not full system validation or physical safety.
- Review the future workflow before enabling public actions. Hosted x86_64 results
  do not replace ARM64 or interactive SSH checks.

## User-Only Git Steps

From the chosen reviewed source copy on the Mac, after the gates above:

```bash
git init
git status --short
git add .editorconfig .gitattributes .gitignore README.md CONTRIBUTING.md .github docs scripts src
git diff --cached --stat
git diff --cached
```

Add the chosen LICENSE explicitly once it exists. Review staged contents, not only
names. Never use `git add -A` as a shortcut for a source/privacy review. Configure
your own real Git identity privately, then commit with an accurate message and date.
Do not imply target validation if it has not happened. No remote, account name,
commit identity, license holder, or publication URL is invented in this repository.

Create the desired remote yourself and review its visibility before pushing.
Publishing the workflow can cause GitHub to run it on future pushes/PRs; that is
separate from this authoring-only task. Maintain one synchronization direction
until a deliberate branch/merge workflow is established.
