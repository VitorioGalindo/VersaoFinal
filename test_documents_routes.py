import pytest
from datetime import datetime
from backend import db
from backend.models import Company, CvmDocument


def _seed_company_with_docs(app, dates):
    """Helper to create a company and attach documents for each date."""
    with app.app_context():
        company = Company(company_name="Date Co", ticker="DCO")
        db.session.add(company)
        db.session.commit()

        docs = [
            CvmDocument(company_id=company.id, document_type="DFP", delivery_date=d)
            for d in dates
        ]
        db.session.add_all(docs)
        db.session.commit()

        return company.id


def test_get_documents_by_company_start_date_only(client):
    """Documents on or after the start date should be returned."""
    company_id = _seed_company_with_docs(
        client.application,
        [datetime(2024, 1, 1), datetime(2024, 6, 1), datetime(2024, 12, 31)],
    )

    resp = client.get(
        f"/api/documents/by_company/{company_id}?start_date=2024-06-01"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["documents"]) == 2
    assert all(
        datetime.fromisoformat(d["delivery_date"]) >= datetime(2024, 6, 1)
        for d in data["documents"]
    )


def test_get_documents_by_company_end_date_only(client):
    """Documents on or before the end date should be returned."""
    company_id = _seed_company_with_docs(
        client.application,
        [datetime(2024, 1, 1), datetime(2024, 6, 1), datetime(2024, 12, 31)],
    )

    resp = client.get(
        f"/api/documents/by_company/{company_id}?end_date=2024-06-01"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["documents"]) == 2
    assert all(
        datetime.fromisoformat(d["delivery_date"]) <= datetime(2024, 6, 1)
        for d in data["documents"]
    )


def test_get_documents_by_company_between_dates(client):
    """Only documents between both dates should be returned."""
    company_id = _seed_company_with_docs(
        client.application,
        [datetime(2024, 1, 1), datetime(2024, 6, 1), datetime(2024, 12, 31)],
    )

    resp = client.get(
        f"/api/documents/by_company/{company_id}?start_date=2024-02-01&end_date=2024-11-01"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["documents"]) == 1
    assert datetime.fromisoformat(data["documents"][0]["delivery_date"]) == datetime(
        2024, 6, 1
    )


def test_list_cvm_documents_includes_category_and_download_url(client):
    with client.application.app_context():
        company = Company(company_name="ACME", ticker="ACM")
        db.session.add(company)
        db.session.commit()

        doc = CvmDocument(
            company_id=company.id,
            document_type="DFP",
            category="Financeiro",
            title="DFP 2024",
            delivery_date=datetime(2024, 1, 1),
            download_url="http://example.com/dfp",
        )
        db.session.add(doc)
        db.session.commit()

    resp = client.get("/api/cvm/documents")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["documents"]) == 1
    returned = data["documents"][0]
    assert returned["category"] == "Financeiro"
    assert returned["download_url"] == "http://example.com/dfp"

