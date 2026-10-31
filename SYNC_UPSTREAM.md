# Synchronizing with Upstream (`storytold/pdfcraft`)

This guide explains how to pull the latest updates, fixes, and features from the upstream repository ([`storytold/pdfcraft`](https://github.com/storytold/pdfcraft)) into your fork ([`richfrem/pdfcraft`](https://github.com/richfrem/pdfcraft)) while **strictly preserving** your enterprise SDK, REST microservice, and multi-language extensions.

---

## 🎯 Architecture & Invariants

Your fork adds a programmatic developer layer on top of the upstream desktop PDF workbench:
- **Rust SDK (`L7`):** [`crates/sdk`](crates/sdk/) (`pdfcraft-sdk`)
- **REST Service (`L7`):** [`crates/rest`](crates/rest/) (`pdfcraft-rest`)
- **Multi-Language SDKs:** [`sdks/python`](sdks/python/), [`sdks/typescript`](sdks/typescript/), [`sdks/openapi.json`](sdks/openapi.json)
- **Documentation:** [`docs/sdk/`](docs/sdk/), [`docs/sdk.md`](docs/sdk.md), [`docs/sdk-api-reference.md`](docs/sdk-api-reference.md)
- **Wiring:** Workspace registration in [`Cargo.toml`](Cargo.toml) and layer permissions in [`xtask/src/layers.rs`](xtask/src/layers.rs).

### ⛔ Golden Rules
1. **NEVER run `git reset --hard upstream/main`**: This will destroy your local commits and delete your fork extensions.
2. **NEVER run `git rebase upstream/main`**: Rebasing rewrites history and causes repeated, painful conflict resolution across existing merge commits.
3. **ALWAYS use standard 3-way merge (`git merge upstream/main`)**: Git cleanly merges non-conflicting files and preserves your fork's commit graph.
4. **NEVER accept upstream deletions** of `crates/sdk/`, `crates/rest/`, `sdks/`, or `docs/sdk/`.

---

## 🔄 Step-by-Step Upstream Sync Protocol

### Step 1: Verify Remote Configuration
Ensure both `origin` (your fork) and `upstream` (storytold) are configured:
```bash
git remote -v
```
You should see:
```text
origin    https://github.com/richfrem/pdfcraft.git (fetch)
origin    https://github.com/richfrem/pdfcraft.git (push)
upstream  https://github.com/storytold/pdfcraft.git (fetch)
upstream  https://github.com/storytold/pdfcraft.git (push)
```
*(If `upstream` is missing, add it with: `git remote add upstream https://github.com/storytold/pdfcraft.git`)*

---

### Step 2: Ensure Clean Working Tree
Before pulling changes, ensure all current work is committed or stashed:
```bash
git checkout main
git status
```
The tree should be clean (`nothing to commit, working tree clean`).

---

### Step 3: Fetch Upstream
Fetch all new branches, tags, and commits from upstream without touching your working directory:
```bash
git fetch upstream
```

---

### Step 4: Merge Upstream into Your Main Branch
Execute the merge:
```bash
git merge upstream/main
```

Git will automatically merge hundreds of files that upstream updated (engine, viewer, assets, etc.).

---

### Step 5: Resolve Expected Conflicts (If Any)

Because your fork's custom code lives in dedicated directories (`crates/sdk`, `crates/rest`, `sdks`), git will automatically merge them without conflicts.

Only two files may ever show minor conflicts:

#### 1. `Cargo.toml`
When upstream releases a new version (e.g., bumping `version = "0.16.1"`), resolve the conflict by keeping both:
- Accept upstream's new `[workspace.package].version` (e.g. `0.16.1`).
- Ensure `"sdks/python"` remains in `[workspace].members`:
  ```toml
  members = ["crates/*", "apps/*", "xtask", "sdks/python"]
  ```
- Keep `pdfcraft-sdk` and `pdfcraft-rest` under `[workspace.dependencies]`, bumping their version to match the workspace:
  ```toml
  pdfcraft-sdk = { path = "crates/sdk", version = "0.16.1" }
  pdfcraft-rest = { path = "crates/rest", version = "0.16.1" }
  ```

#### 2. `.gitignore`
Retain both upstream's additions (e.g. `.claude/`) and your local agent configurations (`/.agents/`, `/.claude/`, `/.gemini/`).

#### 3. `xtask/src/layers.rs`
If upstream modified layer definitions, verify that your fork's entries remain in `TABLE` and `SIDEWAYS`:
```rust
// in TABLE:
("sdk", Class::Layer(7)),
("rest", Class::Layer(7)),
("pyo3", Class::Exempt),

// in SIDEWAYS:
("sdk", "automation"),
("rest", "sdk"),
("rest", "automation"),
```

---

### Step 6: Run Quality & Verification Gates

Before committing or pushing the merge, verify that all systems are healthy:

```bash
# 1. Architectural layering test (ensures L7 rules are satisfied)
cargo run -p xtask -- layers

# 2. Run all unit and integration tests across SDK & REST crates
cargo test -p pdfcraft-sdk -p pdfcraft-rest

# 3. Verify cross-language OpenAPI / SDK contract integrity
python3 sdks/check_contract_drift.py

# 4. Check clippy gates on the protected crates
cargo clippy -p pdfcraft-sdk -p pdfcraft-rest --all-targets -- -D warnings
```

---

### Step 7: Finalize and Push to Your Fork

Once the verification commands pass, finalize the merge commit and push to `origin`:

```bash
# Stage resolved files if you had conflicts
git add Cargo.toml .gitignore

# Commit merge
git commit -m "chore(sync): merge upstream/main into main preserving SDK and REST extensions"

# Push to your fork
git push origin main
```

---

## 🆘 Emergency: Aborting a Merge

If a merge encounters unexpected problems and you want to cleanly revert to where you started before resolving:
```bash
git merge --abort
```
This safely restores your local working tree to the state before `git merge` was called.
