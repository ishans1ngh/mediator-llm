const API_BASE = '/api';

async function apiFetch(path, options = {}) {
  const url = API_BASE + path;
  const res = await fetch(url, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

export const getPatients = () => apiFetch('/patients');
export const getPatient = (id) => apiFetch('/patients/' + id);
export const uploadMRI = (formData) => apiFetch('/mri/upload', { method: 'POST', body: formData });
export const analyzeMRI = (payload) => apiFetch('/mri/analyze', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
export const buildProfile = (payload) => apiFetch('/patient/profile', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
export const searchTrials = (payload) => apiFetch('/trials/search', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
export const matchTrial = (payload) => apiFetch('/trials/match', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
