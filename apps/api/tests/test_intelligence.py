from fastapi.testclient import TestClient
import pytest

from app.intelligence.briefing_builder import enforce_cited_actions
from app.intelligence.models import CausalDiagnosis, DealBriefing, NextBestAction, RiskFlag
from app.main import app

DEAL_MEMORY_NODE_ID = "deal_northstar_expansion:deal_memory:2026-03-04T15:00:00.000Z"
CALL_NODE_ID = "call_ns_005"
PLAYBOOK_NODE_ID = "playbook_proposal_risk"
SOURCE_FACT_NODE_ID = "source_fact_crm_stage"
INTEGRATION_FACT_NODE_ID = "integration_fact_crm_amount"
TEST_TENANT_ID = "tenant_test"
AUTH_HEADERS = {"X-Tenant-Id": TEST_TENANT_ID, "Authorization": "Bearer test-token"}
QUERY_RESPONSE = {
    "results": [
        {"record_type": "tenant", "id": TEST_TENANT_ID},
        {
            "record_type": "deal",
            "tenant_id": TEST_TENANT_ID,
            "deal_id": "deal_northstar_expansion",
            "id": "deal_northstar_expansion",
        },
        {
            "record_type": "deal_memory",
            "tenant_id": TEST_TENANT_ID,
            "deal_id": "deal_northstar_expansion",
            "id": DEAL_MEMORY_NODE_ID,
            "stage": "Proposal",
            "champion_id": "contact_elena",
            "economic_buyer_id": "contact_marcus",
            "champion_confidence": 0.34,
            "budget_confirmed": False,
            "technical_validated": True,
            "active_objections": ["budget_freeze"],
            "next_step_agreed": "Send revised rollout plan to CFO",
            "last_call_id": CALL_NODE_ID,
            "valid_from": "2026-03-04T15:00:00.000Z",
            "valid_to": None,
        },
        {
            "record_type": "call_event",
            "id": CALL_NODE_ID,
            "tenant_id": TEST_TENANT_ID,
            "deal_id": "deal_northstar_expansion",
            "timestamp": "2026-03-04T15:00:00.000Z",
        },
        {
            "record_type": "playbook",
            "id": PLAYBOOK_NODE_ID,
            "tenant_id": TEST_TENANT_ID,
            "stage": "Proposal",
            "title": "Proposal risk",
            "content": "Use cited executive evidence.",
        },
        {
            "record_type": "source_fact",
            "id": SOURCE_FACT_NODE_ID,
            "tenant_id": TEST_TENANT_ID,
            "source": "crm",
            "content": "CRM stage is Proposal.",
        },
        {
            "record_type": "integration_fact",
            "id": INTEGRATION_FACT_NODE_ID,
            "tenant_id": TEST_TENANT_ID,
            "source": "crm",
            "content": "CRM amount is 120000.",
        },
    ]
}


def configure_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDI_TENANT_ID", TEST_TENANT_ID)
    monkeypatch.setenv("CDI_AUTH_TOKEN", "test-token")


class FakeHydraDbClient:
    def query_deal(self, tenant_id: str, deal_id: str) -> dict:
        assert tenant_id == TEST_TENANT_ID
        assert deal_id == "deal_northstar_expansion"
        return QUERY_RESPONSE

    @classmethod
    def from_settings(cls, settings) -> "FakeHydraDbClient":
        return cls()


class FakeOpenAIClient:
    context: dict | None = None

    def build_briefing(self, deal_id: str, context: dict) -> DealBriefing:
        self.__class__.context = context
        return DealBriefing(
            deal_id=deal_id,
            generated_at="2026-03-04T16:00:00.000Z",
            status_summary="Budget risk after CFO silence.",
            causal_diagnosis=(
                CausalDiagnosis(
                    description="CFO silence follows budget freeze.",
                    causal_chain=("budget_freeze", "cfo_silence"),
                    evidence_node_ids=(CALL_NODE_ID,),
                ),
                CausalDiagnosis(
                    description="Invented diagnosis.",
                    causal_chain=("unknown",),
                    evidence_node_ids=("unknown_memory",),
                ),
            ),
            risk_flags=(
                RiskFlag(flag="CFO silence", severity="high", evidence_node_id=DEAL_MEMORY_NODE_ID),
                RiskFlag(flag="Invented risk", severity="medium", evidence_node_id="unknown_risk_node"),
            ),
            next_best_actions=(
                NextBestAction(
                    action="Bring Marcus back into the business case.",
                    rationale="Budget freeze followed champion silence.",
                    cited_memory_node_id=DEAL_MEMORY_NODE_ID,
                    cited_knowledge_node_id=None,
                ),
                NextBestAction(
                    action="Offer a generic discount.",
                    rationale="Discounts can help.",
                    cited_memory_node_id=None,
                    cited_knowledge_node_id=None,
                ),
                NextBestAction(
                    action="Use missing memory.",
                    rationale="This memory id is not in the deal context.",
                    cited_memory_node_id="tenant_other:deal_memory:missing",
                    cited_knowledge_node_id=None,
                ),
                NextBestAction(
                    action="Confirm the CRM stage with RevOps.",
                    rationale="The CRM stage source fact is in the deal context.",
                    cited_memory_node_id=None,
                    cited_knowledge_node_id=SOURCE_FACT_NODE_ID,
                ),
                NextBestAction(
                    action="Confirm forecast amount before commit.",
                    rationale="The CRM amount integration fact is in the deal context.",
                    cited_memory_node_id=None,
                    cited_knowledge_node_id=INTEGRATION_FACT_NODE_ID,
                ),
            ),
            confidence=0.71,
        )

    @classmethod
    def from_settings(cls, settings) -> "FakeOpenAIClient":
        return cls()


