import { Eye, Upload, Download, RotateCcw } from 'lucide-react';

export function Content() {
  const files = [
    {
      name: 'base_cv_content.json',
      lastModified: '2026-04-12',
      size: '18.4 KB',
      keys: ['name', 'contact', 'summary', 'experience', 'education', 'skills'],
    },
    {
      name: 'master_profile.json',
      lastModified: '2026-03-28',
      size: '42.1 KB',
      keys: ['profile', 'projects', 'achievements', 'certifications', 'publications'],
    },
  ];

  return (
    <div className="p-8 max-w-5xl">
      <h2 className="text-2xl font-semibold text-neutral-900 mb-8">Content files</h2>

      <div className="grid grid-cols-2 gap-6">
        {files.map((file) => (
          <div key={file.name} className="bg-white border border-neutral-200 rounded-lg p-6">
            <div className="mb-4">
              <h3 className="text-sm font-medium text-neutral-900 mb-1">{file.name}</h3>
              <div className="flex gap-4 text-xs text-neutral-500">
                <span>Modified {file.lastModified}</span>
                <span>{file.size}</span>
              </div>
            </div>

            {/* Preview */}
            <div className="mb-4 p-3 bg-neutral-50 rounded border border-neutral-200">
              <div className="text-xs text-neutral-500 mb-2">Top-level keys:</div>
              <div className="flex flex-wrap gap-1">
                {file.keys.map((key) => (
                  <span
                    key={key}
                    className="text-xs px-2 py-1 bg-white border border-neutral-200 rounded font-mono text-neutral-700"
                  >
                    {key}
                  </span>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-wrap gap-2">
              <button className="inline-flex items-center gap-2 px-3 py-2 border border-neutral-300 text-neutral-700 rounded-md text-sm hover:bg-neutral-50">
                <Eye className="w-4 h-4" />
                View
              </button>
              <button className="inline-flex items-center gap-2 px-3 py-2 border border-neutral-300 text-neutral-700 rounded-md text-sm hover:bg-neutral-50">
                <Upload className="w-4 h-4" />
                Replace
              </button>
              <button className="inline-flex items-center gap-2 px-3 py-2 border border-neutral-300 text-neutral-700 rounded-md text-sm hover:bg-neutral-50">
                <Download className="w-4 h-4" />
                Download
              </button>
              <button className="inline-flex items-center gap-2 px-3 py-2 border border-neutral-300 text-neutral-700 rounded-md text-sm hover:bg-neutral-50">
                <RotateCcw className="w-4 h-4" />
                Revert
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-900">
          Files are validated before replacement. If a file does not match the expected schema, the upload will be rejected and the existing file will remain unchanged.
        </p>
      </div>
    </div>
  );
}
