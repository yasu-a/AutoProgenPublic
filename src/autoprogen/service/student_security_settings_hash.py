import hashlib
import json

from autoprogen.domain.model.value import StudentID
from autoprogen.infra.repository.project_settings import ProjectSettingsRepository
from autoprogen.service.source_code_check_factory import SourceCodeCheckCatalogFactory


class StudentSecuritySettingsHashService:
    """学生ごとのソースコード安全性チェック設定をSHA-256で識別する。"""

    def __init__(
            self,
            *,
            project_settings_repository: ProjectSettingsRepository,
            source_code_check_catalog_factory: SourceCodeCheckCatalogFactory,
    ) -> None:
        """プロジェクト設定と固定チェックカタログの生成元を受け取る。"""
        self._project_settings_repository = project_settings_repository
        self._source_code_check_catalog_factory = source_code_check_catalog_factory

    def execute(self, student_id: StudentID) -> str:
        """対象学生へ適用されるセキュリティ設定のSHA-256を返す。"""
        project_settings = self._project_settings_repository.get()

        # プロジェクトで抑制された規則を除き、実際に検査するカタログを構成する。
        catalog = self._source_code_check_catalog_factory.create().filter(
            exclude=(
                (identifier.group_id, identifier.check_id)
                for identifier in project_settings.suppressed_source_code_checks
            ),
        )

        # 表示情報を除外し、検査動作に影響する値だけを規則ID順に正規化する。
        rules = sorted(
            (
                {
                    "group_id": group.group_id,
                    "check_id": entry.check_id,
                    "match_type": entry.match_type.value,
                    "target_strings": sorted(entry.target_strings),
                }
                for group in catalog.groups
                for entry in group.entries
            ),
            key=lambda rule: (rule["group_id"], rule["check_id"]),
        )

        # 他の学生の許可情報を除外し、対象学生の許可済みハッシュだけを正規化する。
        approved_source_sha256s = sorted(
            skip.source_sha256
            for skip in project_settings.source_code_check_skips
            if skip.student_id == student_id
        )
        normalized_json = json.dumps(
            {
                "rules": rules,
                "approved_source_sha256s": approved_source_sha256s,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(normalized_json.encode("utf-8")).hexdigest()
