import { Eye, Upload, Download } from 'lucide-react';

export function Templates() {
  const templates = [
    { id: 'A', name: 'Classic Single Column', uploaded: true },
    { id: 'B', name: 'Modern Two Column', uploaded: true },
    { id: 'C', name: 'Minimal Timeline', uploaded: true },
  ];

  const clusters = [
    { name: 'nhs_healthcare', defaultTemplate: 'A' },
    { name: 'ux_design', defaultTemplate: 'B' },
    { name: 'product_management', defaultTemplate: 'B' },
    { name: 'user_research', defaultTemplate: 'A' },
    { name: 'service_design', defaultTemplate: 'B' },
    { name: 'digital_delivery', defaultTemplate: 'C' },
    { name: 'design_systems', defaultTemplate: 'B' },
  ];

  return (
    <div className="p-8 max-w-6xl">
      <h2 className="text-2xl font-semibold text-neutral-900 mb-8">Templates</h2>

      {/* Template cards */}
      <div className="grid grid-cols-3 gap-6 mb-12">
        {templates.map((template) => (
          <div key={template.id} className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
            {/* Preview */}
            <div className="aspect-[8.5/11] bg-neutral-100 border-b border-neutral-200 flex items-center justify-center">
              <div className="text-neutral-400 text-sm">Template {template.id} preview</div>
            </div>

            {/* Details */}
            <div className="p-4">
              <div className="mb-3">
                <input
                  type="text"
                  value={template.name}
                  className="w-full text-sm font-medium text-neutral-900 border-none outline-none p-0 focus:ring-0"
                />
              </div>

              {/* Actions */}
              <div className="flex flex-wrap gap-2">
                <button className="inline-flex items-center gap-2 px-3 py-1.5 border border-neutral-300 text-neutral-700 rounded text-xs hover:bg-neutral-50">
                  <Eye className="w-3 h-3" />
                  Preview
                </button>
                <button className="inline-flex items-center gap-2 px-3 py-1.5 border border-neutral-300 text-neutral-700 rounded text-xs hover:bg-neutral-50">
                  <Upload className="w-3 h-3" />
                  Replace
                </button>
                <button className="inline-flex items-center gap-2 px-3 py-1.5 border border-neutral-300 text-neutral-700 rounded text-xs hover:bg-neutral-50">
                  <Download className="w-3 h-3" />
                  Download
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Cluster defaults */}
      <div className="bg-white border border-neutral-200 rounded-lg">
        <div className="px-6 py-4 border-b border-neutral-200">
          <h3 className="text-sm font-medium text-neutral-900">Cluster defaults</h3>
          <p className="text-sm text-neutral-500 mt-1">
            Choose which template each cluster should use by default. Individual jobs can override this setting.
          </p>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {clusters.map((cluster) => (
              <div key={cluster.name} className="flex items-center justify-between">
                <span className="text-sm text-neutral-900">{cluster.name}</span>
                <select
                  value={cluster.defaultTemplate}
                  className="px-3 py-2 border border-neutral-300 rounded-md text-sm"
                >
                  <option value="A">Template A</option>
                  <option value="B">Template B</option>
                  <option value="C">Template C</option>
                </select>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
