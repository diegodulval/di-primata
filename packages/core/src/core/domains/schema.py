from pydantic import BaseModel


class EntityLabel(BaseModel):
    singular: str
    plural: str


class SelectOption(BaseModel):
    value: str
    label: str


class EventTypeOption(BaseModel):
    value: str
    label: str
    aliases: list[str] = []


class DomainLabels(BaseModel):
    account: EntityLabel
    unit: EntityLabel
    cycle: EntityLabel
    event: EntityLabel
    user: EntityLabel
    product: EntityLabel


class DomainSchema(BaseModel):
    domain: str
    labels: DomainLabels
    unit_types: list[SelectOption]
    event_types: list[EventTypeOption]
    setor_options: list[SelectOption]
    features: list[str]
