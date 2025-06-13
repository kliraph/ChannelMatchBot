from typing import List, Dict, Any, Union
from jinja2 import Template
from weasyprint import HTML

def generate_channel_report_pdf(
    metadata: pd.DataFrame,
    analyses: List[Dict[str, Any]],
    output_path: str = "report.pdf"
) -> str:
    """
    Generate a PDF report by merging channel metadata and posts analysis via pandas.
    - metadata: DataFrame with columns
        ['address','name','subscribers','avg_reach','ci_index']
    - analyses: list of dicts with keys
        ['address','scores','comments']
    """
    
    # Expand 'scores' and 'comments' into separate columns
    df_analysis = pd.json_normalize(analyses)  
    # This produces columns like scores.no_swearing, comments.no_swearing, etc.
    
    # Merge on 'address'
    df = pd.merge(metadata, df_analysis, on="address", how="left")

    # Prepare template
    html_template = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
      <meta charset="utf-8">
      <style>
        body { font-family: sans-serif; margin: 20px; }
        h2 { margin-top: 40px; }
        .metadata span { margin-right: 20px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
        th, td { border: 1px solid #ccc; padding: 8px; }
        th { background-color: #f0f0f0; }
      </style>
    </head>
    <body>
    {% for _, row in df.iterrows() %}
      <h2>{{ row.name }} ({{ row.address }})</h2>
      <div class="metadata">
        <span><strong>Подписчики:</strong> {{ row.subscribers }}</span>
        <span><strong>Охват:</strong> {{ row.avg_reach }}</span>
        <span><strong>CI индекс:</strong> {{ row.ci_index }}</span>
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
        {% for crit in criteria %}
          <tr>
            <td>{{ labels[crit] }}</td>
            <td style="text-align:center;">
              {{ row["scores." + crit] if pd.notna(row["scores." + crit]) else '-' }}
            </td>
            <td>{{ row["comments." + crit] or '-' }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    {% endfor %}
    </body>
    </html>
    """

    # Render HTML
    template = Template(html_template)
    # pass df, list of criteria keys, and human-readable labels
    rendered = template.render(
      df=df,
      pd=pd,
      criteria=["no_swearing", "no_gore", "topicality", "no_contradiction", "tone_of_voice"],
      labels={
        "no_swearing": "Отсутствие мата",
        "no_gore": "Отсутствие жести",
        "topicality": "Соответствие тематике",
        "no_contradiction": "Отсутствие противоречий",
        "tone_of_voice": "Tone of Voice"
      }
    )

    # Write PDF
    HTML(string=rendered).write_pdf(output_path)
    return output_path

# Example usage:
# df = pd.DataFrame([...])  # or channels_list = [...]
# pdf_path = generate_channel_report_pdf(df, "report.pdf")
# print(f"PDF report generated at: {pdf_path}")

def generate_channel_report_excel(
    metadata: pd.DataFrame,
    analyses: List[Dict[str, Any]],
    output_path: str = "report.xlsx"
) -> str:
    """
    Generates an Excel report for Telegram channels including metadata and analysis.
    Returns:
    - The filepath of the generated Excel file.
    """
    # Expand 'scores' and 'comments' into separate columns
    df_analysis = pd.json_normalize(analyses)  
    # This produces columns like scores.no_swearing, comments.no_swearing, etc.
    
    # Merge on 'address'
    df = pd.merge(metadata, df_analysis, on="address", how="left")

    # Write to Excel
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Channels Report")
        # Optionally, autofit columns (requires openpyxl >= 2.6.0)
        for column_cells in writer.sheets["Channels Report"].columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            writer.sheets["Channels Report"].column_dimensions[
                column_cells[0].column_letter
            ].width = length + 2

    return output_path


