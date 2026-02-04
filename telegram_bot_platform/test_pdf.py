from weasyprint import HTML, CSS

html = "<p>Проверка кириллицы: АБВГДЕЁЖЗИЙ</p>"
css = CSS(string="""
    body { font-family: "DejaVu Sans", sans-serif; }
""")

HTML(string=html).write_pdf("test.pdf", stylesheets=[css])
