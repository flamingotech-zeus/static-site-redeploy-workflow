# Static Site Redeploy Workflow

[English](README.md) | [简体中文](README.zh-CN.md)

> A standard procedure for pushing image and page changes to a live static site, from local edit to verified live state.

## What this is

> **Note on de-identification.** This README is written generically. The skill file itself may still reference internal domains, host names or local absolute paths. Run a scan pass (see `opensource-preflight-audit`) and replace them before publishing.

This is not an upload step. Uploading is the easy part and it is not where the problems come from.

The failure this procedure is built to eliminate: the local version looks right, the server version does not, and the cause is something invisible — a stale cache fingerprint, a file that was skipped in a batch upload, or a valid file placed in the wrong directory. The workflow front-loads the verification so that state cannot persist unnoticed.

## Why we open-sourced it

We run static sites and change them often. Every so often a change would appear to go live and then not, and the cause was always one of the same three things.

Writing the procedure down turned a recurring mystery into a checklist. It is internal workflow knowledge with no proprietary content once the specifics are replaced with placeholders.

## What it does

- **Panel takeover over the debugging protocol.** Rather than clicking through a web interface, the browser session is driven programmatically, so batch operations are scriptable.
- **A batch upload manifest.** Every file that should go up is enumerated, so a skipped file is detectable rather than discovered later by a user.
- **Cache fingerprint synchronisation.** Asset references are versioned so a changed file is actually re-fetched instead of served from cache.
- **Live md5 verification.** Files are hashed on the server and compared against local hashes, which turns "it should be live" into a checkable claim.
- **A defined rollback path** for when verification fails.

## Requirements

Windows · Python 3 · access to the site's hosting panel

## Installation

```bash
git clone https://github.com/<your-username>/takelemon-site-deploy.git
```

Then place the folder into your agent skills directory:

| OS | Path |
|---|---|
| Windows | `C:\Users\<you>\.workbuddy\skills\takelemon-site-deploy\` |
| macOS / Linux | `~/.workbuddy/skills/takelemon-site-deploy/` |

There is no build step. Restart the session and it takes effect.

## How to use

Ask for the change to be pushed:

- "Update these images on the live site"
- "Push the page changes and confirm they took"
- "Check whether the live site matches the local version"

The skill uploads, synchronises fingerprints, then verifies hashes and reports what actually matches.

## Files

```
├── SKILL.md
└── scripts/
    ├── crop_to_target.py
    └── match_refine.py
```

## Notes and limits

1. **"It looks right" is not verification.** Screenshots from a cached browser prove nothing. The hash comparison is the step that counts.
2. **Fingerprints must change when files change.** A changed file with an unchanged fingerprint is served from cache, and the site looks like the change never happened.
3. **Panel sessions expire.** Long-running batch operations may need the session refreshed partway through.
4. **Keep a copy before publishing.** The rollback path assumes something to roll back to.

## License

MIT
