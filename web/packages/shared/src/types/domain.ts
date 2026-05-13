export interface Account {
  id: string;
  nome: string;
  setor_primario: string;
  whatsapp_phone: string | null;
}

export interface Unit {
  id: string;
  nome: string;
  tipo: string;
  area_capacidade?: number | null;
}

export interface PlatformUser {
  id: string;
  nome: string;
  email: string;
  ativo: boolean;
  role: string | null;
  portal_access: boolean;
  account_id: string;
  account_nome: string;
  setor_primario: string;
  whatsapp_phone: string | null;
  criado_em: string;
}

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
