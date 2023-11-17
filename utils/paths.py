import os


def get_root_directory(root_name: str = 'heimr-backend') -> str:
    """
    Get the root directory of the project

    :return: str
    """
    file_path = os.path.abspath(__file__)
    root = file_path.split(root_name)[0] + root_name
    return root
