'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import api from '@/lib/api';

export default function Navbar() {
  const pathname = usePathname();
  const [user, setUser] = useState(null);
  const [deviceStatus, setDeviceStatus] = useState(null);

  useEffect(() => {
    api.getMe().then(setUser).catch(() => setUser(null));
  }, [pathname]); // Refresh user state on navigation

  useEffect(() => {
    // Poll device status every 5 seconds
    const fetchStatus = () => {
      api.getDeviceStatus().then(setDeviceStatus).catch(() => setDeviceStatus(null));
    };
    fetchStatus();
    const inv = setInterval(fetchStatus, 5000);
    return () => clearInterval(inv);
  }, []);

  const links = [
    { href: '/', label: 'Dashboard', icon: '📊' },
    { href: '/compare', label: 'Compare', icon: '🔬' },
  ];

  function handleLogout() {
    api.clearToken();
    window.location.href = '/login';
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[var(--border-subtle)]"
         style={{ background: 'rgba(10, 14, 26, 0.85)', backdropFilter: 'blur(20px)' }}>
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center text-white font-bold text-sm"
               style={{ background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' }}>
            CP
          </div>
          <span className="text-lg font-bold tracking-wide text-white group-hover:text-blue-400 transition-colors">
            ColorPro
          </span>
        </Link>

        {/* Nav Links */}
        <div className="flex items-center gap-1">
          {links.map(link => (
            <Link
              key={link.href}
              href={link.href}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                pathname === link.href
                  ? 'bg-blue-500/15 text-blue-400'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <span className="mr-2">{link.icon}</span>
              {link.label}
            </Link>
          ))}

          {/* Device Sensor Status */}
          <div className="ml-4 flex items-center gap-2">
            <div className="flex h-3 w-3 relative">
              {deviceStatus?.online && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              )}
              <span className={`relative inline-flex rounded-full h-3 w-3 ${deviceStatus?.online ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
            </div>
            <span className="text-xs font-semibold text-slate-300">
              Sensor {deviceStatus?.online ? 'Online' : 'Offline'}
            </span>
          </div>

          {/* Auth Button */}
          <div className="ml-4 pl-4 border-l border-[var(--border-subtle)] flex items-center gap-3">
            {user ? (
              <>
                <span className="text-sm text-slate-300">@{user.username}</span>
                <button onClick={handleLogout} className="text-sm text-red-400 hover:text-red-300 transition-colors">
                  Logout
                </button>
              </>
            ) : (
              <Link href="/login" className="text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors">
                Sign In
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
