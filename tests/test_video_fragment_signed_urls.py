from graphql import print_ast

from playerdatapy.custom_fields import SignedUrlFields, VideoFragmentFields


class TestVideoFragmentSignedUrls:
    """The staff-only signed-download-URL fields on VideoFragment."""

    def _render(self, *subfields):
        fragment = VideoFragmentFields("videoFragments").fields(*subfields)
        return print_ast(fragment.to_ast(0))

    def test_raw_signed_url_selection(self):
        query = self._render(
            VideoFragmentFields.raw_signed_url().fields(
                SignedUrlFields.signed_url, SignedUrlFields.expires_at
            )
        )

        assert "rawSignedUrl" in query
        assert "signedUrl" in query
        assert "expiresAt" in query

    def test_processing_intermediate_signed_url_selection(self):
        query = self._render(
            VideoFragmentFields.processing_intermediate_signed_url().fields(
                SignedUrlFields.signed_url, SignedUrlFields.expires_at
            )
        )

        assert "processingIntermediateSignedUrl" in query
        assert "signedUrl" in query
        assert "expiresAt" in query
