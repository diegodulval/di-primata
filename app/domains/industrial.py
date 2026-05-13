from app.domains.schema import DomainLabels, DomainSchema, EntityLabel, EventTypeOption, SelectOption

INDUSTRIAL = DomainSchema(
    domain="industrial",
    labels=DomainLabels(
        account=EntityLabel(singular="Fábrica", plural="Fábricas"),
        unit=EntityLabel(singular="Setor", plural="Setores"),
        cycle=EntityLabel(singular="Ordem de Produção", plural="Ordens de Produção"),
        event=EntityLabel(singular="Operação", plural="Operações"),
        user=EntityLabel(singular="Funcionário", plural="Funcionários"),
        product=EntityLabel(singular="Produto", plural="Produtos"),
    ),
    unit_types=[
        SelectOption(value="LINHA_PRODUCAO", label="Linha de Produção"),
        SelectOption(value="TEAR", label="Tear"),
        SelectOption(value="ATELIE", label="Ateliê"),
        SelectOption(value="OUTRO", label="Outro"),
    ],
    event_types=[
        EventTypeOption(value="operacao", label="Operação", aliases=["operação", "operacao", "operar", "produção", "producao"]),
        EventTypeOption(value="manutencao", label="Manutenção", aliases=["manutenção", "manutencao", "manutenção preventiva", "manutencao corretiva"]),
        EventTypeOption(value="controle_qualidade", label="Controle de Qualidade", aliases=["controle", "qualidade", "controle de qualidade", "inspeção", "inspecao"]),
        EventTypeOption(value="expedicao", label="Expedição", aliases=["expedição", "expedicao", "despacho", "envio"]),
        EventTypeOption(value="anomalia", label="Anomalia", aliases=["anomalia", "problema", "defeito", "falha", "erro"]),
    ],
    setor_options=[
        SelectOption(value="textil", label="Têxtil"),
        SelectOption(value="metalurgica", label="Metalúrgica"),
        SelectOption(value="alimenticia", label="Alimentícia"),
        SelectOption(value="quimica", label="Química"),
        SelectOption(value="moveleira", label="Moveleira"),
        SelectOption(value="industrial", label="Industrial Geral"),
    ],
    features=["qr_tracking"],
)
