"""TAD – PDF report generation."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)

from constants import (
    COLUMN_SENSOR_ID,
    COLUMN_TEMPERATURE,
    COLUMN_TIMESTAMP,
    DATETIME_FORMAT_PY,
    PDF_FIGURE_CAPTION_TEMPLATE,
    PDF_FILTERED_RANGE_TEMPLATE,
    PDF_FOOTER_MESSAGE,
    PDF_GLOBAL_STATS_TITLE,
    PDF_NO_DATA_MESSAGE,
    PDF_REPORT_TITLE,
    PDF_SENSOR_TITLE_TEMPLATE,
    PDF_STATISTICS_SECTION_TITLE,
    PDF_STYLE_CODE,
    PDF_STYLE_HEADING_2,
    PDF_STYLE_HEADING_3,
    PDF_STYLE_ITALIC,
    PDF_STYLE_NORMAL,
    PDF_STYLE_TITLE,
    PDF_VISUALIZATIONS_TITLE,
)
from visualizations import build_pdf_figures, fig_to_png_buffer


def append_pdf_stats(df, story, styles):
    """Append global and per-sensor statistics text blocks to `story`."""
    story.append(Spacer(1, 12))
    story.append(Paragraph(PDF_STATISTICS_SECTION_TITLE, styles[PDF_STYLE_HEADING_2]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(PDF_GLOBAL_STATS_TITLE, styles[PDF_STYLE_HEADING_3]))
    story.append(
        Preformatted(
            df[COLUMN_TEMPERATURE].describe().to_string(float_format=lambda value: f"{value:.2f}"),
            styles[PDF_STYLE_CODE],
        )
    )
    for sensor_id, sensor_data in df.groupby(COLUMN_SENSOR_ID):
        story.append(Spacer(1, 6))
        story.append(Paragraph(PDF_SENSOR_TITLE_TEMPLATE.format(sensor_id=sensor_id), styles[PDF_STYLE_HEADING_3]))
        story.append(
            Preformatted(
                sensor_data[COLUMN_TEMPERATURE].describe().to_string(float_format=lambda value: f"{value:.2f}"),
                styles[PDF_STYLE_CODE],
            )
        )


def append_pdf_visualizations(df, story, styles, doc):
    """Append a page break followed by all chart images to `story`."""
    story.append(PageBreak())
    story.append(Paragraph(PDF_VISUALIZATIONS_TITLE, styles[PDF_STYLE_HEADING_2]))
    story.append(Spacer(1, 8))
    available_width = A4[0] - doc.leftMargin - doc.rightMargin
    chart_width = available_width
    chart_height = chart_width * 0.5
    for index, (caption, figure) in enumerate(build_pdf_figures(df), start=1):
        chart_buffer = fig_to_png_buffer(figure)
        story.append(Image(chart_buffer, width=chart_width, height=chart_height))
        story.append(Spacer(1, 2))
        story.append(
            Paragraph(PDF_FIGURE_CAPTION_TEMPLATE.format(index=index, caption=caption), styles[PDF_STYLE_ITALIC])
        )
        story.append(Spacer(1, 8))


def create_pdf_doc(pdf_path):
    """Create and return a ReportLab `SimpleDocTemplate` configured for A4 output."""
    return SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )


def export_pdf_report(df, pdf_path, include_stats=True, include_viz=True):
    """Build and write a full PDF report with optional statistics and visualizations."""
    styles = getSampleStyleSheet()
    doc = create_pdf_doc(pdf_path)
    story = [Paragraph(PDF_REPORT_TITLE, styles[PDF_STYLE_TITLE]), Spacer(1, 8)]
    story.append(Spacer(1, 4))
    if df.empty:
        story.append(Paragraph(PDF_NO_DATA_MESSAGE, styles[PDF_STYLE_NORMAL]))
    else:
        min_date = df[COLUMN_TIMESTAMP].min()
        max_date = df[COLUMN_TIMESTAMP].max()
        range_text = PDF_FILTERED_RANGE_TEMPLATE.format(
            min_date=min_date.strftime(DATETIME_FORMAT_PY),
            max_date=max_date.strftime(DATETIME_FORMAT_PY),
        )
        story.append(Paragraph(range_text, styles[PDF_STYLE_ITALIC]))
        story.append(Spacer(1, 10))
    if include_stats and not df.empty:
        append_pdf_stats(df, story, styles)
    if include_viz and not df.empty:
        append_pdf_visualizations(df, story, styles, doc)
    story.append(Spacer(1, 12))
    story.append(Paragraph(PDF_FOOTER_MESSAGE, styles[PDF_STYLE_ITALIC]))
    doc.build(story)
