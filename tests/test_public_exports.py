import playerdatapy


class TestPublicExports:
    """Hand-written modules must stay importable from the package root.

    The generated ``__init__.py`` is rewritten on every codegen run; the
    PublicApiExportsPlugin (codegen_plugins/public_api.py) re-adds these
    exports. If this test fails, the plugin was dropped from
    ``[tool.ariadne-codegen]`` or codegen ran without it (as happened in
    v1.11.1).
    """

    def test_playerdata_api_import(self):
        from playerdatapy import PlayerDataAPI
        from playerdatapy.playerdata_api import PlayerDataAPI as canonical

        assert PlayerDataAPI is canonical
        assert "PlayerDataAPI" in playerdatapy.__all__
