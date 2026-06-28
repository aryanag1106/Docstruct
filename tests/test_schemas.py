from docstruct.schemas import GenericFormFields, ReceiptFields, ResumeFields, json_schema_for


def test_receipt_fields_accepts_partial_data():
    r = ReceiptFields.model_validate({"merchant_name": "Test Store", "total_amount": 100.5})
    assert r.merchant_name == "Test Store"
    assert r.currency == "INR"  # default


def test_resume_fields_defaults_are_empty_not_none():
    r = ResumeFields.model_validate({"full_name": "Jane Doe"})
    assert r.skills == []
    assert r.experience == []


def test_generic_form_fields_roundtrip():
    g = GenericFormFields.model_validate({"fields": {"Invoice No": "INV-001"}})
    assert g.fields["Invoice No"] == "INV-001"


def test_json_schema_for_every_doc_type():
    for doc_type in ("receipt", "resume", "generic_form"):
        schema = json_schema_for(doc_type)  # type: ignore[arg-type]
        assert schema["type"] == "object"
        assert "properties" in schema
