import pytest

from addresses import canonical_address


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://Datasink.Example.com:6684/sensor-reading", "https://datasink.example.com:6684/sensor-reading"),
        ("https://datasink.example.com/sensor-reading/", "https://datasink.example.com:443/sensor-reading"),
        ("http://gateway.local", "http://gateway.local:80"),
        ("http://192.168.1.20:8080/readings", "http://192.168.1.20:8080/readings"),
        ("http://[::1]:8080", "http://[::1]:8080"),
    ],
)
def test_address_is_lowercase_with_explicit_port_and_no_trailing_slash(url, expected):
    assert canonical_address(url) == expected


def test_address_never_carries_credentials_query_or_fragment():
    url = "https://user:secret@datasink.example.com:6684/sensor-reading?sig=abc#frag"
    assert canonical_address(url) == "https://datasink.example.com:6684/sensor-reading"


@pytest.mark.parametrize("url", ["", "not a url", "ftp://host/file", "http://", "http://host:notaport"])
def test_unsupported_or_malformed_urls_have_no_address(url):
    assert canonical_address(url) is None
