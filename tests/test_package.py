def test_package_version_pep396():
    from testcontainers_on_whales import __version__

    assert isinstance(__version__, str), "__version__ is not a string"
