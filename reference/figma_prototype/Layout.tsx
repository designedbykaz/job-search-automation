import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router';
import {
  LayoutDashboard,
  Play,
  Briefcase,
  FileText,
  Code,
  Layers,
  Settings as SettingsIcon
} from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Run', href: '/run', icon: Play },
  { name: 'Jobs', href: '/jobs', icon: Briefcase },
  { name: 'Content', href: '/content', icon: FileText },
  { name: 'Prompts', href: '/prompts', icon: Code },
  { name: 'Templates', href: '/templates', icon: Layers },
  { name: 'Settings', href: '/settings', icon: SettingsIcon },
];

export function Layout({ children }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="flex h-screen bg-neutral-50">
      {/* Sidebar */}
      <div className="w-60 bg-white border-r border-neutral-200 flex flex-col">
        <div className="h-14 flex items-center px-6 border-b border-neutral-200">
          <h1 className="font-semibold text-neutral-900">Pipeline</h1>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? 'bg-neutral-100 text-neutral-900'
                    : 'text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900'
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Main content area */}
      <div className="flex-1 flex flex-col">
        {/* Top bar */}
        <div className="h-14 bg-white border-b border-neutral-200 flex items-center justify-between px-6">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-500"></div>
              <span className="text-sm text-neutral-600">Idle</span>
            </div>
            <div className="h-4 w-px bg-neutral-200"></div>
            <Link to="/jobs" className="text-sm text-neutral-600 hover:text-neutral-900">
              <span className="font-medium text-neutral-900">12</span> to review
            </Link>
            <div className="h-4 w-px bg-neutral-200"></div>
            <Link to="/jobs" className="text-sm text-neutral-600 hover:text-neutral-900">
              <span className="font-medium text-neutral-900">5</span> approved
            </Link>
          </div>
          <div className="text-sm text-neutral-500">
            Last run: 2 hours ago
          </div>
        </div>

        {/* Page content */}
        <div className="flex-1 overflow-auto">
          {children}
        </div>
      </div>
    </div>
  );
}
