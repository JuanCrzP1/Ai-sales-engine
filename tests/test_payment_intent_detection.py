from app.services.ai_service import AIService
from app.application.runtime import load_tenant_runtime_yaml


def test_payment_report_detection():
    service = AIService()
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod", channel="whatsapp")

    response, _ai_used, metadata = service.generate_business_reply(
        tenant=None,
        bot_config=None,
        user_message="ya pagué",
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id="test-payment-detection",
        include_metadata=True,
    )

    assert metadata.get("payment_status") == "reported"