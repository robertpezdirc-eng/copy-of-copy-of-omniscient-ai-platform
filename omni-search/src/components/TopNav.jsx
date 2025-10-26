import DarkModeToggle from './DarkModeToggle';

export default function TopNav({ active, onChange }) {
  const items = [
    { key: 'status', label: 'Status' },
    { key: 'gemini', label: 'Gemini Stream' },
    { key: 'modules', label: 'Moduli' },
    { key: 'settings', label: 'Nastavitve' }
  ];

  return (
    <div className="w-full flex items-center justify-between px-4 py-3 border-b border-gray-800 bg-black/60 backdrop-blur dark:bg-white/60">
      <div className="flex items-center gap-2">
        <span className="font-black text-xl tracking-widest">
          <span className="text-neonBlue">O</span>
          <span className="text-neonPink">M</span>
          <span className="text-neonOrange">N</span>
          <span className="text-neonBlue">I</span>
        </span>
        <span className="text-xs font-mono text-gray-400">Unified Dashboard</span>
      </div>

      <nav className="flex items-center gap-2">
        {items.map(it => (
          <button
            key={it.key}
            onClick={() => onChange?.(it.key)}
            className={
              'px-3 py-1.5 rounded-md text-sm font-mono ' +
              (active === it.key ? 'bg-neonBlue text-black' : 'text-gray-300 hover:text-white hover:bg-gray-800')
            }
          >
            {it.label}
          </button>
        ))}
      </nav>

      <DarkModeToggle />
    </div>
  );
}