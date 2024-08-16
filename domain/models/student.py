#
#
# class StudentProcessStage(Enum):
#     ENVIRONMENT_BUILDING = 1
#     COMPILE = 2
#     AUTO_TESTING = 3
#
#     @classmethod
#     def first(cls):
#         return cls.ENVIRONMENT_BUILDING
#
#
# class StudentProcessResult(Enum):
#     UNFINISHED = 1
#     OK = 2
#     ERROR = 3
#
#
# @dataclass(slots=True)
# class Student:
#     meta: StudentMeta
#     mark_scores: dict[int, int]  # target-id -> score
#     env_meta: StudentEnvMeta | None
#     compile_result: EnvironmentCompileResult | None
#     test_result: StudentTestResult | None = None
#
#     def to_json(self):
#         return dict(
#             meta=self.meta.to_json(),
#             mark_scores=self.mark_scores,
#             env_meta=None if self.env_meta is None else self.env_meta.to_json(),
#             compile_result=None if self.compile_result is None else self.compile_result.to_json(),
#             test_result=None if self.test_result is None else self.test_result.to_json(),
#         )
#
#     @classmethod
#     def from_json(cls, body):
#         return cls(
#             meta=StudentMeta.from_json(body["meta"]),
#             mark_scores={
#                 int(k): v
#                 for k, v in body.get("mark_scores", {}).items()
#             },
#             env_meta=(
#                 None
#                 if body["env_meta"] is None
#                 else StudentEnvMeta.from_json(body["env_meta"])
#             ),
#             compile_result=(
#                 None
#                 if body["compile_result"] is None
#                 else EnvironmentCompileResult.from_json(body["compile_result"])
#             ),
#             test_result=(
#                 None
#                 if body["test_result"] is None
#                 else StudentTestResult.from_json(body["test_result"])
#             ),  # TODO: impl
#         )
#
#     @classmethod
#     def from_meta(cls, meta: StudentMeta):
#         return cls(
#             meta=meta,
#             env_meta=None,
#             compile_result=None,
#             test_result=None,
#             mark_scores={},
#         )
#
#     @property
#     def process_stage_flags(self) -> OrderedDict[StudentProcessStage, StudentProcessResult]:
#         flags = OrderedDict()
#
#         if self.env_meta is None:
#             result = StudentProcessResult.UNFINISHED
#         elif self.env_meta.success:
#             result = StudentProcessResult.OK
#         else:
#             result = StudentProcessResult.ERROR
#         flags[StudentProcessStage.ENVIRONMENT_BUILDING] = result
#
#         if self.compile_result is None:
#             result = StudentProcessResult.UNFINISHED
#         elif self.compile_result.success:
#             result = StudentProcessResult.OK
#         else:
#             result = StudentProcessResult.ERROR
#         flags[StudentProcessStage.COMPILE] = result
#
#         if self.test_result is None:
#             result = StudentProcessResult.UNFINISHED
#         elif self.test_result.success:
#             result = StudentProcessResult.OK
#         else:
#             result = StudentProcessResult.ERROR
#         flags[StudentProcessStage.AUTO_TESTING] = result
#
#         return flags
#
#     @property
#     def current_finished_state(
#             self,
#     ) -> tuple[StudentProcessStage, StudentProcessResult] | tuple[None, None]:
#         flags = self.process_stage_flags
#
#         last_finished_item = None, None  # (None, None): nothing started
#         for item in flags.items():
#             stage, result = item
#             if result != StudentProcessResult.UNFINISHED:  # finished
#                 last_finished_item = item
#             else:  # unfinished
#                 return last_finished_item
#         return last_finished_item
#
#     @property
#     def required_next_stage(self) \
#             -> StudentProcessStage | None:  # None: all stages completed
#         stage, result = self.current_finished_state
#         if stage is None:  # nothing has been started
#             return StudentProcessStage.first()
#         elif result == StudentProcessResult.OK:
#             try:
#                 return StudentProcessStage(stage.value + 1)
#             except ValueError:  # stage is the last stage
#                 return None
#         else:  # result is an error
#             return stage
#
#     @property
#     def last_stage_main_error_reason(self) \
#             -> str | None:  # None: no error or no progress
#         stage, result = self.current_finished_state
#         if stage is None and result is None:  # nothing has been started
#             return None
#         elif result == StudentProcessResult.OK:
#             return None
#         else:  # result is an error
#             if stage == StudentProcessStage.ENVIRONMENT_BUILDING:
#                 for import_result in self.env_meta.import_results.values():
#                     if import_result.success:
#                         continue
#                     reference_path = import_result.source_item_path
#                     reference_text = "" if reference_path is None else f": \"{reference_path}\""
#                     message_text = import_result.reason
#                     return f"{message_text}{reference_text}"
#             elif stage == StudentProcessStage.COMPILE:
#                 return self.compile_result.reason
#             elif stage == StudentProcessStage.AUTO_TESTING:
#                 return self.test_result.main_reason
#             else:
#                 assert False, stage
