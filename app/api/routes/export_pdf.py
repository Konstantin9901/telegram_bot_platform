from fastapi import APIRouter, Body
from fastapi.responses import FileResponse
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from pathlib import Path

router = APIRouter()

# Путь к шаблонам (корень проекта/templates)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

@router.post("/export/pdf")
def export_pdf(payload: dict = Body(...)):
    summary = payload.get("summary", "")
    rows = payload.get("rows", [])

    template = env.get_template("report.html")
    html_content = template.render(summary=summary, rows=rows)

    pdf_file = "roi-report.pdf"
    HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf(
        pdf_file,
        stylesheets=[CSS(string="""
            body { font-family: "DejaVu Sans", sans-serif; }
            table, th, td { font-family: "DejaVu Sans", sans-serif; }
        """)]
    )

    return FileResponse(pdf_file, media_type="application/pdf", filename=pdf_file)
