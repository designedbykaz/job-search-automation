import { useState } from 'react';
import { ExternalLink, Check, Archive, FileDown, X } from 'lucide-react';

interface Job {
  id: number;
  title: string;
  employer: string;
  location: string;
  cluster: string;
  status: 'to_review' | 'approved' | 'rendered';
  closingDate: string;
  dateFound: string;
}

const jobs: Job[] = [
  { id: 1, title: 'Senior Product Designer', employer: 'NHS Digital', location: 'Leeds', cluster: 'ux_design', status: 'to_review', closingDate: '2026-05-02', dateFound: '2026-04-18' },
  { id: 2, title: 'UX Researcher', employer: 'Department for Education', location: 'London', cluster: 'user_research', status: 'to_review', closingDate: '2026-04-28', dateFound: '2026-04-18' },
  { id: 3, title: 'Service Designer', employer: 'HMRC', location: 'Manchester', cluster: 'service_design', status: 'approved', closingDate: '2026-05-10', dateFound: '2026-04-18' },
  { id: 4, title: 'Product Manager', employer: 'Home Office', location: 'London', cluster: 'product_management', status: 'to_review', closingDate: '2026-04-25', dateFound: '2026-04-18' },
  { id: 5, title: 'Interaction Designer', employer: 'DVLA', location: 'Swansea', cluster: 'ux_design', status: 'approved', closingDate: '2026-05-05', dateFound: '2026-04-17' },
  { id: 6, title: 'Clinical Systems Designer', employer: 'NHS England', location: 'Remote', cluster: 'nhs_healthcare', status: 'to_review', closingDate: '2026-05-12', dateFound: '2026-04-17' },
  { id: 7, title: 'Head of User Research', employer: 'Ministry of Justice', location: 'London', cluster: 'user_research', status: 'rendered', closingDate: '2026-04-30', dateFound: '2026-04-16' },
  { id: 8, title: 'Design System Lead', employer: 'GDS', location: 'London', cluster: 'design_systems', status: 'approved', closingDate: '2026-05-08', dateFound: '2026-04-16' },
];

