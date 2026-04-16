# test_cover_letter.py - standalone: generate tailored cover letter JSON for one test job

from pathlib import Path

from dotenv import load_dotenv

from pipeline.tailor import tailor_cover_letter

load_dotenv()

if __name__ == "__main__":
    try:
        test_job = {
            "title": "Clinical Engineering Apprentice",
            "employer": "NHS Jobs",
            "location": "London",
            "date": "2026-03-21",
            "url": "https://findajob.dwp.gov.uk/details/test",
            "description": (
                "We are looking for an enthusiastic apprentice "
                "to join our Clinical Engineering team. The role involves "
                "supporting qualified engineers in the maintenance and repair "
                "of medical equipment. No prior experience required. Training "
                "will be provided."
            ),
            "source": "govuk",
        }

        output_folder = Path("outputs/test_single_job")
        output_folder.mkdir(parents=True, exist_ok=True)

        print("Generating cover letter...")
        tailor_cover_letter(test_job, output_folder)
        print(
            "Done. Cover letter saved to "
            "outputs/test_single_job/cover_letter_tailored.json"
        )
    except Exception as e:
        print(f"test_cover_letter failed: {e!r}")
        raise SystemExit(1) from e
