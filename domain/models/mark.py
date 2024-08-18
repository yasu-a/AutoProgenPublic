from dataclasses import dataclass


@dataclass
class Mark:
    score: int | None  # Noneは未採点を表す

    def to_json(self):
        return dict(
            score=self.score,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            score=body["score"],
        )

    @classmethod
    def create_default(cls):
        return Mark(
            score=None,  # 初期状態は未採点
        )

    @property
    def is_marked(self) -> bool:
        return self.score is not None

    def set_unmarked(self) -> None:
        self.score = None

    def set_score(self, score: int) -> None:
        self.score = score
