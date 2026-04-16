# render_cover_letter_test.py - standalone: render cover_letter_tailored.json to PDF

import json
import re
from pathlib import Path

from dotenv import load_dotenv
from weasyprint import HTML

load_dotenv()

if __name__ == "__main__":
    try:
        json_path = Path("outputs/test_single_job/cover_letter_tailored.json")
        template_path = Path("templates/cover_letter_template.html")
        output_html = Path("outputs/test_single_job/cover_letter_rendered.html")
        output_pdf = Path("outputs/test_single_job/cover_letter_output.pdf")

        if not json_path.is_file():
            print(
                "Error: cover_letter_tailored.json not found. "
                "Run test_cover_letter.py first."
            )
            raise SystemExit(1)

        if not template_path.is_file():
            print(
                "Error: cover_letter_template.html not found in templates/."
            )
            raise SystemExit(1)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["NAME"] = "YOUR_NAME_HERE"
        data["EMPLOYER"] = "YOUR_EMPLOYER_HERE"
        data["JOB_TITLE"] = "YOUR_JOB_TITLE_HERE"

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            if isinstance(value, list):
                value_str = ", ".join(str(item) for item in value)
            else:
                value_str = str(value)
            template = template.replace(placeholder, value_str)

        remaining = re.findall(r"\{\{[^}]+\}\}", template)
        if remaining:
            print(f"Warning: unfilled placeholders: {remaining}")

        output_html.parent.mkdir(parents=True, exist_ok=True)
        with open(output_html, "w", encoding="utf-8") as f:
            f.write(template)

        HTML(filename=str(output_html)).write_pdf(str(output_pdf))

        print(
            "Done. PDF saved to "
            "outputs/test_single_job/cover_letter_output.pdf"
        )
    except SystemExit:
        raise
    except Exception as e:
        print(f"render_cover_letter_test failed: {e!r}")
        raise SystemExit(1) from e
