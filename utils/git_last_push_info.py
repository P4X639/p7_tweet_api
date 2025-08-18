#!/usr/bin/env python3
# utils/git_last_push_info.py
# Génère un JSON avec:
# 1) Infos repo (owner/repo, branche, commit_id, commit_date)
# 2) Liste + date des fichiers rapportés par `git status` (par défaut)
#
# Modes:
#   - fs (défaut) : reflète exactement `git status` (worktree complet)
#   - staging     : fichiers stagés uniquement (index)
#   - commit      : fichiers du dernier commit
#
# Usage:
#   python3 utils/git_last_push_info.py --repo . --branch main > version_info.json
#
import argparse
import os
import subprocess
import json
from datetime import datetime
from collections import OrderedDict

def run(cmd, cwd=None, check=True, text=True):
    """
    Exécute une commande et renvoie stdout (str par défaut, bytes si text=False).
    """
    res = subprocess.run(cmd, cwd=cwd, text=text, capture_output=True)
    if check and res.returncode != 0:
        raise subprocess.CalledProcessError(res.returncode, cmd, res.stdout, res.stderr)
    return res.stdout if text else res.stdout  # bytes si text=False

def fmt_ts(ts):
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def parse_github_repo(remote_url: str):
    """
    Extrait (owner, repo) d'une URL ssh/https GitHub.
    """
    # https://github.com/OWNER/REPO(.git)
    if remote_url.startswith(("https://", "http://")):
        parts = remote_url.rstrip("/").replace(".git", "").split("/")
        if len(parts) >= 2:
            return parts[-2], parts[-1]
    # git@github.com:OWNER/REPO(.git)
    if remote_url.startswith("git@"):
        after_colon = remote_url.split(":", 1)[-1]
        parts = after_colon.replace(".git", "").split("/")
        if len(parts) >= 2:
            return parts[-2], parts[-1]
    return None, None

def get_repo_info(repo_path: str, branch_fallback: str):
    """
    owner/repo GitHub + branche + commit_id + commit_date.
    """
    try:
        remote_url = run(["git", "remote", "get-url", "origin"], cwd=repo_path).strip()
    except Exception:
        remote_url = ""
    owner, repo = parse_github_repo(remote_url)

    try:
        branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path).strip()
    except Exception:
        branch = branch_fallback

    try:
        commit_id = run(["git", "rev-parse", "--short", "HEAD"], cwd=repo_path).strip()
        commit_date = run(
            ["git", "show", "-s", "--format=%cd", "--date=format:%Y-%m-%d %H:%M:%S", "HEAD"],
            cwd=repo_path
        ).strip()
    except Exception:
        commit_id, commit_date = None, None

    return OrderedDict([
        ("github_repo", OrderedDict([
            ("owner", owner),
            ("repo", repo),
        ])),
        ("branch", branch or branch_fallback),
        ("commit_id", commit_id),
        ("commit_date", commit_date),
    ])

def list_files_status(repo_path: str):
    """
    Reflète `git status` complet (worktree).
    Utilise --porcelain=v1 -z pour un parsing robuste, inclut non suivis et renommés.
    Renvoie une liste de dicts {file, date, status}.
    status = colonnes XY de porcelain (" M", "M ", "??", "A ", "R ", etc.)
    Pour les renommages, on retourne le chemin cible (nouveau nom).
    """
    out = run(
        ["git", "-c", "core.quotepath=false", "status", "--porcelain=v1", "-z",
         "--ignored=no", "--untracked-files=all"],
        cwd=repo_path, text=False
    )
    data = out.decode("utf-8", errors="replace")
    parts = [p for p in data.split("\x00") if p]

    files = []
    i = 0
    while i < len(parts):
        rec = parts[i]
        i += 1
        if len(rec) < 3:
            continue
        XY = rec[:2]
        path1 = rec[3:]          # après "XY "
        path = path1
        # Pour R/C, un deuxième chemin (nouveau nom) suit dans le flux -z
        if XY and (XY[0] in ("R", "C")) and i < len(parts):
            path2 = parts[i]
            i += 1
            path = path2

        # Exclure version_info.json
        if path == "version_info.json":
            continue
            
        f_abs = os.path.join(repo_path, path)
        date_val = fmt_ts(os.path.getmtime(f_abs)) if os.path.exists(f_abs) else None
        files.append(OrderedDict([
            ("file", path),
            ("date", date_val),
            ("status", XY),
        ]))
    return files

def list_files_staging(repo_path: str):
    """
    Fichiers stagés (index) seulement. Équivalent `git diff --cached --name-only -z`.
    """
    out = run(["git", "diff", "--cached", "--name-only", "-z"], cwd=repo_path, text=False)
    data = out.decode("utf-8", errors="replace")
    parts = [p for p in data.split("\x00") if p]
    files = []
    for path in parts:
        # Exclure version_info.json
        if path == "version_info.json":
            continue
            
        f_abs = os.path.join(repo_path, path)
        date_val = fmt_ts(os.path.getmtime(f_abs)) if os.path.exists(f_abs) else None
        files.append(OrderedDict([
            ("file", path),
            ("date", date_val),
            ("status", "INDEX"),
        ]))
    return files

def list_files_last_commit(repo_path: str):
    """
    Fichiers du dernier commit.
    """
    out = run(["git", "show", "--name-only", "--pretty=format:", "HEAD"], cwd=repo_path)
    paths = [p for p in out.splitlines() if p.strip()]
    try:
        commit_date = run(
            ["git", "show", "-s", "--format=%cd", "--date=format:%Y-%m-%d %H:%M:%S", "HEAD"],
            cwd=repo_path
        ).strip()
    except Exception:
        commit_date = None
    files = []
    for path in paths:
        # Exclure version_info.json
        if path == "version_info.json":
            continue
            
        files.append(OrderedDict([
            ("file", path),
            ("date", commit_date),
            ("status", "COMMIT"),
        ]))
    return files

def main():
    p = argparse.ArgumentParser(description="Génère des infos repo + liste des fichiers modifiés")
    p.add_argument("--repo", default=".", help="Chemin du repo")
    p.add_argument("--branch", default="main", help="Nom de la branche (fallback)")
    p.add_argument("--mode", choices=["fs", "status", "staging", "commit"], default="fs",
                   help="fs/status = état complet du worktree (git status), staging = index, commit = dernier commit")
    args = p.parse_args()

    repo_path = os.path.abspath(args.repo)
    mode = "fs" if args.mode == "status" else args.mode

    info = get_repo_info(repo_path, args.branch)
    out = OrderedDict()
    out["fetch_info"] = OrderedDict([
        ("github_repo", info["github_repo"]),
        ("branch", info["branch"]),
    ])
    out["commit_id"] = info["commit_id"]
    out["commit_date"] = info["commit_date"]

    if mode == "fs":
        files = list_files_status(repo_path)
    elif mode == "staging":
        files = list_files_staging(repo_path)
    else:  # commit
        files = list_files_last_commit(repo_path)

    out["files"] = files
    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
