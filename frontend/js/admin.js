// admin.js
// Handles fetching data for the Admin Dashboard

document.addEventListener('DOMContentLoaded', () => {
    initAdminDashboard();
});

const getToken = () => localStorage.getItem("gotrip_token");

// Re-use the global API from config.js if it exists, otherwise define it locally
const API = window.ELITE_API_URL ? window.ELITE_API_URL + "/api" : (() => {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return "http://localhost:10000/api";
  }
  return "https://travel-xyyl.onrender.com/api";
})();

async function initAdminDashboard() {
    const token = getToken();
    if (!token) {
        window.location.href = "index.html"; // Redirect to login
        return;
    }

    try {
        await Promise.all([
            fetchStats(token),
            fetchBookings(token)
        ]);
    } catch (err) {
        console.error("Admin dashboard init failed", err);
        alert("Failed to load admin data. Are you sure you're an Admin?");
    }
}

async function fetchStats(token) {
    const res = await fetch(`${API}/admin/stats?token=${encodeURIComponent(token)}`);
    if (!res.ok) throw new Error("Failed to fetch stats");
    const stats = await res.json();
    
    document.getElementById("stat-bookings").textContent = stats.totalBookings || 0;
    
    // We can show pending orders or something else here. For now, defaulting to 0.
    document.getElementById("stat-pending").textContent = stats.totalOrders || 0;
    
    document.getElementById("stat-revenue").textContent = `$${stats.estimatedRevenue || 0}`;
    document.getElementById("stat-customers").textContent = stats.totalUsers || 0;
}

async function fetchBookings(token) {
    const res = await fetch(`${API}/admin/bookings?token=${encodeURIComponent(token)}`);
    if (!res.ok) throw new Error("Failed to fetch bookings");
    const bookings = await res.json();
    
    const tableBody = document.getElementById("admin-bookings-table");
    tableBody.innerHTML = "";
    
    if (bookings.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="px-6 py-4 text-center text-gray-500">No bookings found.</td></tr>`;
        return;
    }

    bookings.forEach(b => {
        // Safe defaults if details are missing
        const details = b.details || {};
        const title = details.name || (details.from ? `${details.from} → ${details.to}` : null) || details.destination || "Booking";
        const date = details.departureDate || details.checkIn || details.pickupDate || details.date || "N/A";
        
        let statusBadge = "";
        if (b.status === "confirmed") {
            statusBadge = `<span class="px-2.5 py-1 rounded-md text-xs font-medium bg-green-100 text-green-700 border border-green-200">Confirmed</span>`;
        } else if (b.status === "cancelled") {
            statusBadge = `<span class="px-2.5 py-1 rounded-md text-xs font-medium bg-red-100 text-red-700 border border-red-200">Cancelled</span>`;
        } else {
            statusBadge = `<span class="px-2.5 py-1 rounded-md text-xs font-medium bg-yellow-100 text-yellow-700 border border-yellow-200">${b.status || 'Pending'}</span>`;
        }

        const rowHTML = `
            <tr class="admin-table-row">
              <td class="px-6 py-4 font-mono text-gray-500">#BK-${b._id ? b._id.substring(b._id.length - 4).toUpperCase() : '0000'}</td>
              <td class="px-6 py-4">${b.user_email || b.userEmail || 'Guest'}</td>
              <td class="px-6 py-4">${title}</td>
              <td class="px-6 py-4">${date}</td>
              <td class="px-6 py-4">${statusBadge}</td>
              <td class="px-6 py-4 text-right">
                <button class="text-gray-400 hover:text-red-600 mr-2" onclick="deleteBooking('${b._id}')" title="Delete Booking"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>
        `;
        tableBody.insertAdjacentHTML('beforeend', rowHTML);
    });
}

window.deleteBooking = function(id) {
    // Create custom confirmation modal overlay
    const overlay = document.createElement("div");
    overlay.className = "gt-overlay active";
    overlay.style.zIndex = "999999";
    
    // Add custom styling that matches the app
    overlay.innerHTML = `
      <div style="background: rgba(0,0,0,0.5); position: fixed; inset: 0; display: flex; align-items: center; justify-content: center;">
        <div style="background: white; padding: 24px; border-radius: 12px; max-width: 400px; width: 100%; box-shadow: 0 4px 20px rgba(0,0,0,0.2);">
          <h3 style="font-size: 18px; color: #1a2b6b; font-weight: bold; margin-bottom: 12px;">Delete Booking?</h3>
          <p style="font-size: 14px; color: #555; margin-bottom: 24px;">Are you sure you want to permanently delete this booking? This action cannot be undone.</p>
          <div style="display: flex; gap: 12px; justify-content: flex-end;">
            <button id="admin-delete-cancel" style="padding: 8px 16px; border-radius: 6px; background: #f3f4f6; color: #374151; font-weight: 500; cursor: pointer; border: none;">Cancel</button>
            <button id="admin-delete-confirm" style="padding: 8px 16px; border-radius: 6px; background: #ef4444; color: white; font-weight: 500; cursor: pointer; border: none;">Delete</button>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(overlay);

    document.getElementById("admin-delete-cancel").onclick = () => {
        document.body.removeChild(overlay);
    };

    document.getElementById("admin-delete-confirm").onclick = async () => {
        const btn = document.getElementById("admin-delete-confirm");
        btn.textContent = "Deleting...";
        btn.disabled = true;
        
        const token = getToken();
        try {
            const res = await fetch(`${API}/admin/bookings/${id}?token=${encodeURIComponent(token)}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                document.body.removeChild(overlay);
                showCustomAlert("Success", "Booking deleted successfully.", "success");
                fetchBookings(token); // reload table
            } else {
                throw new Error("Failed to delete booking.");
            }
        } catch (err) {
            console.error(err);
            document.body.removeChild(overlay);
            showCustomAlert("Error", "An error occurred while deleting the booking.", "error");
        }
    };
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
          <button id="admin-alert-ok" style="padding: 8px 24px; border-radius: 6px; background: #1a2b6b; color: white; font-weight: 500; cursor: pointer; border: none;">OK</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(overlay);
    document.getElementById("admin-alert-ok").onclick = () => {
        document.body.removeChild(overlay);
    };
}
