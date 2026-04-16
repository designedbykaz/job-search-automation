# render_test.py - standalone test: render one tailored CV JSON to PDF

import json, re, os
from pathlib import Path

from dotenv import load_dotenv
from weasyprint import HTML

load_dotenv()

if __name__ == "__main__":
    try:
        # Step 1-2: path and existence check
        input_path = Path("outputs/test_single_job/cv_tailored.json")
        if not input_path.is_file():
            print(
                f"Error: could not find cv_tailored.json at {input_path}. "
                "Run test_tailor.py first."
            )
            raise SystemExit(1)

        # Step 3: load JSON
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Step 3 failed (load JSON from {input_path}): {e}")
            raise

        # Step 4: load template
        template_path = Path("templates/cv_template.html")
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()
        except Exception as e:
            print(f"Step 4 failed (load template {template_path}): {e}")
            raise

        # Step 5: replace placeholders
        try:
            for key, value in data.items():
                placeholder = f"{{{{{key}}}}}"
                if isinstance(value, list):
                    value_str = ", ".join(str(item) for item in value)
                else:
                    value_str = str(value)
                template = template.replace(placeholder, value_str)
        except Exception as e:
            print(f"Step 5 failed (placeholder replacement): {e}")
            raise

        # Step 6: warn on remaining placeholders
        try:
            remaining = re.findall(r"\{\{[^}]+\}\}", template)
            if remaining:
                print(
                    f"Warning: the following placeholders were not filled: {remaining}"
                )
        except Exception as e:
            print(f"Step 6 failed (scan for remaining placeholders): {e}")
            raise

        # Step 7: save HTML
        out_html = Path("outputs/test_single_job/cv_rendered.html")
        try:
            out_html.parent.mkdir(parents=True, exist_ok=True)
            with open(out_html, "w", encoding="utf-8") as f:
                f.write(template)
        except Exception as e:
            print(f"Step 7 failed (write {out_html}): {e}")
            raise

        # Step 8: PDF
        try:
            HTML(filename="outputs/test_single_job/cv_rendered.html").write_pdf(
                "outputs/test_single_job/cv_output.pdf"
            )
        except Exception as e:
            print(f"Step 8 failed (WeasyPrint PDF): {e}")
            raise

        # Step 9
        print("Done. PDF saved to outputs/test_single_job/cv_output.pdf")

    except SystemExit:
        raise
    except Exception as e:
        print(f"render_test.py failed: {e}")
