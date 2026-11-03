"""Weekly delivery report, rendered to HTML."""
import quillparse
import tabulon


def render(rows):
    table = tabulon.table(rows)
    return quillparse.to_html(table)
