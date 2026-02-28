/* ══════════════════════════════════════
   SmartGov — Frontend Application Core
   API Client, Auth, Toast, Utilities
   ══════════════════════════════════════ */

const API_BASE = '/api';

// ── Auth Manager ──
const Auth = {
  getToken: () => localStorage.getItem('smartgov_token'),
  getUser: () => JSON.parse(localStorage.getItem('smartgov_user') || 'null'),
  setSession: (token, user) => {
    localStorage.setItem('smartgov_token', token);
    localStorage.setItem('smartgov_user', JSON.stringify(user));
  },
  clear: () => {
    localStorage.removeItem('smartgov_token');
    localStorage.removeItem('smartgov_user');
  },
  isLoggedIn: () => !!localStorage.getItem('smartgov_token'),
  requireAuth: (allowedRoles = []) => {
    const user = Auth.getUser();
    if (!user) { window.location.href = '/login.html'; return null; }
    if (allowedRoles.length && !allowedRoles.includes(user.role)) {
      window.location.href = '/login.html';
      return null;
    }
    return user;
  },
  logout: () => {
    Auth.clear();
    window.location.href = '/login.html';
  }
};

// ── API Client ──
const api = {
  async request(method, endpoint, body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const token = Auth.getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${API_BASE}${endpoint}`, opts);
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Something went wrong');
    }
    return data;
  },
  get: (ep) => api.request('GET', ep),
  post: (ep, body) => api.request('POST', ep, body),
  put: (ep, body) => api.request('PUT', ep, body),
  delete: (ep) => api.request('DELETE', ep),
};

// ── Toast Notifications ──
const Toast = {
  container: null,
  init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }
  },
  show(message, type = 'info') {
    this.init();
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
    this.container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  },
  success: (msg) => Toast.show(msg, 'success'),
  error: (msg) => Toast.show(msg, 'error'),
  warning: (msg) => Toast.show(msg, 'warning'),
  info: (msg) => Toast.show(msg, 'info'),
};

// ── Utility Functions ──
function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatDateTime(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now - d) / 1000);
  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return formatDate(dateStr);
}

function getStatusBadge(status) {
  const s = status.toLowerCase().replace(/\s+/g, '-');
  const icons = {
    'submitted': '📝', 'acknowledged': '👁️', 'in-progress': '🔧',
    'resolved': '✅', 'closed': '🔒', 'rejected': '❌'
  };
  return `<span class="badge badge-${s}">${icons[s] || ''} ${status}</span>`;
}

function getPriorityBadge(priority) {
  return `<span class="badge badge-${priority.toLowerCase()}">${priority}</span>`;
}

function getRoleBadge(role) {
  return `<span class="badge badge-${role}">${role.charAt(0).toUpperCase() + role.slice(1)}</span>`;
}

function getCategoryIcon(category) {
  const icons = { 'Water': '💧', 'Electricity': '⚡', 'Sanitation': '🗑️', 'Infrastructure': '🏗️', 'Other': '📋' };
  return icons[category] || '📋';
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ── Navbar Builder ──
function buildNavbar(user) {
  const links = {
    citizen: [
      { href: '/citizen/dashboard.html', label: '📊 Dashboard', id: 'nav-dashboard' },
      { href: '/citizen/submit.html', label: '➕ New Complaint', id: 'nav-submit' },
      { href: '/citizen/my-complaints.html', label: '📋 My Complaints', id: 'nav-complaints' },
    ],
    staff: [
      { href: '/staff/dashboard.html', label: '📊 Dashboard', id: 'nav-dashboard' },
    ],
    admin: [
      { href: '/admin/dashboard.html', label: '📊 Dashboard', id: 'nav-dashboard' },
      { href: '/admin/complaints.html', label: '📋 Complaints', id: 'nav-complaints' },
      { href: '/admin/users.html', label: '👥 Users', id: 'nav-users' },
    ]
  };

  const navLinks = links[user.role] || [];
  const currentPath = window.location.pathname;
  const initials = user.full_name.split(' ').map(n => n[0]).join('').toUpperCase();

  return `
    <nav class="navbar">
      <div class="container">
        <a href="/" class="navbar-brand">
          <div class="logo-icon">🏛️</div>
          <span>SmartGov</span>
        </a>
        <div class="navbar-links">
          ${navLinks.map(l => `<a href="${l.href}" id="${l.id}" class="${currentPath === l.href ? 'active' : ''}">${l.label}</a>`).join('')}
          <button class="notification-badge" onclick="toggleNotifications()" id="notif-btn">
            🔔 <span class="badge" id="notif-count" style="display:none;">0</span>
          </button>
          <div class="user-menu">
            <div class="user-avatar">${initials}</div>
            <div class="user-info">
              <span class="name">${escapeHtml(user.full_name)}</span>
              <span class="role">${user.role}${user.department ? ' · ' + user.department : ''}</span>
            </div>
          </div>
          <button onclick="Auth.logout()" class="btn btn-ghost btn-sm">Logout</button>
        </div>
      </div>
    </nav>
    <div class="notification-panel" id="notif-panel">
      <div class="panel-header">
        <h3>🔔 Notifications</h3>
        <button class="btn btn-sm btn-ghost" onclick="markAllRead()">Mark all read</button>
      </div>
      <div id="notif-list"></div>
    </div>
  `;
}

// ── Notification Functions ──
let notifPanelOpen = false;

function toggleNotifications() {
  const panel = document.getElementById('notif-panel');
  notifPanelOpen = !notifPanelOpen;
  panel.classList.toggle('open', notifPanelOpen);
  if (notifPanelOpen) loadNotifications();
}

async function loadNotifications() {
  try {
    const data = await api.get('/notifications');
    const countEl = document.getElementById('notif-count');
    if (data.unread_count > 0) {
      countEl.textContent = data.unread_count;
      countEl.style.display = 'flex';
    } else {
      countEl.style.display = 'none';
    }
    const list = document.getElementById('notif-list');
    if (!data.notifications.length) {
      list.innerHTML = '<div class="empty-state"><p>No notifications yet</p></div>';
      return;
    }
    list.innerHTML = data.notifications.map(n => `
      <div class="notification-item ${n.is_read ? '' : 'unread'}" onclick="markRead(${n.id})">
        <div class="notif-message">${escapeHtml(n.message)}</div>
        <div class="notif-time">${timeAgo(n.created_at)}</div>
      </div>
    `).join('');
  } catch (e) { console.error('Failed to load notifications:', e); }
}

async function markRead(id) {
  try { await api.put(`/notifications/${id}/read`); loadNotifications(); } catch (e) {}
}

async function markAllRead() {
  try { await api.put('/notifications/read-all'); loadNotifications(); Toast.success('All notifications marked as read'); } catch (e) {}
}

// ── Init Notification Polling ──
function initNotifications() {
  loadNotifications();
  setInterval(loadNotifications, 30000);
}

// ── Stars Rating Component ──
function createStarRating(containerId, initialRating = 0, onChange = null) {
  const container = document.getElementById(containerId);
  if (!container) return;
  let rating = initialRating;
  function render() {
    container.innerHTML = '';
    for (let i = 1; i <= 5; i++) {
      const star = document.createElement('span');
      star.className = `star ${i <= rating ? 'active' : ''}`;
      star.textContent = '★';
      star.onclick = () => {
        rating = i;
        render();
        if (onChange) onChange(i);
      };
      container.appendChild(star);
    }
  }
  render();
  return { getValue: () => rating };
}

function renderStars(rating) {
  let html = '';
  for (let i = 1; i <= 5; i++) {
    html += `<span style="color:${i <= rating ? 'var(--warning)' : 'var(--border)'}">★</span>`;
  }
  return html;
}
