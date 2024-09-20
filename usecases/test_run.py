from services.compile_test import TestRunService


class TestRunUseCase:
    def __init__(self, test_session_service: TestRunService):
        self._test_session_service = test_session_service

    def compile_and_get_output(self) -> bool:
        # テストセッションを作成
        test_run_id = self._test_session_repo.create_session()

        # ビルド
        self._test_session_repo.build(test_run_id)

        try:
            output = self._compile_and_get_output(
                test_run_id=test_run_id,
                compiler_tool_fullpath=compiler_tool_fullpath,
            )
        except CompileTestServiceError:
            raise
        finally:
            # テストセッションを閉じる
            self._test_session_repo.delete(test_run_id)

        return output
