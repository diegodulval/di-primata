// Espelho dos enums definidos em app/models/enums.py
// Manter sincronizado com o backend — geração automática na Fase 2 via openapi-typescript

export type TipoAgente =
  | "PRODUTOR_RURAL"
  | "INDUSTRIAL"
  | "ARTESAO"
  | "CONSULTOR_TECNICO"
  | "OPERADOR"
  | "CONSUMIDOR"
  | "ADMIN_PLATAFORMA";

export type PlanoAssinatura =
  | "FREE"
  | "CORE_PLUS"
  | "PREMIUM_AGRO"
  | "INDUSTRIA_BASIC"
  | "INDUSTRIA_PRO"
  | "COOPERATIVA";

export type TipoUnidade =
  | "TALHAO"
  | "LINHA_PRODUCAO"
  | "TEAR"
  | "ATELIE"
  | "BAIA"
  | "VIVEIRO"
  | "OUTRO";

export type StatusCiclo =
  | "ABERTO"
  | "EM_PRODUCAO"
  | "ENCERRADO"
  | "VALIDANDO"
  | "LOTE_GERADO"
  | "ARQUIVADO";

export type TipoEvento =
  | "ENTRADA_INSUMO"
  | "OPERACAO"
  | "CTRL_QUALIDADE"
  | "ANOMALIA"
  | "MOVIMENTACAO"
  | "COLHEITA"
  | "EXPEDICAO";

export type StatusValidacao = "PENDENTE" | "VALIDADO" | "INVALIDO" | "ADITADO";

export type OrigemCaptura = "VOZ" | "FOTO" | "QR_SCAN" | "MANUAL" | "API";

export type StatusLote = "GERADO" | "PUBLICADO" | "SUSPENSO" | "REVOGADO";

export type EstadoAgente =
  | "OCIOSO"
  | "ESCUTANDO"
  | "PROCESSANDO"
  | "AGUARD_CONFIRM"
  | "SINCRONIZANDO"
  | "OFFLINE";

export type CategoriaKb =
  | "INSUMO"
  | "OPERACAO"
  | "CONTROLE_QUALIDADE"
  | "ANOMALIA"
  | "COLHEITA"
  | "MOVIMENTACAO";

export type RolePerfil = "PRODUTOR" | "OPERADOR" | "CONSULTOR" | "ADMIN" | "CONSUMIDOR";

export type TipoAsset = "QR_PNG" | "QR_SVG" | "CERTIFICADO_PDF";
