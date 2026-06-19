# utils/file_utils.py

ALLOWED_EXTENSIONS = (
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".cpp",
    ".c",
    ".cs",
    ".rs",
    ".md",
    ".json",
    ".yaml",
    ".yml"
)


def is_supported_file(path: str) -> bool:

    return path.lower().endswith(
        ALLOWED_EXTENSIONS
    )


def is_large_file(size: int) -> bool:
    """
    Skip files larger than 100 KB.
    """

    return size > 100 * 1024