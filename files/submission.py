import os


class SubmissionIO:
    def __init__(self, *, project_path):
        self.__project_path = project_path

    def student_submission_folder_fullpath(self, submission_folder_name):
        return os.path.join(self.__project_path, submission_folder_name)
