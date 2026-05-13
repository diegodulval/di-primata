export interface EntityLabel {
  singular: string;
  plural: string;
}

export interface SelectOption {
  value: string;
  label: string;
}

export interface DomainLabels {
  account: EntityLabel;
  unit: EntityLabel;
  cycle: EntityLabel;
  event: EntityLabel;
  user: EntityLabel;
  product: EntityLabel;
}

export interface DomainSchema {
  domain: string;
  labels: DomainLabels;
  unit_types: SelectOption[];
  event_types: SelectOption[];
  setor_options: SelectOption[];
  features: string[];
}
