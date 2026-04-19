import { Save, RotateCcw, Play } from 'lucide-react';
import { useState } from 'react';

export function Prompts() {
  const [selectedJob, setSelectedJob] = useState('');
  const [testOutput, setTestOutput] = useState('');

  const defaultPrompt = `You are tailoring a CV for a specific job application.

Given:
- Job title: {{JOB_TITLE}}
- Employer: {{EMPLOYER}}
- Job description: {{JOB_DESCRIPTION}}
- Base CV content: {{BASE_CV}}
- Master profile: {{MASTER_PROFILE}}

Produce a tailored CV as JSON that:
1. Emphasizes relevant experience from the master profile
2. Adjusts the summary to match the role requirements
3. Reorders and highlights skills that align with the job
4. Maintains honesty while optimizing presentation

Return only valid JSON matching the base CV schema.`;

  return (
    <div className="flex h-full">
      {/* Editor */}
      <div className="flex-1 flex flex-col border-r border-neutral-200">
        <div className="p-6 border-b border-neutral-200">
          <h2 className="text-2xl font-semibold text-neutral-900 mb-4">Prompts</h2>
          <div className="flex gap-2">
            <button className="px-3 py-2 bg-neutral-100 text-neutral-900 rounded-md text-sm font-medium">
              CV prompt
            </button>
          </div>
        </div>

        <div className="flex-1 flex flex-col p-6">
          <div className="flex gap-2 mb-4">
            <button className="inline-flex items-center gap-2 px-4 py-2 bg-neutral-900 text-white rounded-md text-sm font-medium hover:bg-neutral-800">
              <Save className="w-4 h-4" />
              Save
            </button>
            <button className="inline-flex items-center gap-2 px-4 py-2 border border-neutral-300 text-neutral-700 rounded-md text-sm hover:bg-neutral-50">
              <RotateCcw className="w-4 h-4" />
              Revert
            </button>
          </div>

          <div className="flex-1 border border-neutral-200 rounded-md overflow-hidden">
            <textarea
              value={defaultPrompt}
              className="w-full h-full p-4 font-mono text-sm resize-none focus:outline-none"
              spellCheck={false}
            />
          </div>
        </div>
      </div>

      {/* Test panel */}
      <div className="w-[480px] bg-white flex flex-col">
        <div className="p-6 border-b border-neutral-200">
          <h3 className="text-sm font-medium text-neutral-900 mb-4">Test against job</h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-neutral-700 mb-2">Select job</label>
              <select
                value={selectedJob}
                onChange={(e) => setSelectedJob(e.target.value)}
                className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm"
              >
                <option value="">Choose a job...</option>
                <option value="1">Senior Product Designer - NHS Digital</option>
                <option value="2">UX Researcher - Department for Education</option>
                <option value="3">Service Designer - HMRC</option>
              </select>
            </div>

            <button
              disabled={!selectedJob}
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 bg-neutral-900 text-white rounded-md text-sm font-medium hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="w-4 h-4" />
              Run test
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-auto p-6">
          {selectedJob ? (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-medium text-neutral-900">Output</h4>
                <button className="text-xs text-neutral-600 hover:text-neutral-900">
                  Show diff
                </button>
              </div>
              <div className="border border-neutral-200 rounded-md p-4 bg-neutral-50 font-mono text-xs text-neutral-700 overflow-auto">
                <pre>{`{
  "name": "Alex Jordan",
  "contact": {
    "email": "alex.jordan@example.com",
    "phone": "+44 7700 900000"
  },
  "summary": "Senior product designer with 8 years of experience designing accessible digital services in healthcare and public sector contexts. Proven track record of leading design work across complex multi-stakeholder environments.",
  "experience": [
    {
      "role": "Lead Product Designer",
      "organization": "Public Sector Digital Team",
      "period": "2020-present",
      "highlights": [
        "Led design of patient-facing services used by 2M+ users",
        "Established accessibility standards across product portfolio",
        "Mentored junior designers and researchers"
      ]
    }
  ],
  "skills": [
    "Interaction design",
    "Accessibility (WCAG 2.1 AA)",
    "User-centered design",
    "Service design",
    "Design systems"
  ]
}`}</pre>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-sm text-neutral-500">
              Select a job to test the prompt
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
