from domain.model.app_version import AppVersion, ReleaseType


def test_app_version_ordering():
    versions = [
        AppVersion(0, 9, ReleaseType.ALPHA, 0),
        AppVersion(1, 9, ReleaseType.ALPHA, 0),
        AppVersion(1, 9, ReleaseType.BETA, 0),
        AppVersion(1, 9, ReleaseType.STABLE, 0),
        AppVersion(2, 0, ReleaseType.STABLE, 0),
        AppVersion(2, 1, ReleaseType.STABLE, 0),
        AppVersion(2, 1, ReleaseType.STABLE, 1),
    ]

    for i, v_i in enumerate(versions):
        for j, v_j in enumerate(versions):
            print(i, str(v_i), j, str(v_j))
            if i == j:
                assert v_i == v_j
            elif i < j:
                assert v_i < v_j
            else:
                assert v_i > v_j
