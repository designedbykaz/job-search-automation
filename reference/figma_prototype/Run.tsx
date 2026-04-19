import { useState } from 'react';
import { Play, StopCircle, ExternalLink } from 'lucide-react';

export function Run() {
  const [isRunning, setIsRunning] = useState(false);
  const [scrapers, setScrapers] = useState([
    { id: 1, name: 'Indeed UK', enabled: true, status: 'healthy' },
    { id: 2, name: 'NHS Jobs', enabled: true, status: 'healthy' },
    { id: 3, name: 'Civil Service Jobs', enabled: false, status: 'untested' },
  ]);

  const [clusters, setClusters] = useState([
    { id: 1, name: 'nhs_healthcare', enabled: true, keywords: 80 },
    { id: 2, name: 'ux_design', enabled: true, keywords: 25 },
    { id: 3, name: 'product_management', enabled: true, keywords: 42 },
    { id: 4, name: 'user_research', enabled: true, keywords: 31 },
    { id: 5, name: 'service_design', enabled: false, keywords: 18 },
    { id: 6, name: 'digital_delivery', enabled: true, keywords: 36 },
    { id: 7, name: 'design_systems', enabled: false, keywords: 22 },
  ]);

  const toggleScraper = (id: number) => {
    setScrapers(scrapers.map(s => s.id === id ? { ...s, enabled: !s.enabled } : s));
  };

  const toggleCluster = (id: number) => {
    setClusters(clusters.map(c => c.id === id ? { ...c, enabled: !c.enabled } : c));
  };

  if (isRunning) {
    return (
      <div className="p-8 max-w-6xl">
        <h2 className="text-2xl font-semibold text-neutral-900 mb-8">Run pipeline</h2>

        <div className="bg-white border border-neutral-200 rounded-lg mb-6">
          <div className="px-6 py-4 border-b border-neutral-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
              <span className="text-sm font-medium text-neutral-900">Running</span>
            </div>
            <button
              onClick={() => setIsRunning(false)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm font-medium hover:bg-red-100 transition-colors"
            >
              <StopCircle className="w-4 h-4" />
              Cancel run
            </button>
          </div>

          <div className="p-6 bg-neutral-50 font-mono text-sm max-h-96 overflow-auto">
            <div className="space-y-1 text-neutral-700">
              <div>[14:32:15] Starting pipeline run</div>
              <div>[14:32:15] Active scrapers: Indeed UK, NHS Jobs</div>
              <div>[14:32:15] Active clusters: nhs_healthcare, ux_design, product_management, user_research, digital_delivery</div>
              <div>[14:32:16] Scraping Indeed UK...</div>
              <div>[14:32:18] Indeed UK: 42 listings found</div>
              <div>[14:32:18] Scraping NHS Jobs...</div>
              <div>[14:32:21] NHS Jobs: 28 listings found</div>
              <div>[14:32:21] Total listings: 70</div>
              <div>[14:32:21] Filtering and deduplicating...</div>
              <div>[14:32:22] Removed 12 duplicates</div>
              <div>[14:32:22] Matching against keyword clusters...</div>
              <div>[14:32:23] nhs_healthcare: 15 matches</div>
              <div>[14:32:23] ux_design: 8 matches</div>
              <div>[14:32:23] product_management: 3 matches</div>
              <div>[14:32:23] user_research: 6 matches</div>
              <div>[14:32:23] Total matches: 32</div>
              <div>[14:32:23] Tailoring CVs...</div>
              <div>[14:32:25] Tailored 1/32: Senior Product Designer - NHS Digital</div>
              <div>[14:32:27] Tailored 2/32: UX Researcher - Department for Education</div>
              <div className="text-blue-600">[14:32:29] In progress...</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl">
      <h2 className="text-2xl font-semibold text-neutral-900 mb-8">Run pipeline</h2>

      {/* Scraper selection */}
      <div className="bg-white border border-neutral-200 rounded-lg p-6 mb-6">
        <h3 className="text-sm font-medium text-neutral-900 mb-4">Scrapers</h3>
        <div className="space-y-3">
          {scrapers.map(scraper => (
            <label key={scraper.id} className="flex items-center justify-between p-3 rounded-md border border-neutral-200 hover:bg-neutral-50 cursor-pointer">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={scraper.enabled}
                  onChange={() => toggleScraper(scraper.id)}
                  className="w-4 h-4 rounded border-neutral-300"
                />
                <span className="text-sm text-neutral-900">{scraper.name}</span>
              </div>
              <span className={`text-xs px-2 py-1 rounded-full ${
                scraper.status === 'healthy' ? 'bg-green-50 text-green-700' : 'bg-neutral-100 text-neutral-600'
              }`}>
                {scraper.status}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Cluster selection */}
      <div className="bg-white border border-neutral-200 rounded-lg p-6 mb-6">
        <h3 className="text-sm font-medium text-neutral-900 mb-4">Keyword clusters</h3>
        <div className="grid grid-cols-2 gap-3">
          {clusters.map(cluster => (
            <label key={cluster.id} className="flex items-center gap-3 p-3 rounded-md border border-neutral-200 hover:bg-neutral-50 cursor-pointer">
              <input
                type="checkbox"
                checked={cluster.enabled}
                onChange={() => toggleCluster(cluster.id)}
                className="w-4 h-4 rounded border-neutral-300"
              />
              <div className="flex-1">
                <div className="text-sm text-neutral-900">{cluster.name}</div>
                <div className="text-xs text-neutral-500">{cluster.keywords} keywords</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white border border-neutral-200 rounded-lg p-6 mb-6">
        <h3 className="text-sm font-medium text-neutral-900 mb-4">Filters</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-neutral-700 mb-2">Location</label>
            <input
              type="text"
              placeholder="e.g., London, Manchester, Remote"
              className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm"
            />
          </div>
          <div>
            <label className="block text-sm text-neutral-700 mb-2">Date range</label>
            <select className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm">
              <option>Since last run</option>
              <option>Last 24 hours</option>
              <option>Last 7 days</option>
              <option>Last 30 days</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-neutral-700 mb-2">Mode</label>
            <select className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm">
              <option>Full run (scrape + tailor)</option>
              <option>Scrape only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Run button */}
      <button
        onClick={() => setIsRunning(true)}
        className="w-full inline-flex items-center justify-center gap-2 px-4 py-3 bg-neutral-900 text-white rounded-md text-sm font-medium hover:bg-neutral-800 transition-colors"
      >
        <Play className="w-4 h-4" />
        Run pipeline
      </button>
    </div>
  );
}
