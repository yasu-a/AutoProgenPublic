from dataclasses import dataclass


@dataclass(frozen=True)
class AboutInfo:
    """About画面に表示する情報"""
    app_name: str
    version_text: str  # 例: "1.1-beta.2" または "1.1.2"
    repo_url: str
    icon_credit_url: str
