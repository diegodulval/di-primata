export interface paths {
    "/auth/register": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Register */
        post: operations["register_auth_register_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Login */
        post: operations["login_auth_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/accounts/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Me */
        get: operations["get_me_accounts_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Me */
        patch: operations["update_me_accounts_me_patch"];
        trace?: never;
    };
    "/accounts/users": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Users */
        get: operations["list_users_accounts_users_get"];
        put?: never;
        /** Create User */
        post: operations["create_user_accounts_users_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/units": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Units */
        get: operations["list_units_units_get"];
        put?: never;
        /** Create Unit */
        post: operations["create_unit_units_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/units/{unit_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Unit */
        get: operations["get_unit_units__unit_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/units/protocols": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Protocols */
        get: operations["list_protocols_units_protocols_get"];
        put?: never;
        /** Create Protocol */
        post: operations["create_protocol_units_protocols_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/cycles": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Cycles */
        get: operations["list_cycles_cycles_get"];
        put?: never;
        /** Create Cycle */
        post: operations["create_cycle_cycles_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/cycles/{cycle_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Cycle */
        get: operations["get_cycle_cycles__cycle_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/cycles/{cycle_id}/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Transition Cycle */
        patch: operations["transition_cycle_cycles__cycle_id__status_patch"];
        trace?: never;
    };
    "/cycles/{cycle_id}/missing-steps": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Missing Steps */
        get: operations["missing_steps_cycles__cycle_id__missing_steps_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/cycles/{cycle_id}/events": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Events */
        get: operations["list_events_cycles__cycle_id__events_get"];
        put?: never;
        /** Add Event */
        post: operations["add_event_cycles__cycle_id__events_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/cycles/{cycle_id}/lots": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Generate Lot */
        post: operations["generate_lot_cycles__cycle_id__lots_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/cycles/lots/{lot_id}/publish": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Publish Lot */
        post: operations["publish_lot_cycles_lots__lot_id__publish_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/cycles/lots": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Lots */
        get: operations["list_lots_cycles_lots_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/p/{qr_hash}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Public View */
        get: operations["public_view_p__qr_hash__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/whatsapp/webhook": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Webhook
         * @description Configurar em: Sandbox Settings → "When a message comes in"
         *     URL: POST /whatsapp/webhook
         */
        post: operations["webhook_whatsapp_webhook_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/whatsapp/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Status Callback
         * @description Configurar em: Sandbox Settings → "Status callback URL"
         *     URL: POST /whatsapp/status
         *     Recebe atualizações de entrega: queued → sent → delivered → read
         */
        post: operations["status_callback_whatsapp_status_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/whatsapp/sessions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Sessions
         * @description Lista todas as sessões WhatsApp com contagem de mensagens.
         */
        get: operations["list_sessions_whatsapp_sessions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/whatsapp/sessions/{session_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Session
         * @description Retorna uma sessão pelo ID.
         */
        get: operations["get_session_whatsapp_sessions__session_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /**
         * Update Session
         * @description Atualiza campos editáveis da sessão (ex: vincular talhão).
         */
        patch: operations["update_session_whatsapp_sessions__session_id__patch"];
        trace?: never;
    };
    "/whatsapp/sessions/{session_id}/messages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Session Messages
         * @description Lista todas as mensagens de uma sessão em ordem cronológica.
         */
        get: operations["list_session_messages_whatsapp_sessions__session_id__messages_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health */
        get: operations["health_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/hello": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Hello */
        get: operations["hello_hello_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** Account */
        Account: {
            /**
             * Id
             * Format: uuid
             */
            id?: string;
            /** Nome */
            nome: string;
            /** Documento */
            documento: string;
            /** Email */
            email: string;
            /** @default FREE */
            plano: components["schemas"]["PlanoAssinatura"];
            /** Setor Primario */
            setor_primario: string;
            /** Whatsapp Phone */
            whatsapp_phone?: string | null;
            /**
             * Ativo
             * @default true
             */
            ativo: boolean;
            /**
             * Criado Em
             * Format: date-time
             */
            criado_em?: string;
            /** Meta Json */
            meta_json?: {
                [key: string]: unknown;
            };
        };
        /** AccountCreate */
        AccountCreate: {
            /** Nome */
            nome: string;
            /** Documento */
            documento: string;
            /** Email */
            email: string;
            /** @default FREE */
            plano: components["schemas"]["PlanoAssinatura"];
            /** Setor Primario */
            setor_primario: string;
            /** Whatsapp Phone */
            whatsapp_phone?: string | null;
            /** Meta Json */
            meta_json?: {
                [key: string]: unknown;
            };
        };
        /** AccountUpdate */
        AccountUpdate: {
            /** Nome */
            nome?: string | null;
            /** Whatsapp Phone */
            whatsapp_phone?: string | null;
        };
        /** Certification */
        Certification: {
            /**
             * Id
             * Format: uuid
             */
            id?: string;
            /**
             * Lot Id
             * Format: uuid
             */
            lot_id: string;
            /**
             * Cert User Id
             * Format: uuid
             */
            cert_user_id: string;
            /** Notas */
            notas?: string | null;
            /**
             * Assinado Em
             * Format: date-time
             */
            assinado_em?: string;
            /** Assinatura Digital */
            assinatura_digital?: string | null;
        };
        /** Cycle */
        Cycle: {
            /**
             * Id
             * Format: uuid
             */
            id?: string;
            /**
             * Account Id
             * Format: uuid
             */
            account_id: string;
            /**
             * Unit Id
             * Format: uuid
             */
            unit_id: string;
            /** Protocol Id */
            protocol_id?: string | null;
            /** Codigo */
            codigo: string;
            /** Produto */
            produto: string;
            /** @default ABERTO */
            status: components["schemas"]["StatusCiclo"];
            /**
             * Iniciado Em
             * Format: date-time
             */
            iniciado_em?: string;
            /** Encerrado Em */
            encerrado_em?: string | null;
            /** Insumos Json */
            insumos_json?: {
                [key: string]: unknown;
            }[];
            /** Meta Json */
            meta_json?: {
                [key: string]: unknown;
            };
        };
        /** CycleCreate */
        CycleCreate: {
            /**
             * Unit Id
             * Format: uuid
             */
            unit_id: string;
            /**
             * Protocol Id
             * Format: uuid
             */
            protocol_id: string;
            /** Produto */
            produto: string;
            /** Insumos Json */
            insumos_json?: {
                [key: string]: unknown;
            }[];
            /** Meta Json */
            meta_json?: {
                [key: string]: unknown;
            };
        };
        /** Event */
        Event: {
            /**
             * Id
             * Format: uuid
             */
            id?: string;
            /**
             * Ciclo Id
             * Format: uuid
             */
            ciclo_id: string;
            /** Etapa Protocolo Id */
            etapa_protocolo_id?: string | null;
            /** Autor User Id */
            autor_user_id?: string | null;
            tipo_evento: components["schemas"]["TipoEvento"];
            /** Descricao */
            descricao: string;
            /** Payload Json */
            payload_json?: {
                [key: string]: unknown;
            };
            /** @default PENDENTE */
            status_validacao: components["schemas"]["StatusValidacao"];
            origem: components["schemas"]["OrigemCaptura"];
            /**
             * Capturado Em
             * Format: date-time
             */
            capturado_em?: string;
            /** Sincronizado Em */
            sincronizado_em?: string | null;
            /** Aditamento De Id */
            aditamento_de_id?: string | null;
            /**
             * Visivel Publico
             * @default true
             */
            visivel_publico: boolean;
            /** Attachments */
            attachments?: components["schemas"]["EventAttachment"][];
            location?: components["schemas"]["EventLocation"] | null;
        };
        /** EventAttachment */
        EventAttachment: {
            /**
             * Id
             * Format: uuid
             */
            id?: string;
            /**
             * Event Id
             * Format: uuid
             */
            event_id: string;
            /** Tipo */
            tipo: string;
            /** Url */
            url: string;
            /** Filename */
            filename?: string | null;
            /**
             * Criado Em
             * Format: date-time
             */
            criado_em?: string;
        };
        /** EventCreate */
        EventCreate: {
            /**
             * Etapa Protocolo Id
             * Format: uuid
             */
            etapa_protocolo_id: string;
            tipo_evento: components["schemas"]["TipoEvento"];
            /** Descricao */
            descricao: string;
            /** Payload Json */
            payload_json?: {
                [key: string]: unknown;
            };
            /** @default MANUAL */
            origem: components["schemas"]["OrigemCaptura"];
            /**
             * Capturado Em
             * Format: date-time
             */
            capturado_em?: string;
            /** Aditamento De Id */
            aditamento_de_id?: string | null;
            /**
             * Visivel Publico
             * @default true
             */
            visivel_publico: boolean;
        };
        /** EventLocation */
        EventLocation: {
            /**
             * Id
             * Format: uuid
             */
            id?: string;
            /**
             * Event Id
             * Format: uuid
             */
            event_id: string;
            /** Lat */
            lat: number;
            /** Lng */
            lng: number;
            /** Accuracy */
            accuracy?: number | null;
            /**
             * Capturado Em
             * Format: date-time
             */
            capturado_em?: string;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** LoginRequest */
        LoginRequest: {
            /** Email */
            email: string;
            /** Senha */
            senha: string;
        };
        /** Lot */
        Lot: {
            /**
             * Id
             * Format: uuid
             */
            id?: string;
            /**
             * Ciclo Id
             * Format: uuid
             */
            ciclo_id: string;
            /** Codigo Lote */
            codigo_lote: string;
            /** Qr Hash */
            qr_hash: string;
            /** @default GERADO */
            status: components["schemas"]["StatusLote"];
            /**
             * Gerado Em
             * Format: date-time
             */
            gerado_em?: string;
            /** Snapshot Json */
            snapshot_json?: {
                [key: string]: unknown;
            };
            /**
             * Publico
             * @default false
             */
            publico: boolean;
            /** Cert User Id */
            cert_user_id?: string | null;
            /** Assets */
            assets?: components["schemas"]["LotAsset"][];
            /** Certifications */
            certifications?: components["schemas"]["Certification"][];
        };
        /** LotAsset */
        LotAsset: {
            /**
             * Id
             * Format: uuid
             */
            id?: string;
            /**
             * Lot Id
             * Format: uuid
             */
            lot_id: string;
            tipo: components["schemas"]["TipoAsset"];
            /** Url */
            url: string;
            /**
             * Gerado Em
             * Format: date-time
             */
            gerado_em?: string;
        };
        /**
         * OrigemCaptura
         * @enum {string}
         */
        OrigemCaptura: "VOZ" | "FOTO" | "QR_SCAN" | "MANUAL" | "API";
        /**
         * PlanoAssinatura
         * @enum {string}
         */
        PlanoAssinatura: "FREE" | "CORE_PLUS" | "PREMIUM_AGRO" | "INDUSTRIA_BASIC" | "INDUSTRIA_PRO" | "COOPERATIVA";
        /** Protocol */
        Protocol: {
            /**
             * Id
             * Format: uuid
             */
            id?: string;
            /** Setor Template */
            setor_template: string;
            /** Nome */
            nome: string;
            /** Versao */
            versao: string;
            /** Etapas */
            etapas?: components["schemas"]["ProtocolStep"][];
            /** Etapas Obrig Ids */
            etapas_obrig_ids?: string[];
            /** Ref Normativa */
            ref_normativa?: string | null;
            /**
             * Ativo
             * @default true
             */
            ativo: boolean;
        };
        /** ProtocolCreate */
        ProtocolCreate: {
            /** Setor Template */
            setor_template: string;
            /** Nome */
            nome: string;
            /** Versao */
            versao: string;
            /** Etapas */
            etapas?: components["schemas"]["ProtocolStep"][];
            /** Etapas Obrig Ids */
            etapas_obrig_ids?: string[];
            /** Ref Normativa */
            ref_normativa?: string | null;
        };
        /** ProtocolStep */
        ProtocolStep: {
            /**
             * Id
             * Format: uuid
             */
            id?: string;
            /** Nome */
            nome: string;
            /** Tipo */
            tipo: string;
            /**
             * Obrigatorio
             * @default true
             */
            obrigatorio: boolean;
            /** Criterios */
            criterios?: {
                [key: string]: unknown;
            };
        };
        /** RegisterRequest */
        RegisterRequest: {
            account: components["schemas"]["AccountCreate"];
            admin: components["schemas"]["UserCreate"];
        };
        /**
         * RolePerfil
         * @enum {string}
         */
        RolePerfil: "PRODUTOR" | "OPERADOR" | "CONSULTOR" | "ADMIN" | "CONSUMIDOR";
        /**
         * StatusCiclo
         * @enum {string}
         */
        StatusCiclo: "ABERTO" | "EM_PRODUCAO" | "ENCERRADO" | "VALIDANDO" | "LOTE_GERADO" | "ARQUIVADO";
        /**
         * StatusLote
         * @enum {string}
         */
        StatusLote: "GERADO" | "PUBLICADO" | "SUSPENSO" | "REVOGADO";
        /**
         * StatusValidacao
         * @enum {string}
         */
        StatusValidacao: "PENDENTE" | "VALIDADO" | "INVALIDO" | "ADITADO";
        /**
         * TipoAgente
         * @enum {string}
         */
        TipoAgente: "PRODUTOR_RURAL" | "INDUSTRIAL" | "ARTESAO" | "CONSULTOR_TECNICO" | "OPERADOR" | "CONSUMIDOR" | "ADMIN_PLATAFORMA";
        /**
         * TipoAsset
         * @enum {string}
         */
        TipoAsset: "QR_PNG" | "QR_SVG" | "CERTIFICADO_PDF";
        /**
         * TipoEvento
         * @enum {string}
         */
        TipoEvento: "ENTRADA_INSUMO" | "OPERACAO" | "CTRL_QUALIDADE" | "ANOMALIA" | "MOVIMENTACAO" | "COLHEITA" | "EXPEDICAO";
        /**
         * TipoUnidade
         * @enum {string}
         */
        TipoUnidade: "TALHAO" | "LINHA_PRODUCAO" | "TEAR" | "ATELIE" | "BAIA" | "VIVEIRO" | "OUTRO";
        /** TokenResponse */
        TokenResponse: {
            /** Access Token */
            access_token: string;
            /**
             * Token Type
             * @default bearer
             */
            token_type: string;
        };
        /** TransitionRequest */
        TransitionRequest: {
            status: components["schemas"]["StatusCiclo"];
        };
        /** Unit */
        Unit: {
            /**
             * Id
             * Format: uuid
             */
            id?: string;
            /**
             * Account Id
             * Format: uuid
             */
            account_id: string;
            /** Nome */
            nome: string;
            tipo: components["schemas"]["TipoUnidade"];
            /** Area Capacidade */
            area_capacidade?: number | null;
            /** Lat */
            lat?: number | null;
            /** Lng */
            lng?: number | null;
            /** Setor Template */
            setor_template: string;
            /**
             * Ativo
             * @default true
             */
            ativo: boolean;
            /**
             * Criado Em
             * Format: date-time
             */
            criado_em?: string;
        };
        /** UnitCreate */
        UnitCreate: {
            /** Nome */
            nome: string;
            tipo: components["schemas"]["TipoUnidade"];
            /** Area Capacidade */
            area_capacidade?: number | null;
            /** Lat */
            lat?: number | null;
            /** Lng */
            lng?: number | null;
            /** Setor Template */
            setor_template: string;
        };
        /** User */
        User: {
            /**
             * Id
             * Format: uuid
             */
            id?: string;
            /**
             * Account Id
             * Format: uuid
             */
            account_id: string;
            /** Nome */
            nome: string;
            /** Email */
            email: string;
            tipo: components["schemas"]["TipoAgente"];
            /** Senha Hash */
            senha_hash: string;
            /**
             * Ativo
             * @default true
             */
            ativo: boolean;
            /**
             * Criado Em
             * Format: date-time
             */
            criado_em?: string;
        };
        /** UserCreate */
        UserCreate: {
            /** Nome */
            nome: string;
            /** Email */
            email: string;
            tipo: components["schemas"]["TipoAgente"];
            /** Senha */
            senha: string;
        };
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
            /** Input */
            input?: unknown;
            /** Context */
            ctx?: Record<string, never>;
        };
        /** WhatsappSessaoUpdate */
        WhatsappSessaoUpdate: {
            /** Unit Id */
            unit_id?: string | null;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    register_auth_register_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RegisterRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TokenResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    login_auth_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LoginRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TokenResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_me_accounts_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Account"];
                };
            };
        };
    };
    update_me_accounts_me_patch: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AccountUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Account"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_users_accounts_users_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["User"][];
                };
            };
        };
    };
    create_user_accounts_users_post: {
        parameters: {
            query?: {
                role?: components["schemas"]["RolePerfil"];
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UserCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["User"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_units_units_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Unit"][];
                };
            };
        };
    };
    create_unit_units_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UnitCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Unit"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_unit_units__unit_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                unit_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Unit"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_protocols_units_protocols_get: {
        parameters: {
            query?: {
                setor?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Protocol"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_protocol_units_protocols_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProtocolCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Protocol"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_cycles_cycles_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Cycle"][];
                };
            };
        };
    };
    create_cycle_cycles_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CycleCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Cycle"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_cycle_cycles__cycle_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                cycle_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Cycle"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    transition_cycle_cycles__cycle_id__status_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                cycle_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TransitionRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Cycle"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    missing_steps_cycles__cycle_id__missing_steps_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                cycle_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_events_cycles__cycle_id__events_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                cycle_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Event"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    add_event_cycles__cycle_id__events_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                cycle_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EventCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Event"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    generate_lot_cycles__cycle_id__lots_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                cycle_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Lot"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    publish_lot_cycles_lots__lot_id__publish_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                lot_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Lot"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_lots_cycles_lots_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Lot"][];
                };
            };
        };
    };
    public_view_p__qr_hash__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                qr_hash: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    webhook_whatsapp_webhook_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "text/plain": string;
                };
            };
        };
    };
    status_callback_whatsapp_status_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "text/plain": string;
                };
            };
        };
    };
    list_sessions_whatsapp_sessions_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    get_session_whatsapp_sessions__session_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_session_whatsapp_sessions__session_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["WhatsappSessaoUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_session_messages_whatsapp_sessions__session_id__messages_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    health_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    hello_hello_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
}
