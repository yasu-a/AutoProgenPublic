import copy

from shared.domain.entity.testcase import TestCaseConfigEntity
from shared.domain.error import ServiceError
from shared.domain.value.identifier import TestCaseID
from shared.infra.repository.testcase import TestCaseRepository


class TestCaseConfigCopyService:
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_id: TestCaseID, new_testcase_id: TestCaseID) -> None:
        if self._testcase_config_repo.exists(new_testcase_id):
            raise ServiceError(f"testcase_id {new_testcase_id} already exists")
        entity: TestCaseConfigEntity = self._testcase_config_repo.get(testcase_id)
        entity_copy = TestCaseConfigEntity(
            testcase_id=new_testcase_id,
            execute_config=copy.deepcopy(entity.execute_config),
            test_config=copy.deepcopy(entity.test_config),
        )
        self._testcase_config_repo.put(entity_copy)
