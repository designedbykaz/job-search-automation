from pipeline.tailor import tailor_cv
from pathlib import Path
import json

# Use a single hardcoded test job
test_job = {
    "title": "Clinical Engineering Apprentice",
    "employer": "NHS Jobs",
    "location": "London",
    "date": "2026-03-21",
    "url": "https://findajob.dwp.gov.uk/details/test",
    "description": "We are looking for an enthusiastic apprentice to join our Clinical Engineering team. The role involves supporting qualified engineers in the maintenance and repair of medical equipment. No prior experience required. Training will be provided.",
    "source": "govuk"
}

output_folder = Path("outputs/test_single_job")
output_folder.mkdir(parents=True, exist_ok=True)

print("Testing tailor_cv...")
result = tailor_cv(test_job, output_folder)
print("Success! Tailored CV saved.")
print(f"Keys returned: {list(result.keys())}")

if __name__ == "__main__":
    pass

