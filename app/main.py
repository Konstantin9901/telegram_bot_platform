from fastapi import FastAPI, Body
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# 🔗 Импортируем роутер analytics
from app.api.routes import analytics

app = FastAPI()

# Подключаем роутер из analytics.py
app.include_router(analytics.router)

# Путь к шаблонам (корень проекта/templates)
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

@app.post("/export/pdf")
def export_pdf(payload: dict = Body(...)):
    metric = payload.get("metric", "roi")
    summary = payload.get("summary", "")
    rows = payload.get("rows", [])
    campaigns = payload.get("campaigns", [])

    template = env.get_template("report.html")
    html_content = template.render(
        metric=metric.upper(),
        summary=summary,
        rows=rows,
        campaigns=campaigns
    )

    pdf_file = f"{metric}-report.pdf"
    HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf(
        pdf_file,
        stylesheets=[CSS(string="""
            body { font-family: "DejaVu Sans", sans-serif; }
            table, th, td { font-family: "DejaVu Sans", sans-serif; }
        """)]
    )

    return FileResponse(pdf_file, media_type="application/pdf", filename=pdf_file)

# ✅ Подключаем фронтенд (дашборд)
app.mount("/", StaticFiles(directory="webapp", html=True), name="webapp")

# ✅ Проверка API
@app.get("/check")
def check():
    return {"status": "ok", "message": "API живой и готов к работе"}

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
















