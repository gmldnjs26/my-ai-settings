---
name: git-workflow
description: "Git commit, push, and PR creation skill using gh CLI. This skill should be used when the user asks to commit changes, push to remote, or create a pull request. Follows Conventional Commits convention and commits under the user's identity only."
---

# Git Workflow

Manage git commits, pushes, and pull requests using `gh` CLI with Conventional Commits convention.

## When to Use

- The user asks to commit, push, or create a PR
- The user asks to review and commit staged/unstaged changes
- The user invokes `/git-workflow`

## Important Rules

- **Never include Claude co-author information.** All commits must be authored solely under the user's git identity. Do not append `Co-Authored-By` lines.
- **Always confirm with the user** before executing `git commit`, `git push`, or `gh pr create`.
- **Never run destructive git commands** (`reset --hard`, `push --force`, `clean -f`) without explicit user request.
- **Never skip hooks** (`--no-verify`) unless the user explicitly asks.

## Workflow

### 1. Analyze Changes

Gather the current state before composing a commit:

```bash
git status
git diff
git diff --cached
git log --oneline -10
```

Identify:
- Which files are staged vs unstaged vs untracked
- The nature of each change (new feature, bug fix, refactor, etc.)
- Whether changes should be split into multiple commits

### 2. Compose Commit Message

Follow **Conventional Commits** convention. Load `references/conventional-commits.md` for the full specification.

Rules for composing the message:
- Select the appropriate type (`feat`, `fix`, `docs`, `refactor`, etc.) based on the actual change
- Add a scope when the change targets a specific module or area
- Write the description in imperative mood, lowercase, no period, under 72 characters
- Add a body when the description alone is insufficient to explain the change
- If changes span multiple unrelated concerns, propose splitting into separate commits
- Use a HEREDOC to pass the commit message to avoid shell escaping issues:

```bash
git commit -m "$(cat <<'EOF'
<type>[scope]: <description>

<optional body>
EOF
)"
```

### 3. Push

After committing, push to the remote:

```bash
# Check if current branch tracks a remote
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null

# Push (set upstream if needed)
git push
# or
git push -u origin <branch-name>
```

### 4. Create Pull Request

Use `gh` CLI to create a PR:

```bash
gh pr create --title "<type>[scope]: <short title>" --body "$(cat <<'EOF'
## Summary
<1-3 bullet points describing the changes>

## Changes
<list of specific changes>

## Test Plan
<how to verify the changes>
EOF
)"
```

PR guidelines:
- Title follows Conventional Commits format, under 72 characters
- Body includes Summary, Changes, and Test Plan sections
- Base branch defaults to `main` unless the user specifies otherwise
- Add `--draft` flag if the user wants a draft PR

### 5. Composite Operations

When the user asks to "commit and push" or "commit, push, and create a PR," execute the steps sequentially, confirming the commit message before proceeding.

## Edge Cases

- **No changes detected**: Inform the user that there are no changes to commit.
- **Merge conflicts**: Do not auto-resolve. Inform the user and wait for instructions.
- **Detached HEAD**: Warn the user before committing.
- **Pre-commit hook failure**: Fix the issue, re-stage, and create a **new** commit (never amend).
