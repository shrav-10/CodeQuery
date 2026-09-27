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
    os.makedirs(REPOSITORIES_DIR, exist_ok=True)

    repository_name = repository_url.rstrip("/").split("/")[-1]

    if repository_name.endswith(".git"):
        repository_name = repository_name[:-4]

    repository_path = os.path.join(
        REPOSITORIES_DIR,
        repository_name
    )

    if os.path.exists(repository_path):
        shutil.rmtree(
            repository_path,
            onerror=remove_readonly
        )

    Repo.clone_from(
        repository_url,
        repository_path
    )

    return repository_path