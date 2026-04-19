import { Eye, EyeOff, ExternalLink } from 'lucide-react';
import { useState } from 'react';

export function Settings() {
  const [showApiKey, setShowApiKey] = useState(false);

  return (
    <div className="p-8 max-w-3xl">
      <h2 className="text-2xl font-semibold text-neutral-900 mb-8">Settings</h2>

      <div className="space-y-8">
        {/* API Configuration */}
        <div className="bg-white border border-neutral-200 rounded-lg p-6">
          <h3 className="text-sm font-medium text-neutral-900 mb-4">API configuration</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-neutral-700 mb-2">Anthropic API key</label>
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    value="sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxx"
                    readOnly
                    className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm font-mono"
                  />
                  <button
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-neutral-100 rounded"
                  >
                    {showApiKey ? (
                      <EyeOff className="w-4 h-4 text-neutral-400" />
                    ) : (
                      <Eye className="w-4 h-4 text-neutral-400" />
                    )}
                  </button>
                </div>
                <button className="px-4 py-2 border border-neutral-300 text-neutral-700 rounded-md text-sm hover:bg-neutral-50">
                  Edit
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm text-neutral-700 mb-2">Claude model</label>
              <select className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm">
                <option>claude-opus-4-20250514</option>
                <option>claude-sonnet-4-20250514</option>
                <option>claude-3-5-sonnet-20241022</option>
              </select>
            </div>
          </div>
        </div>

        {/* Google Sheets */}
        <div className="bg-white border border-neutral-200 rounded-lg p-6">
          <h3 className="text-sm font-medium text-neutral-900 mb-4">Google Sheets</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-neutral-700 mb-2">Sheets ID</label>
              <input
                type="text"
                value="1abc123xyz456def789ghi012jkl345mno"
                readOnly
                className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm font-mono"
              />
            </div>

            <div>
              <label className="block text-sm text-neutral-700 mb-2">Credentials file path</label>
              <input
                type="text"
                value="~/.config/pipeline/credentials.json"
                readOnly
                className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm font-mono"
              />
            </div>

            <button className="px-4 py-2 border border-neutral-300 text-neutral-700 rounded-md text-sm hover:bg-neutral-50">
              Test connection
            </button>
          </div>
        </div>

        {/* Scraper defaults */}
        <div className="bg-white border border-neutral-200 rounded-lg p-6">
          <h3 className="text-sm font-medium text-neutral-900 mb-4">Scraper defaults</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-neutral-700 mb-2">Request delay (seconds)</label>
              <input
                type="number"
                value="2"
                className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm"
              />
            </div>

            <div>
              <label className="block text-sm text-neutral-700 mb-2">User agent</label>
              <input
                type="text"
                value="Mozilla/5.0 (compatible; JobPipeline/1.0)"
                className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm font-mono"
              />
            </div>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                defaultChecked
                className="w-4 h-4 rounded border-neutral-300"
              />
              <span className="text-sm text-neutral-700">Enforce robots.txt</span>
            </label>
          </div>
        </div>

        {/* Storage */}
        <div className="bg-white border border-neutral-200 rounded-lg p-6">
          <h3 className="text-sm font-medium text-neutral-900 mb-4">Storage</h3>
          <div>
            <label className="block text-sm text-neutral-700 mb-2">Output directory</label>
            <div className="flex gap-2">
              <input
                type="text"
                value="~/Documents/job-pipeline/output"
                readOnly
                className="flex-1 px-3 py-2 border border-neutral-300 rounded-md text-sm font-mono"
              />
              <button className="px-4 py-2 border border-neutral-300 text-neutral-700 rounded-md text-sm hover:bg-neutral-50">
                Change
              </button>
            </div>
          </div>
        </div>

        {/* About */}
        <div className="bg-white border border-neutral-200 rounded-lg p-6">
          <h3 className="text-sm font-medium text-neutral-900 mb-4">About</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-neutral-600">Version</span>
              <span className="text-neutral-900 font-mono">2.0.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-600">Last Sheet sync</span>
              <span className="text-neutral-900">18 Apr 2026, 14:32</span>
            </div>
            <div>
              <a
                href="#"
                className="text-blue-600 hover:text-blue-700 inline-flex items-center gap-1"
              >
                View repository <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
