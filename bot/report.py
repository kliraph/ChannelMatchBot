import pandas as pd
from typing import List, Dict, Any, Union
from jinja2 import Template
from weasyprint import HTML

def generate_channel_report_pdf(
    channels_data: Union[pd.DataFrame, List[Dict[str, Any]]],
    output_path: str = "channel_report.pdf"
) -> str:
    """
    Generates a PDF report for Telegram channels including metadata and analysis.
    
    Parameters:
    - channels_data: either a pandas DataFrame or a list of dicts where each dict contains:
        {
            "address": str,
            "name": str,
            "subscribers": int,
            "avg_reach": int,
            "ci_index": int,
            "scores": dict[str, int],
            "comments": dict[str, str]
        }
    - output_path: file path where the PDF will be written
    
    Returns:
    - The filepath of the generated PDF.
    """
    # Normalize to list of dicts
    if isinstance(channels_data, pd.DataFrame):
        channels = channels_data.to_dict(orient="records")
    else:
        channels = channels_data

    # HTML template for the report
    html_template = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="utf-8">
        <style>
            body { font-family: sans-serif; margin: 20px; }
            h2 { margin-top: 40px; }
            .metadata { margin-bottom: 10px; }
            .metadata span { margin-right: 20px; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
            th, td { border: 1px solid #ccc; padding: 8px; }
            th { background-color: #f0f0f0; }
        </style>
    </head>
    <body>
    {% for ch in channels %}
        <h2>{{ ch.name }} ({{ ch.address }})</h2>
        <div class="metadata">
            <span><strong>Подписчики:</strong> {{ ch.subscribers }}</span>
            <span><strong>Охват:</strong> {{ ch.avg_reach }}</span>
            <span><strong>CI индекс:</strong> {{ ch.ci_index }}</span>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Критерий</th>
                    <th>Оценка</th>
                    <th>Комментарий</th>
                </tr>
            </thead>
            <tbody>
            {% for crit, score in ch.scores.items() %}
                <tr>
                    <td>{{ crit }}</td>
                    <td style="text-align: center;">{{ score }}</td>
                    <td>{{ ch.comments[crit] }}</td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
    {% endfor %}
    </body>
    </html>
    """

    # Render HTML with data
    template = Template(html_template)
    rendered_html = template.render(channels=channels)

    # Convert HTML to PDF
    HTML(string=rendered_html).write_pdf(output_path)

    return output_path

# Example usage:
# df = pd.DataFrame([...])  # or channels_list = [...]
# pdf_path = generate_channel_report_pdf(df, "report.pdf")
# print(f"PDF report generated at: {pdf_path}")


