import os
from pathlib import Path

from shared.domain.interface.gateway import IFolderShowInExplorerGateway


class FolderShowInExplorerGateway(IFolderShowInExplorerGateway):
    """フォルダをエクスプローラで開くGateway実装"""
    
    def __init__(self):
        pass
    
    def execute(self, folder_path: Path) -> None:
        """フォルダをエクスプローラで開く"""
        if folder_path.exists():
            os.startfile(folder_path)

