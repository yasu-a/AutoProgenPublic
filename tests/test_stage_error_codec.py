from autoprogen.domain.error.stage.test import OutputMatchingError
from autoprogen.domain.service.stage_error_codec import StageErrorCodec, StageErrorRecord


def test_stage_error_codec_roundtrip() -> None:
    """具象エラーをレコードに変換し、元の型と値に復元できることを確認する。"""
    codec = StageErrorCodec()
    error = OutputMatchingError(detail="テスト用エラー")

    record = codec.encode(error)

    assert record == StageErrorRecord(
        error_group_id="test",
        error_type_id="output_matching_error",
        params={"detail": "テスト用エラー"},
    )

    restored = codec.decode(record)

    assert isinstance(restored, OutputMatchingError)
    assert restored.detail == error.detail