export function Jobs() {
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const filteredJobs = statusFilter === 'all'
    ? jobs
    : jobs.filter(j => j.status === statusFilter);

  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'to_review': return { label: 'To review', color: 'bg-amber-50 text-amber-700 border-amber-200' };
      case 'approved': return { label: 'Approved', color: 'bg-blue-50 text-blue-700 border-blue-200' };
      case 'rendered': return { label: 'Rendered', color: 'bg-green-50 text-green-700 border-green-200' };
      default: return { label: status, color: 'bg-neutral-50 text-neutral-700 border-neutral-200' };
    }
  };

  return (
    <div className="flex h-full">
      {/* Jobs list */}
      <div className={`flex-1 flex flex-col ${selectedJob ? 'border-r border-neutral-200' : ''}`}>
        <div className="p-6 border-b border-neutral-200">
          <h2 className="text-2xl font-semibold text-neutral-900 mb-4">Jobs</h2>

          {/* Filters */}
          <div className="flex gap-3">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-neutral-300 rounded-md text-sm"
            >
              <option value="all">All statuses</option>
              <option value="to_review">To review</option>
              <option value="approved">Approved</option>
              <option value="rendered">Rendered</option>
            </select>
            <input
              type="text"
              placeholder="Search title or employer..."
              className="flex-1 px-3 py-2 border border-neutral-300 rounded-md text-sm"
            />
          </div>
        </div>

        {/* Table */}
        <div className="flex-1 overflow-auto">
          <table className="w-full">
            <thead className="bg-neutral-50 border-b border-neutral-200 sticky top-0">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase">Title</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase">Employer</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase">Location</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase">Cluster</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase">Closing</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {filteredJobs.map(job => {
                const statusDisplay = getStatusDisplay(job.status);
                return (
                  <tr
                    key={job.id}
                    onClick={() => setSelectedJob(job)}
                    className={`hover:bg-neutral-50 cursor-pointer ${selectedJob?.id === job.id ? 'bg-neutral-50' : ''}`}
                  >
                    <td className="px-6 py-4">
                      <span className={`text-xs px-2 py-1 rounded-full border ${statusDisplay.color}`}>
                        {statusDisplay.label}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-neutral-900">{job.title}</td>
                    <td className="px-6 py-4 text-sm text-neutral-600">{job.employer}</td>
                    <td className="px-6 py-4 text-sm text-neutral-600">{job.location}</td>
                    <td className="px-6 py-4">
                      <span className="text-xs px-2 py-1 rounded bg-neutral-100 text-neutral-700">
                        {job.cluster}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-neutral-600">{job.closingDate}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail pane */}
      {selectedJob && (
        <div className="w-[600px] bg-white flex flex-col">
          <div className="p-6 border-b border-neutral-200 flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-neutral-900 mb-1">{selectedJob.title}</h3>
              <p className="text-sm text-neutral-600 mb-2">{selectedJob.employer} · {selectedJob.location}</p>
              <a href="#" className="text-sm text-blue-600 hover:text-blue-700 inline-flex items-center gap-1">
                View listing <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            <button onClick={() => setSelectedJob(null)} className="p-1 hover:bg-neutral-100 rounded">
              <X className="w-5 h-5 text-neutral-400" />
            </button>
          </div>

          <div className="flex-1 overflow-auto p-6 space-y-6">
            {/* Job description */}
            <div>
              <h4 className="text-sm font-medium text-neutral-900 mb-2">Job description</h4>
              <div className="text-sm text-neutral-600 leading-relaxed space-y-2 max-h-40 overflow-auto border border-neutral-200 rounded-md p-4">
                <p>We are looking for an experienced Senior Product Designer to join our digital team working on critical healthcare services used by millions across the UK.</p>
                <p>You will lead design work across multiple product areas, working closely with user researchers, product managers, and developers to create accessible, user-centered services that meet the needs of patients and healthcare professionals.</p>
                <p>The role requires someone with strong interaction design skills, experience working within government or healthcare contexts, and a deep understanding of accessibility requirements.</p>
              </div>
            </div>

            {/* CV tabs */}
            <div>
              <h4 className="text-sm font-medium text-neutral-900 mb-2">Tailored CV</h4>
              <div className="border border-neutral-200 rounded-md">
                <div className="border-b border-neutral-200 flex">
                  <button className="px-4 py-2 text-sm font-medium text-neutral-900 border-b-2 border-neutral-900">
                    JSON
                  </button>
                  <button className="px-4 py-2 text-sm text-neutral-600 hover:text-neutral-900">
                    Preview
                  </button>
                </div>
                <div className="p-4 bg-neutral-50 font-mono text-xs text-neutral-700 max-h-60 overflow-auto">
                  {`{
  "name": "Alex Jordan",
  "summary": "Senior product designer with 8 years experience designing accessible healthcare services...",
  "experience": [
    {
      "role": "Lead Product Designer",
      "emphasis": "Designed patient-facing services for NHS trusts..."
    }
  ]
}`}
                </div>
              </div>
            </div>

            {/* Template selector */}
            <div>
              <h4 className="text-sm font-medium text-neutral-900 mb-2">Template</h4>
              <div className="flex gap-2">
                {['A', 'B', 'C'].map(template => (
                  <button
                    key={template}
                    className={`flex-1 p-3 border rounded-md text-sm font-medium ${
                      template === 'A'
                        ? 'border-neutral-900 bg-neutral-50 text-neutral-900'
                        : 'border-neutral-200 text-neutral-600 hover:border-neutral-300'
                    }`}
                  >
                    Template {template}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="p-6 border-t border-neutral-200 flex gap-2">
            {selectedJob.status === 'to_review' && (
              <>
                <button className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-neutral-900 text-white rounded-md text-sm font-medium hover:bg-neutral-800">
                  <Check className="w-4 h-4" />
                  Approve
                </button>
                <button className="inline-flex items-center gap-2 px-4 py-2 border border-neutral-300 text-neutral-700 rounded-md text-sm font-medium hover:bg-neutral-50">
                  <Archive className="w-4 h-4" />
                  Archive
                </button>
              </>
            )}
            {selectedJob.status === 'approved' && (
              <button className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-neutral-900 text-white rounded-md text-sm font-medium hover:bg-neutral-800">
                <FileDown className="w-4 h-4" />
                Render PDF
              </button>
            )}
            {selectedJob.status === 'rendered' && (
              <button className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-neutral-900 text-white rounded-md text-sm font-medium hover:bg-neutral-800">
                <FileDown className="w-4 h-4" />
                Download PDF
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
