import { Play, FileCheck } from 'lucide-react';
import { Link } from 'react-router';

export function Dashboard() {
  return (
    <div className="p-8 max-w-6xl">
      <h2 className="text-2xl font-semibold text-neutral-900 mb-8">Dashboard</h2>

      {/* Status block */}
      <div className="bg-white border border-neutral-200 rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full bg-green-500"></div>
              <span className="text-sm font-medium text-neutral-900">Pipeline idle</span>
            </div>
            <p className="text-sm text-neutral-500">Last run completed 2 hours ago</p>
          </div>
          <div className="flex gap-3">
            <Link
              to="/run"
              className="inline-flex items-center gap-2 px-4 py-2 bg-neutral-900 text-white rounded-md text-sm font-medium hover:bg-neutral-800 transition-colors"
            >
              <Play className="w-4 h-4" />
              Run pipeline
            </Link>
            <button className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-neutral-300 text-neutral-700 rounded-md text-sm font-medium hover:bg-neutral-50 transition-colors">
              <FileCheck className="w-4 h-4" />
              Render approved
            </button>
          </div>
        </div>
      </div>

      {/* Counters */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white border border-neutral-200 rounded-lg p-5">
          <div className="text-3xl font-semibold text-neutral-900 mb-1">12</div>
          <div className="text-sm text-neutral-600">Awaiting review</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-5">
          <div className="text-3xl font-semibold text-neutral-900 mb-1">5</div>
          <div className="text-sm text-neutral-600">Approved, unrendered</div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-5">
          <div className="text-3xl font-semibold text-neutral-900 mb-1">3</div>
          <div className="text-sm text-neutral-600">Rendered today</div>
        </div>
      </div>

      {/* Recent activity */}
      <div className="bg-white border border-neutral-200 rounded-lg">
        <div className="px-6 py-4 border-b border-neutral-200">
          <h3 className="text-sm font-medium text-neutral-900">Recent activity</h3>
        </div>
        <div className="divide-y divide-neutral-100">
          {[
            { action: 'Pipeline run completed', detail: '18 jobs scraped, 12 matched', time: '2 hours ago' },
            { action: 'CV rendered', detail: 'Senior Product Designer at NHS Digital', time: '5 hours ago' },
            { action: 'CV rendered', detail: 'UX Researcher at Department for Education', time: '5 hours ago' },
            { action: 'Prompt edited', detail: 'CV tailoring prompt updated', time: '1 day ago' },
            { action: 'Pipeline run completed', detail: '24 jobs scraped, 15 matched', time: '1 day ago' },
            { action: 'Template uploaded', detail: 'Template B replaced', time: '3 days ago' },
          ].map((item, i) => (
            <div key={i} className="px-6 py-3 flex items-center justify-between hover:bg-neutral-50">
              <div>
                <div className="text-sm text-neutral-900">{item.action}</div>
                <div className="text-sm text-neutral-500">{item.detail}</div>
              </div>
              <div className="text-sm text-neutral-400">{item.time}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
