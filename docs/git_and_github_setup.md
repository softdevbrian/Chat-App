# Git and GitHub Setup & Push Guide

This document records the exact steps and commands taken to link the local repository to the **softdevbrian/Chat-App** GitHub account, resolve remote account permission conflicts, and push the initial project files.

---

## 1. Context & The Initial Conflict

When we inspected the existing local git configuration:
- Local git user: `softdevbrian` (`softdevbriankuria@gmail.com`)
- Existing remote URL: `https://github.com/StaticBuilder/CHAT_APP.git`

When attempting to push to the previous `StaticBuilder` remote, GitHub returned a permission error:
```text
remote: Permission to StaticBuilder/CHAT_APP.git denied to softdevbrian.
fatal: unable to access 'https://github.com/StaticBuilder/CHAT_APP.git/': The requested URL returned error: 403
```

**Why this happened:**
Windows Git Credential Manager was signed in with credentials for the `softdevbrian` account. Because `softdevbrian` did not have write permissions to the `StaticBuilder` repository, GitHub rejected the push with `403 Forbidden`.

To resolve this, we redirected the local repository's `origin` remote to your newly created repository under `softdevbrian/Chat-App`.

---

## 2. Step-by-Step Commands Executed

### Step 1: Inspect Current Status and Remotes
Before changing anything, we checked the local repository status and existing remotes:
```powershell
# Check tracked and untracked changes
git status

# Check the current fetch and push URLs
git remote -v

# Check who git thinks you are locally
git config user.name
git config user.email
```
*Output showed the remote was pointing to `StaticBuilder/CHAT_APP.git`.*

---

### Step 2: Change the Remote URL to the New Repository
Instead of deleting and re-initializing git, we updated the existing `origin` remote to point to `softdevbrian/Chat-App`:
```powershell
git remote set-url origin https://github.com/softdevbrian/Chat-App.git
```

**What this does:**
`git remote set-url <remote_name> <new_url>` updates the destination address for `origin` without touching your local commit history or branch structure.

---

### Step 3: Verify the Remote Was Updated
```powershell
git remote -v
```
**Output:**
```text
origin  https://github.com/softdevbrian/Chat-App.git (fetch)
origin  https://github.com/softdevbrian/Chat-App.git (push)
```

---

### Step 4: Push to GitHub and Set Upstream Tracking
We pushed the local `main` branch to the remote repository and configured upstream tracking:
```powershell
git push -u origin main
```

**What `-u` (or `--set-upstream`) does:**
- Links your local branch `main` to the remote branch `origin/main`.
- For all future pushes on this branch, you only need to run `git push` instead of typing `git push origin main` every time.

**Output:**
```text
branch 'main' set up to track 'origin/main'.
To https://github.com/softdevbrian/Chat-App.git
 * [new branch]      main -> main
```

---

### Step 5: Verify Final Clean State
```powershell
git status
```
**Output:**
```text
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

---

## 3. Quick Reference for Future Work

Whenever you make changes in future phases:

### Adding and Committing Changes:
```powershell
git add .
git commit -m "Complete Phase X: <Description of changes>"
```

### Pushing to GitHub:
```powershell
git push
```

### Checking Account Credentials on Windows (If switching accounts):
If you ever need to switch between `StaticBuilder` and `softdevbrian` on Windows:
1. Open the Windows Start menu and search for **Credential Manager**.
2. Go to **Windows Credentials**.
3. Under **Generic Credentials**, find `git:https://github.com`.
4. Click **Remove** or **Edit** to force Git Credential Manager to re-prompt you for login on the next push.
