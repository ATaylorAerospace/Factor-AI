"""Tests for report building and export tools."""

from pathlib import Path

from factor.tools.export import build_risk_report, export_excel, export_html


def test_build_risk_report_structure(sample_analysis_results):
    """Report should have all required sections and metadata."""
    report = build_risk_report(analysis_results=sample_analysis_results)
    assert report["title"] == "Due Diligence Risk Report"
    assert report["overall_risk"] == "high"
    assert report["disclaimer"]
    assert report["synthetic_dataset_used"] is True
    assert report["generated_at"]
    assert len(report["sections"]) == 3

    section_titles = [s["title"] for s in report["sections"]]
    assert "Risk Assessment" in section_titles
    assert "Gap Analysis" in section_titles
    assert "Cross-Document Comparison" in section_titles


def test_build_risk_report_overall_risk_critical():
    """Critical provisions should produce critical overall risk."""
    results = {
        "risk_scores": [{"risk_level": "critical", "score": 9.0}],
        "gaps": [],
        "comparisons": [],
        "document_count": 1,
    }
    report = build_risk_report(analysis_results=results)
    assert report["overall_risk"] == "critical"


def test_build_risk_report_overall_risk_low():
    """Only low-risk provisions should produce low overall risk."""
    results = {
        "risk_scores": [{"risk_level": "low", "score": 2.0}],
        "gaps": [],
        "comparisons": [],
        "document_count": 1,
    }
    report = build_risk_report(analysis_results=results)
    assert report["overall_risk"] == "low"


def test_build_risk_report_empty_input():
    """Empty input should default to low risk."""
    results = {
        "risk_scores": [],
        "gaps": [],
        "comparisons": [],
        "document_count": 0,
    }
    report = build_risk_report(analysis_results=results)
    assert report["overall_risk"] == "low"
    assert "0 provisions" in report["executive_summary"] or "0 documents" in report["executive_summary"]


def test_export_excel_creates_file(sample_analysis_results, temp_dir):
    """Excel export should create a valid file on disk."""
    report = build_risk_report(analysis_results=sample_analysis_results)
    path = f"{temp_dir}/test_report.xlsx"
    result = export_excel(report=report, output_path=path)
    assert Path(result).exists()
    assert Path(result).stat().st_size > 0


def test_export_html_creates_file(sample_analysis_results, temp_dir):
    """HTML export should create a file with disclaimers."""
    report = build_risk_report(analysis_results=sample_analysis_results)
    path = f"{temp_dir}/test_report.html"
    result = export_html(report=report, output_path=path)
    assert Path(result).exists()
    content = Path(result).read_text()
    assert "DISCLAIMER" in content
    assert "synthetic" in content.lower()


def test_export_html_contains_risk_sections(sample_analysis_results, temp_dir):
    """HTML report should render all sections from the report."""
    report = build_risk_report(analysis_results=sample_analysis_results)
    path = f"{temp_dir}/test_report_sections.html"
    export_html(report=report, output_path=path)
    content = Path(path).read_text()
    assert "Risk Assessment" in content
    assert "Gap Analysis" in content
    assert "Cross-Document Comparison" in content