def test_enforce_cited_actions_drops_uncited_actions() -> None:
    actions = (
        NextBestAction(
            action="Bring Marcus back into the business case.",
            rationale="Budget freeze followed champion silence.",
            cited_memory_node_id="deal_northstar_expansion:deal_memory:2026-03-04T15:00:00.000Z",
            cited_knowledge_node_id=None,
        ),
        NextBestAction(
            action="Offer a generic discount.",
            rationale="Discounts can help.",
            cited_memory_node_id=None,
            cited_knowledge_node_id=None,
        ),
    )

    cited = enforce_cited_actions(
        actions,
        valid_memory_node_ids=(DEAL_MEMORY_NODE_ID,),
        valid_knowledge_node_ids=(PLAYBOOK_NODE_ID,),
    )

    assert [action.action for action in cited] == ["Bring Marcus back into the business case."]


def test_enforce_cited_actions_drops_unknown_or_cross_context_citations() -> None:
    actions = (
        NextBestAction(
            action="Use cited playbook.",
            rationale="The playbook is in the deal context.",
            cited_memory_node_id=None,
            cited_knowledge_node_id=PLAYBOOK_NODE_ID,
        ),
        NextBestAction(
            action="Use missing memory.",
            rationale="This memory id is not in the deal context.",
            cited_memory_node_id="tenant_other:deal_memory:missing",
            cited_knowledge_node_id=None,
        ),
        NextBestAction(
            action="Mix valid and invalid citations.",
            rationale="A dangling citation should remove the action.",
            cited_memory_node_id=DEAL_MEMORY_NODE_ID,
            cited_knowledge_node_id="unknown_playbook",
        ),
    )

    cited = enforce_cited_actions(
        actions,
        valid_memory_node_ids=(DEAL_MEMORY_NODE_ID,),
        valid_knowledge_node_ids=(PLAYBOOK_NODE_ID,),
    )

    assert [action.action for action in cited] == ["Use cited playbook."]


def test_intelligence_route_fails_closed_without_hydradb_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_auth(monkeypatch)
    client = TestClient(app)

    response = client.get(
        "/intelligence/deal/deal_northstar_expansion",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "provider-not-ready: HYDRA_DB_API_KEY"


def test_intelligence_route_scopes_by_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    client = TestClient(app)

    mismatched_tenant = client.get(
        "/intelligence/deal/deal_northstar_expansion",
        headers=AUTH_HEADERS,
        params={"tenant_id": "tenant_other"},
    )

    assert mismatched_tenant.status_code == 403


def test_intelligence_route_fails_closed_without_openai_after_hydradb(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("app.intelligence.router.HydraDbClient", FakeHydraDbClient)
    client = TestClient(app)

    response = client.get(
        "/intelligence/deal/deal_northstar_expansion",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "provider-not-ready: OPENAI_API_KEY"


def test_intelligence_route_enforces_current_context_citations(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    FakeOpenAIClient.context = None
    monkeypatch.setattr("app.intelligence.router.HydraDbClient", FakeHydraDbClient)
    monkeypatch.setattr("app.intelligence.router.OpenAIClient", FakeOpenAIClient)
    client = TestClient(app)

    response = client.get(
        "/intelligence/deal/deal_northstar_expansion",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 200
    body = response.json()
    assert [action["action"] for action in body["next_best_actions"]] == [
        "Bring Marcus back into the business case.",
        "Confirm the CRM stage with RevOps.",
        "Confirm forecast amount before commit.",
    ]
    assert [diagnosis["description"] for diagnosis in body["causal_diagnosis"]] == ["CFO silence follows budget freeze."]
    assert [risk["flag"] for risk in body["risk_flags"]] == ["CFO silence"]
    assert FakeOpenAIClient.context is not None
    assert FakeOpenAIClient.context["deal_memory"]["id"] == DEAL_MEMORY_NODE_ID
