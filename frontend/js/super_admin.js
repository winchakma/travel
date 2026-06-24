// super_admin.js
// Handles fetching data and operations for the Super Admin Dashboard

document.addEventListener('DOMContentLoaded', () => {
    initSuperAdminDashboard();
});

const getToken = () => localStorage.getItem("gotrip_token");

const API = window.ELITE_API_URL ? window.ELITE_API_URL + "/api" : (() => {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return "http://localhost:10000/api";
  }
  return "https://travel-xyyl.onrender.com/api";
})();

async function initSuperAdminDashboard() {
    const token = getToken();
    if (!token) {
        window.location.href = "index.html";
        return;
    }

    try {
        await Promise.all([
            fetchStats(token),
            fetchAdmins(token)
        ]);
    } catch (err) {
        console.error("Super Admin dashboard init failed", err);
        alert("Failed to load super admin data. Are you sure you are authorized?");
    }
}

async function fetchStats(token) {
    const res = await fetch(`${API}/admin/stats?token=${encodeURIComponent(token)}`);
    if (!res.ok) throw new Error("Failed to fetch stats");
    const stats = await res.json();
    
    document.getElementById("super-stat-bookings").textContent = stats.totalBookings || 0;
    document.getElementById("super-stat-revenue").textContent = `$${(stats.estimatedRevenue || 0).toLocaleString()}`;
    document.getElementById("super-stat-users").textContent = (stats.totalUsers || 0).toLocaleString();
}

async function fetchAdmins(token) {
    const res = await fetch(`${API}/admin/users?token=${encodeURIComponent(token)}`);
    if (!res.ok) throw new Error("Failed to fetch users");
    const users = await res.json();
    
    // Filter to show only admins & super admins
    const admins = users.filter(u => u.role === 'admin' || u.role === 'super_admin');
    
    // Update active admins stat count
    const statAdmins = document.getElementById("super-stat-admins");
    if (statAdmins) {
        statAdmins.textContent = admins.length;
    }

    const tableBody = document.getElementById("super-admin-table");
    if (!tableBody) return;
    tableBody.innerHTML = "";
    
    if (admins.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="px-6 py-4 text-center text-gray-500">No admins found.</td></tr>`;
        return;
    }

    admins.forEach(u => {
        const roleLabel = u.role === 'super_admin' ? 'Super Admin' : 'Admin';
        const roleBadge = u.role === 'super_admin'
            ? `<span class="px-2.5 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700 border border-purple-200">Super Admin</span>`
            : `<span class="px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 border border-blue-200">Admin</span>`;
            
        // Super Admin cannot demote themselves or other super admins from this panel
        const actionBtn = u.role === 'super_admin'
            ? `<button disabled class="text-gray-300 cursor-not-allowed mr-3" title="Cannot modify Super Admin"><i class="fa-solid fa-ban"></i></button>`
            : `<button class="text-red-600 hover:text-red-800" onclick="demoteUser('${u.email}')" title="Revoke Admin Access"><i class="fa-solid fa-ban"></i></button>`;

        const rowHTML = `
            <tr class="admin-table-row">
              <td class="px-6 py-4 flex items-center gap-3">
                <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(u.firstName || 'A')}+${encodeURIComponent(u.lastName || '')}&background=random" class="w-8 h-8 rounded-full" />
                <span class="font-medium">${u.firstName || ''} ${u.lastName || ''}</span>
              </td>
              <td class="px-6 py-4">${u.email}</td>
              <td class="px-6 py-4">${roleLabel}</td>
              <td class="px-6 py-4">${roleBadge}</td>
              <td class="px-6 py-4">Active</td>
              <td class="px-6 py-4 text-right">
                ${actionBtn}
              </td>
            </tr>
        `;
        tableBody.insertAdjacentHTML('beforeend', rowHTML);
    });
}

window.demoteUser = function(email) {
    const overlay = document.createElement("div");
    overlay.className = "gt-overlay active";
    overlay.style.zIndex = "999999";
    
    overlay.innerHTML = `
      <div style="background: rgba(0,0,0,0.5); position: fixed; inset: 0; display: flex; align-items: center; justify-content: center;">
        <div style="background: white; padding: 24px; border-radius: 12px; max-width: 400px; width: 100%; box-shadow: 0 4px 20px rgba(0,0,0,0.2);">
          <h3 style="font-size: 18px; color: #1a2b6b; font-weight: bold; margin-bottom: 12px;">Revoke Admin Privileges?</h3>
          <p style="font-size: 14px; color: #555; margin-bottom: 24px;">Are you sure you want to revoke Admin rights for <strong>${email}</strong>? They will be demoted back to a standard Member.</p>
          <div style="display: flex; gap: 12px; justify-content: flex-end;">
            <button id="super-demote-cancel" style="padding: 8px 16px; border-radius: 6px; background: #f3f4f6; color: #374151; font-weight: 500; cursor: pointer; border: none;">Cancel</button>
            <button id="super-demote-confirm" style="padding: 8px 16px; border-radius: 6px; background: #ef4444; color: white; font-weight: 500; cursor: pointer; border: none;">Revoke</button>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(overlay);

    document.getElementById("super-demote-cancel").onclick = () => {
        document.body.removeChild(overlay);
    };

    document.getElementById("super-demote-confirm").onclick = async () => {
        const btn = document.getElementById("super-demote-confirm");
        btn.textContent = "Revoking...";
        btn.disabled = true;
        
        const token = getToken();
        try {
            const res = await fetch(`${API}/admin/demote?email=${encodeURIComponent(email)}&token=${encodeURIComponent(token)}`, {
                method: 'POST'
            });
            if (res.ok) {
                document.body.removeChild(overlay);
                showCustomAlert("Success", `${email} has been demoted to standard Member.`, "success");
                fetchStats(token);
                fetchAdmins(token);
            } else {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || "Failed to demote user.");
            }
        } catch (err) {
            console.error(err);
            document.body.removeChild(overlay);
            showCustomAlert("Error", err.message, "error");
        }
    };
};

