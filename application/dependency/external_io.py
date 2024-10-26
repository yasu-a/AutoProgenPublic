from pathlib import Path

from files.external.compile_tool import CompileToolIO
from files.external.executable import ExecutableIO
from files.external.report_archive import ManabaReportArchiveIO


def get_manaba_report_archive_io(manaba_report_archive_fullpath: Path):
    return ManabaReportArchiveIO(
        manaba_report_archive_fullpath=manaba_report_archive_fullpath,
    )


def get_compile_tool_io():
    return CompileToolIO()


def get_executable_io():
    return ExecutableIO()
