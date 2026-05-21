from core.domains.schema import DomainLabels, DomainSchema, EntityLabel, EventTypeOption, SelectOption

RURAL = DomainSchema(
    domain="rural",
    labels=DomainLabels(
        account=EntityLabel(singular="Propriedade", plural="Propriedades"),
        unit=EntityLabel(singular="Talhão", plural="Talhões"),
        cycle=EntityLabel(singular="Safra", plural="Safras"),
        event=EntityLabel(singular="Atividade", plural="Atividades"),
        user=EntityLabel(singular="Produtor", plural="Produtores"),
        product=EntityLabel(singular="Cultura", plural="Culturas"),
    ),
    unit_types=[
        SelectOption(value="TALHAO", label="Talhão"),
        SelectOption(value="VIVEIRO", label="Viveiro"),
        SelectOption(value="BAIA", label="Baia"),
    ],
    event_types=[
        EventTypeOption(value="adubacao", label="Adubação", aliases=["adubação", "adubacao", "adubar", "fertilização", "fertilizacao"]),
        EventTypeOption(value="irrigacao", label="Irrigação", aliases=["irrigação", "irrigacao", "irrigar"]),
        EventTypeOption(value="colheita", label="Colheita", aliases=["colheita", "colher"]),
        EventTypeOption(value="poda", label="Poda", aliases=["poda"]),
        EventTypeOption(value="pulverizacao", label="Pulverização", aliases=["pulverização", "pulverizacao", "pulverizar"]),
    ],
    setor_options=[
        SelectOption(value="cafe", label="Café"),
        SelectOption(value="soja", label="Soja"),
        SelectOption(value="cana", label="Cana de Açúcar"),
        SelectOption(value="pecuaria", label="Pecuária"),
        SelectOption(value="hortifruti", label="Hortifrúti"),
        SelectOption(value="agro", label="Agronegócio Geral"),
    ],
    features=["whatsapp", "qr_tracking"],
)
