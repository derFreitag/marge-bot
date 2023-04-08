from marge import gitlab


class TestVersion:
    def test_parse(self):
        assert gitlab.Version.parse("16.0.0-ee") == gitlab.Version(
            release=(16, 0, 0), edition="ee"
        )

    def test_parse_no_edition(self):
        assert gitlab.Version.parse("16.0.0") == gitlab.Version(
            release=(16, 0, 0), edition=None
        )

    def test_is_ee(self):
        assert gitlab.Version.parse("16.0.0-ee").is_ee
        assert not gitlab.Version.parse("16.0.0").is_ee
