import unittest
from finsight.application.ai import errors as e


class TestErrorModel(unittest.TestCase):
    def test_all_ai_errors_subclass_base(self):
        for cls in (e.AiAuthorizationError, e.AiScopeError, e.GroundingUnavailableError,
                    e.MaskingError, e.PromptBuildError, e.PromptBudgetError, e.ProviderError,
                    e.ProviderUnavailableError, e.ProviderTimeoutError, e.ResponseFormatError,
                    e.CitationError, e.ConversationNotFoundError, e.MemoryProvenanceError):
            self.assertTrue(issubclass(cls, e.AiError), cls.__name__)

    def test_provider_errors_share_provider_base(self):
        self.assertTrue(issubclass(e.ProviderUnavailableError, e.ProviderError))
        self.assertTrue(issubclass(e.ProviderTimeoutError, e.ProviderError))

    def test_error_carries_message_and_detail(self):
        err = e.MaskingError("boom", detail={"k": 1})
        self.assertEqual(err.message, "boom")
        self.assertEqual(err.detail, {"k": 1})


if __name__ == "__main__":
    unittest.main()
