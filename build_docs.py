"""
Used with the `docs` Github action to make versioned docs directories in the
gh-pages branch.
"""

import os, subprocess, re, shutil
from pathlib import Path
from distutils.version import LooseVersion
import argparse

REDIRECT_HTML = """
<!DOCTYPE html>
<meta charset="utf-8">
<title>Redirecting...</title>
<meta http-equiv="refresh" content="0; URL=./stable/">
"""

DOCS_BUILD_PATH = Path("docs/_build")


def run(args):
    print("Running:", args)
    subprocess.check_call(args)


def main():
    # clean out the contents of the build directory, but leave the directory in
    # place so that serving up files continues to work when you're developing
    # docs locally
    DOCS_BUILD_PATH.mkdir(exist_ok=True)
    for path in DOCS_BUILD_PATH.iterdir():
        shutil.rmtree(path) if path.is_dir() else path.unlink()

    if "pull_request" in os.environ.get("GITHUB_EVENT_NAME"):
        # build the current working dir's docs for a PR because doesn't have all the refs needed for multiversion
        run(["sphinx-build", "docs", "docs/_build"])
        return  # none of the steps below need to run if we're building for a PR
    else:
        # build docs for each version
        run(["sphinx-multiversion", "docs", "docs/_build"])

    # clean up static files so we don't need to host the same 10+ MB of web
    # fonts for each version of the docs
    for d in Path("docs/_build").glob("**/fonts"):
        if "main" in str(d):
            continue  # leave only the copy of the static files from the main branch
        shutil.rmtree(d)

    # move "main" (which gets its name from the `main` branch) to "latest"
    Path("docs/_build/main").rename(Path("docs/_build/latest"))

    # copy the highest released version to "stable"
    all_releases = [
        LooseVersion(d.name) for d in Path("docs/_build").iterdir() if re.match("v\d+\.", d.name)
    ]
    no_pre_releases = [v for v in all_releases if "-" not in str(v)]
    stable = None
    if no_pre_releases:
        stable = max(no_pre_releases)
    elif all_releases:
        stable = max(all_releases)
    else:
        print("WARNING: Couldn't find any released versions. Going to use 'latest' for 'stable'.")
        stable = "latest"
    print(f"Copying latest stable release {stable} to 'stable'.")
    shutil.copytree(Path("docs/_build") / str(stable), Path("docs/_build/stable"))

    # set up the redirect at /index.html
    with open("docs/_build/index.html", "w") as f:
        f.write(REDIRECT_HTML)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rsync",
        help="Where to put the fully built docs subdir for serving in development. /tmp/projectname is recommended.",
    )
    args = parser.parse_args()
    main()
    if args.rsync:
        run(["rsync", "-pthrvz", "--delete", "./docs/_build/", args.rsync])
        print(
            "NOTE: To serve these files in development, run `python3 -m http.server` inside `{}`, then go to http://127.0.0.1:8000/projectname in the browser.".format(
                Path(args.rsync).parent
            )
        )
