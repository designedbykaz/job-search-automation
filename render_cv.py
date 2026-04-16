import json
import os
import re
from typing import Any

from weasyprint import HTML


def main() -> None:
    try:
        # Step 1: Load JSON content
        try:
            base_cv_path = os.path.join("content", "base_cv_content.json")
            with open(base_cv_path, "r", encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
        except Exception as e:
            print(f"Error in step 1 (loading JSON from {base_cv_path}): {e}")
            return

        # Step 2: Load HTML template
        try:
            template_path = os.path.join("templates", "cv_template.html")
            with open(template_path, "r", encoding="utf-8") as f:
                html = f.read()
        except Exception as e:
            print(f"Error in step 2 (loading HTML template from {template_path}): {e}")
            return

        # Step 3: Replace placeholders {{KEY}} with values
        try:
            for key, value in data.items():
                placeholder = f"{{{{{key}}}}}"
                if isinstance(value, list):
                    value_str = ", ".join(str(item) for item in value)
                else:
                    value_str = str(value)
                html = html.replace(placeholder, value_str)
        except Exception as e:
            print(f"Error in step 3 (replacing placeholders): {e}")
            return

        # Step 4: Warn about any remaining {{...}} placeholders
        try:
            remaining = set(re.findall(r"{{([^}]+)}}", html))
            if remaining:
                print("Warning: Unreplaced placeholders found:")
                for name in sorted(remaining):
                    print(f"- {{${{{name}}}}}")  # make it obvious in output
        except Exception as e:
            print(f"Error in step 4 (scanning for remaining placeholders): {e}")
            return

        # Step 5: Write rendered HTML
        try:
            outputs_dir = "outputs"
            os.makedirs(outputs_dir, exist_ok=True)
            rendered_path = os.path.join(outputs_dir, "cv_rendered.html")
            with open(rendered_path, "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            print(f"Error in step 5 (writing rendered HTML to {rendered_path}): {e}")
            return

        # Step 6: Generate PDF via WeasyPrint
        try:
            pdf_path = os.path.join(outputs_dir, "cv_output.pdf")
            HTML(filename=rendered_path).write_pdf(pdf_path)
        except Exception as e:
            print(f"Error in step 6 (generating PDF at {pdf_path}): {e}")
            return

        # Step 7: Success message
        print("Done. PDF saved to outputs/cv_output.pdf")

    except Exception as e:
        print(f"Unexpected error in render_cv.py: {e}")


if __name__ == "__main__":
    main()

