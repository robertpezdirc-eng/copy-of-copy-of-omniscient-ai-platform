import { useEffect, useState } from 'react';

export default function DarkModeToggle() {
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('omni_dark_mode');
    if (saved === 'true') {
      setEnabled(true);
      document.documentElement.classList.add('dark');
    }
  }, []);

  const toggle = () => {
    const next = !enabled;
    setEnabled(next);
    localStorage.setItem('omni_dark_mode', String(next));
    document.documentElement.classList.toggle('dark', next);
  };

  return (
    <button
      onClick={toggle}
      className="px-3 py-2 rounded-md text-sm font-mono border border-gray-700 bg-gray-900 text-gray-200 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-900 dark:border-gray-300"
      title="Preklopi temni način"
    >
      {enabled ? '🌙 Dark' : '☀️ Light'}
    </button>
  );
}