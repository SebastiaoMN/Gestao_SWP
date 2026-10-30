from io import BytesIO

from openpyxl import load_workbook

from app.models.domain import Supplier

COLUMN_ALIASES = {
    "name": {"fornecedor", "nome", "name", "supplier"},
    "tax_id": {"cnpj", "cpf", "tax_id", "documento"},
    "contact_name": {"contato", "nome_contato", "contact_name"},
    "contact_email": {"email", "e-mail", "contact_email"},
    "contact_phone": {"telefone", "phone", "celular", "contact_phone"},
    "notes": {"observacoes", "observações", "notes"},
}


def _normalize_header(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def import_suppliers_from_workbook(content: bytes) -> list[Supplier]:
    workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
    sheet = workbook.active
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return []

    header = [_normalize_header(cell) for cell in rows[0]]
    mapped_indexes: dict[str, int] = {}
    for field_name, aliases in COLUMN_ALIASES.items():
        for index, column_name in enumerate(header):
            if column_name in aliases:
                mapped_indexes[field_name] = index
                break

    suppliers: list[Supplier] = []
    for row in rows[1:]:
        data = {
            field_name: row[index]
            for field_name, index in mapped_indexes.items()
            if index < len(row) and row[index] not in (None, "")
        }
        if data.get("name"):
            suppliers.append(Supplier(**data))
    return suppliers
