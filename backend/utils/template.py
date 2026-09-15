import os
# pyrefly: ignore [missing-import]
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'frontend', 'pages')

env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)


def render_template(handler, template_name, context=None, status_code=200):
    if context is None:
        context = {}

    template = env.get_template(template_name)
    html_content = template.render(**context)

    body_bytes = html_content.encode('utf-8')
    handler.send_response(status_code)
    handler.send_header('Content-Type', 'text/html; charset=utf-8')
    handler.send_header('Content-Length', str(len(body_bytes)))
    handler.end_headers()
    handler.wfile.write(body_bytes)
