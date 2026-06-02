import pytest

from domain.model.value import StudentID


@pytest.mark.parametrize(
    "value",
    [
        "21D5109047B",
        "26HG209871C",
        "26HJ403216F",
    ],
)
def test_student_id_accepts_documented_formats(value: str) -> None:
    assert str(StudentID(value)) == value


@pytest.mark.parametrize(
    "value",
    [
        "26HJA03216F",
        "26HGA09871C",
        "21D5G09047B",
    ],
)
def test_student_id_rejects_undocumented_mixed_formats(value: str) -> None:
    with pytest.raises(ValueError):
        StudentID(value)
