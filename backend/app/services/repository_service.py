import os
import shutil
import stat
from git import Repo


REPOSITORIES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "repositories"
)


def remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clone_repository(repository_url: str) -> str:
    """
    Ingest a repository from a public GitHub URL, local folder path, or repo name.
    Uses depth=1 single_branch for ultra-fast cloning.
    """
    os.makedirs(REPOSITORIES_DIR, exist_ok=True)
    clean_target = repository_url.strip()

    # 1. Direct absolute or relative folder path
    if os.path.isdir(clean_target):
        return os.path.abspath(clean_target)

    # 2. Check if it's already an existing folder name inside data/repositories
    candidate_path = os.path.join(REPOSITORIES_DIR, clean_target)
    if os.path.isdir(candidate_path):
        return candidate_path

    # 3. GitHub or Git remote URL
    repository_name = clean_target.rstrip("/").split("/")[-1]
    if repository_name.endswith(".git"):
        repository_name = repository_name[:-4]

    repository_path = os.path.join(
        REPOSITORIES_DIR,
        repository_name
    )

    if os.path.exists(repository_path):
        try:
            repo = Repo(repository_path)
            if not repo.bare:
                return repository_path
        except Exception:
            shutil.rmtree(
                repository_path,
                onerror=remove_readonly
            )

    Repo.clone_from(
        clean_target,
        repository_path,
        depth=1,
        single_branch=True
    )

    return repository_path