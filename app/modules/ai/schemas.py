from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from app.models.lead_qualification import LeadAction, LeadTier

LeadCompanySize = Literal["1-10", "11-50", "51-200", "200+"]
LeadUrgency = Literal["alta", "media", "baixa"]
LeadTiming = Literal["imediato", "30_dias", "45_dias", "mais_tarde"]
LeadPainLevel = Literal["alta", "media", "baixa"]


class AttachmentRef(BaseModel):
    filename: str
    mime_type: str
    size_bytes: int
    url: Optional[str] = None
    text_content: Optional[str] = None


class ChatMessageIn(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    attachments: list[AttachmentRef] = Field(default_factory=list)
    payload: Optional[Any] = None


class ProposalDraftIn(BaseModel):
    title: Optional[str] = None
    clientName: Optional[str] = None
    clientCompany: Optional[str] = None
    clientEmail: Optional[str] = None
    clientPhone: Optional[str] = None
    projectDescription: Optional[str] = None
    scope: Optional[str] = None
    value: Optional[str] = None
    deadline: Optional[str] = None
    notes: Optional[str] = None


class ProposalAssistantRequest(BaseModel):
    messages: list[ChatMessageIn]
    current_draft: Optional[ProposalDraftIn] = None
    current_proposal_id: Optional[str] = None
    last_saved_proposal_id: Optional[str] = None
    intent_hint: Optional[Literal["create", "validate", "edit"]] = None


class DraftPatchResult(BaseModel):
    kind: Literal["proposal_draft_patch"]
    patch: dict[str, Any]
    missing_required: list[str]


class ValidationReportResult(BaseModel):
    kind: Literal["proposal_validation_report"]
    report: dict[str, Any]
    proposal_id: str


class SaveRequestResult(BaseModel):
    kind: Literal["proposal_save_request"]
    draft_summary: ProposalDraftIn


class UpdateRequestResult(BaseModel):
    kind: Literal["proposal_update_request"]
    proposal_id: str
    patch: dict[str, Any]


class OpenExistingResult(BaseModel):
    kind: Literal["proposal_open_existing"]
    proposal_id: str


ToolResult = Annotated[
    Union[
        DraftPatchResult,
        ValidationReportResult,
        SaveRequestResult,
        UpdateRequestResult,
        OpenExistingResult,
    ],
    Field(discriminator="kind"),
]


class ProposalAssistantResponse(BaseModel):
    reply: str
    tool_result: Optional[ToolResult] = None


class CommercialDiagnosisMessageIn(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class CommercialDiagnosisAssistantRequest(BaseModel):
    messages: list[CommercialDiagnosisMessageIn]


class CommercialDiagnosisReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cenario: str
    gargalo_principal: str
    etapa_critica_funil: str
    sintomas: list[str] = Field(min_length=2)
    causa_provavel: str
    acao_recomendada: str
    plano_prioritario: list[str] = Field(min_length=2)


class CommercialDiagnosisReportResult(BaseModel):
    kind: Literal["commercial_diagnosis_report"]
    report: CommercialDiagnosisReport


class CommercialDiagnosisAssistantResponse(BaseModel):
    reply: str
    tool_result: Optional[CommercialDiagnosisReportResult] = None


class LeadQualificationAssistantRequest(BaseModel):
    messages: list[ChatMessageIn]


class LeadQualificationLeadExtract(BaseModel):
    contact_name: str
    company_name: str
    contact_role: str
    segment: str
    company_size: LeadCompanySize
    urgency: LeadUrgency
    timing: LeadTiming
    pain_level: LeadPainLevel
    notes: Optional[str] = None
    qualification_reason: str
    risk: str
    recommended_next_step: str


class LeadQualificationQueueSummary(BaseModel):
    total_leads: int
    highest_score: Optional[int] = None
    primary_action: Optional[LeadAction] = None


class LeadQualificationLeadResult(BaseModel):
    lead_id: str
    company_name: str
    contact_name: str
    contact_role: str
    segment: str
    company_size: LeadCompanySize
    urgency: LeadUrgency
    timing: LeadTiming
    pain_level: LeadPainLevel
    notes: Optional[str] = None
    score: int
    tier: LeadTier
    recommended_action: LeadAction
    qualification_reason: str
    risk: str
    recommended_next_step: str


class LeadQualificationQueueResult(BaseModel):
    kind: Literal["lead_qualification_queue"]
    summary: LeadQualificationQueueSummary
    leads: list[LeadQualificationLeadResult]


class LeadQualificationAssistantResponse(BaseModel):
    reply: str
    tool_result: Optional[LeadQualificationQueueResult] = None
