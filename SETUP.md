# Getting Wagvive onto GitHub (and working from any device)

Written assuming you have never used git or GitHub. Nothing here touches the
live store — you cannot break Wagvive by following these steps. The worst
outcome is a repo that needs deleting and redoing.

**What you get at the end:** work on this project from your phone, iPad, or any
computer, plus a job that keeps stock and margins correct every 6 hours whether
or not any of your devices are awake.

---

## The OneDrive problem — already solved, nothing for you to do

This project lives inside OneDrive, and OneDrive can corrupt git's internal
files. Personal OneDrive only lets you exclude file *extensions*, not folders,
so the obvious fix is not available.

**What was done instead:** git's database was moved to
`C:\Users\mattm\git-repos\wagvive.git`, outside OneDrive, and the `.git` entry
in this folder is now a one-line pointer to it. Your project files stay where
they are and keep syncing to OneDrive normally; the part OneDrive could damage
is out of its reach.

Practical consequences:
* Everything works exactly as before — `git` commands, Claude, all of it.
* **If you ever move or rename this project folder**, the pointer breaks. Tell
  me and it is a one-line fix, not a disaster.
* That `git-repos` folder is now worth keeping. Once the code is on GitHub,
  GitHub is the real backup, so even losing it is recoverable.

---

## Step 1 — Install git (if you don't have it)

Open PowerShell and type:

```
git --version
```

If it prints a version, skip ahead. If not, download from
<https://git-scm.com/download/win>, run the installer, and accept every default.

## Step 2 — Create a free GitHub account

<https://github.com/signup>. Use an email you'll keep.

## Step 3 — Create the private repository

1. Go to <https://github.com/new>
2. **Repository name:** `wagvive`
3. **Private** — this is important, tick it
4. Do **not** tick "Add a README", "Add .gitignore" or "Choose a license" —
   the repo already has these locally and the extra files cause a conflict
5. Click **Create repository**

GitHub then shows a page with commands. Ignore them; use the ones below.

## Step 4 — Connect and upload

In PowerShell, run these one at a time. Replace `YOURNAME` with your GitHub
username:

```
cd "C:\Users\mattm\OneDrive\Claude Code\Pet Store"
```

```
git remote add origin https://github.com/YOURNAME/wagvive.git
```

```
git branch -M main
```

```
git push -u origin main
```

A browser window will open asking you to sign in to GitHub. Do that, and the
upload runs. It should take under a minute.

**If it says "remote origin already exists":** run
`git remote set-url origin https://github.com/YOURNAME/wagvive.git` and retry
the push.

## Step 5 — Add the secrets

The store token and CJ key are deliberately NOT in the repo. The scheduled job
needs them, stored encrypted.

Go to your repo → **Settings** → **Secrets and variables** → **Actions** →
**New repository secret**. Add these six, one at a time. The values are in
`config/shopify.env` and `config/cj.env` on your PC — open those in Notepad and
copy the part after each `=`.

| Secret name | Where the value comes from |
|---|---|
| `SHOPIFY_ADMIN_API_TOKEN` | config/shopify.env |
| `SHOPIFY_STORE_DOMAIN` | config/shopify.env |
| `SHOPIFY_API_VERSION` | config/shopify.env |
| `CJ_EMAIL` | config/cj.env |
| `CJ_API_KEY` | config/cj.env |
| `CJ_API_BASE` | config/cj.env |

Names must match exactly, including capitals and underscores.

## Step 6 — Test the scheduled job once, by hand

Repo → **Actions** tab → **Scheduled store operations** → **Run workflow** →
green **Run workflow** button.

Watch it run. Green tick means everything works. If it fails, click into the run
and read the red step — the workflow tells you exactly which secret is missing if
that is the problem. Send me the error and I'll fix it.

From then on it runs every 6 hours on its own. **GitHub emails you when a run
fails**, which is your early warning that stock has drifted or a product has
fallen below the 50% margin floor.

## Step 7 — Working from your phone / iPad / another computer

Go to <https://claude.ai/code>, sign in, and pick the `wagvive` repo. Claude
starts with `CLAUDE.md` already loaded, so it knows the margin rules, the
inventory traps and the whole operating history — no re-explaining.

**What works anywhere:** catalogue edits, pricing, product research, copy,
email templates, audits, anything that talks to the Shopify or CJ APIs.

**What still needs your PC:** CJ product pairing (CJ has no API — it must be
driven in your logged-in Chrome) and visual storefront QA. Plan to do those in
occasional sessions at a real computer.

---

## Everyday use, once set up

You do not need to learn git properly. Three commands cover almost everything,
run from the project folder:

```
git add -A
```
```
git commit -m "describe what changed"
```
```
git push
```

Or just ask me and I'll do it.

## If something looks wrong

Nothing in git is truly lost — every commit is recoverable. If you think you have
broken something, stop and ask rather than trying to undo it. The live store is
never affected by anything that happens in the repo; the only thing that touches
Wagvive is the scheduled job, and that only performs the two safe repairs.
