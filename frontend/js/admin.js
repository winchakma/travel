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

window.deleteBooking = async function(id) {
    if (!confirm("Are you sure you want to permanently delete this booking?")) return;
    
    const token = getToken();
    try {
        const res = await fetch(`${API}/admin/bookings/${id}?token=${encodeURIComponent(token)}`, {
            method: 'DELETE'
        });
        if (res.ok) {
            alert("Booking deleted.");
            fetchBookings(token); // reload table
        } else {
            alert("Failed to delete booking.");
        }
    } catch (err) {
        console.error(err);
        alert("An error occurred.");
    }
};