window.addAdminManually = function() {
    const overlay = document.createElement("div");
    overlay.className = "gt-overlay active";
    overlay.style.zIndex = "999999";
    
    overlay.innerHTML = `
      <div style="background: rgba(0,0,0,0.5); position: fixed; inset: 0; display: flex; align-items: center; justify-content: center;">
        <div style="background: white; padding: 24px; border-radius: 12px; max-width: 400px; width: 100%; box-shadow: 0 4px 20px rgba(0,0,0,0.2);">
          <h3 style="font-size: 18px; color: #1a2b6b; font-weight: bold; margin-bottom: 12px;">Add New Admin</h3>
          <p style="font-size: 14px; color: #555; margin-bottom: 16px;">Enter the exact email address of the user you want to grant Admin privileges to:</p>
          <input type="email" id="super-admin-email" class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:border-[#1a2b6b]" style="width: 100%; margin-bottom: 20px;" placeholder="user@example.com" />
          <div style="display: flex; gap: 12px; justify-content: flex-end;">
            <button id="super-add-cancel" style="padding: 8px 16px; border-radius: 6px; background: #f3f4f6; color: #374151; font-weight: 500; cursor: pointer; border: none;">Cancel</button>
            <button id="super-add-confirm" style="padding: 8px 16px; border-radius: 6px; background: #1a2b6b; color: white; font-weight: 500; cursor: pointer; border: none;">Grant Access</button>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(overlay);
    setTimeout(() => {
        const input = document.getElementById("super-admin-email");
        if (input) input.focus();
    }, 100);

    document.getElementById("super-add-cancel").onclick = () => {
        document.body.removeChild(overlay);
    };

    document.getElementById("super-add-confirm").onclick = async () => {
        const emailInput = document.getElementById("super-admin-email").value.trim();
        if (!emailInput) {
            alert("Please enter an email address.");
            return;
        }

        const btn = document.getElementById("super-add-confirm");
        btn.textContent = "Processing...";
        btn.disabled = true;
        
        const token = getToken();
        try {
            const res = await fetch(`${API}/admin/promote?email=${encodeURIComponent(emailInput)}&token=${encodeURIComponent(token)}`, {
                method: 'POST'
            });
            if (res.ok) {
                document.body.removeChild(overlay);
                showCustomAlert("Success", `${emailInput} promoted to Admin.`, "success");
                fetchStats(token);
                fetchAdmins(token);
            } else {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || "Failed to find or promote user.");
            }
        } catch (err) {
            console.error(err);
            document.body.removeChild(overlay);
            showCustomAlert("Error", err.message, "error");
        }
    };
};

window.logout = function(event) {
    if (event) event.preventDefault();
    localStorage.removeItem("gotrip_token");
    localStorage.removeItem("gotrip_user");
    window.location.href = "index.html";
};

function showCustomAlert(title, message, type) {
    const overlay = document.createElement("div");
    overlay.className = "gt-overlay active";
    overlay.style.zIndex = "999999";
    
    const color = type === 'error' ? '#ef4444' : '#10b981';
    
    overlay.innerHTML = `
      <div style="background: rgba(0,0,0,0.5); position: fixed; inset: 0; display: flex; align-items: center; justify-content: center;">
        <div style="background: white; padding: 24px; border-radius: 12px; max-width: 400px; width: 100%; box-shadow: 0 4px 20px rgba(0,0,0,0.2); text-align: center;">
          <h3 style="font-size: 20px; color: ${color}; font-weight: bold; margin-bottom: 12px;">${title}</h3>
          <p style="font-size: 15px; color: #555; margin-bottom: 24px;">${message}</p>
          <button id="super-alert-ok" style="padding: 8px 24px; border-radius: 6px; background: #1a2b6b; color: white; font-weight: 500; cursor: pointer; border: none;">OK</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(overlay);
    document.getElementById("super-alert-ok").onclick = () => {
        document.body.removeChild(overlay);
    };
}
