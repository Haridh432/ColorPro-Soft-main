'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/Navbar';
import BatchCard from '@/components/BatchCard';
import api from '@/lib/api';

export default function Dashboard() {
  const router = useRouter();
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newBatch, setNewBatch] = useState({ name: '', description: '' });
  const [creating, setCreating] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    api.getMe().then(setUser).catch(() => setUser(null));
    loadBatches();
  }, []);

  async function loadBatches() {
    try {
      const data = await api.getBatches();
      setBatches(data.results || data);
    } catch (err) {
      console.error('Failed to load batches:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateBatch(e) {
    e.preventDefault();
    if (!newBatch.name.trim()) return;
    setCreating(true);
    try {
      await api.createBatch(newBatch.name, newBatch.description);
      setNewBatch({ name: '', description: '' });
      setShowCreate(false);
      await loadBatches();
    } catch (err) {
      alert('Failed to create batch: ' + err.message);
    } finally {
      setCreating(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-6 pt-24 pb-12">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">
              Dashboard
            </h1>
            <p className="text-slate-400 mt-1">Manage your fabric shade batches</p>
          </div>
          <button
            onClick={() => {
              if (!user) {
                router.push('/login');
                return;
              }
              setShowCreate(!showCreate);
            }}
            className="btn-primary"
          >
            {user ? '+ New Batch' : 'Login to Create Batch'}
          </button>
        </div>

        {/* Create Form */}
        {showCreate && (
          <div className="glass-card p-6 mb-8 animate-fade-in" style={{ cursor: 'default' }}>
            <h2 className="text-lg font-semibold text-white mb-4">Create New Batch</h2>
            <form onSubmit={handleCreateBatch} className="flex flex-col gap-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input
                  className="input-field"
                  placeholder="Batch name (e.g., Batch-2026-04-12)"
                  value={newBatch.name}
                  onChange={e => setNewBatch({ ...newBatch, name: e.target.value })}
                  autoFocus
                />
                <input
                  className="input-field"
                  placeholder="Description (optional)"
                  value={newBatch.description}
                  onChange={e => setNewBatch({ ...newBatch, description: e.target.value })}
                />
              </div>
              <div className="flex gap-3">
                <button type="submit" className="btn-primary" disabled={creating}>
                  {creating ? 'Creating...' : 'Create Batch'}
                </button>
                <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Batch Grid */}
        {loading ? (
          <div className="text-center py-20">
            <div className="text-slate-500 text-lg">Loading batches...</div>
          </div>
        ) : batches.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">📦</div>
            <h2 className="text-xl font-semibold text-slate-300 mb-2">No batches yet</h2>
            <p className="text-slate-500">Create your first batch to get started</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {batches.map((batch, index) => (
              <BatchCard key={batch.id} batch={batch} index={index} />
            ))}
          </div>
        )}
      </main>
    </>
  );
}
