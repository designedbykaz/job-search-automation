import { BrowserRouter, Routes, Route } from 'react-router';
import { Layout } from './components/Layout';
import { Dashboard } from './components/Dashboard';
import { Run } from './components/Run';
import { Jobs } from './components/Jobs';
import { Content } from './components/Content';
import { Prompts } from './components/Prompts';
import { Templates } from './components/Templates';
import { Settings } from './components/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/run" element={<Run />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/content" element={<Content />} />
          <Route path="/prompts" element={<Prompts />} />
          <Route path="/templates" element={<Templates />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}