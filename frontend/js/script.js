// ============================================================
//  GoTrip — Frontend ↔ Backend connector v2
//  Place at: /js/script.js
// ============================================================

// Auto-detect API URL - works on localhost and production!
const API = (() => {
  if (window.ELITE_API_URL) return window.ELITE_API_URL + "/api";
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return "http://localhost:10000/api";
  }
  return "https://travel-xyyl.onrender.com/api";
})();

const getToken = () => localStorage.getItem("gotrip_token");
const getUser  = () => JSON.parse(localStorage.getItem("gotrip_user") || "null");
const saveAuth = (token, user) => {
  localStorage.setItem("gotrip_token", token);
  localStorage.setItem("gotrip_user", JSON.stringify(user));
};
const clearAuth = () => {
  localStorage.removeItem("gotrip_token");
  localStorage.removeItem("gotrip_user");
};
const isLoggedIn = () => !!getToken();

function getPageType() {
  const path = window.location.pathname;
  if (path.includes("flights")) return "flight";
  if (path.includes("hotel"))   return "hotel";
  if (path.includes("car"))     return "car";
  if (path.includes("cruise"))  return "cruise";
  if (path.includes("tour"))    return "tour";
  if (path.includes("rental"))  return "rental";
  return "activity";
}

function injectModals() {
  if (document.getElementById("gotrip-modals")) return;
  const wrapper = document.createElement("div");
  wrapper.id = "gotrip-modals";
  wrapper.innerHTML = `
    <style>
      .gt-overlay {
        display:none; position:fixed; inset:0;
        background:rgba(0,0,0,0.6); z-index:9999;
        align-items:center; justify-content:center;
        padding:20px; box-sizing:border-box;
      }
      .gt-overlay.active { display:flex; }
      .gt-modal {
        background:#fff; border-radius:16px; width:100%;
        max-width:460px; position:relative;
        box-shadow:0 20px 60px rgba(0,0,0,0.25);
        animation: gtSlideUp 0.25s ease;
        max-height:90vh; overflow-y:auto;
      }
      .gt-modal-wide { max-width:700px; }
      @keyframes gtSlideUp {
        from { opacity:0; transform:translateY(30px); }
        to   { opacity:1; transform:translateY(0); }
      }
      .gt-modal-head {
        padding:22px 25px 0;
        display:flex; justify-content:space-between; align-items:center;
      }
      .gt-modal-head h2 { color:#1a2b6b; font-size:20px; margin:0; }
      .gt-close {
        background:none; border:none; font-size:22px;
        cursor:pointer; color:#999; line-height:1; padding:0;
      }
      .gt-modal-body { padding:20px 25px 25px; }
      .gt-input {
        width:100%; padding:11px 14px; border:1px solid #dde1eb;
        border-radius:8px; font-size:14px; outline:none;
        margin-bottom:12px; box-sizing:border-box; font-family:inherit;
        transition:border 0.2s;
      }
      .gt-input:focus { border-color:#1a2b6b; }
      .gt-btn {
        width:100%; background:#1a2b6b; color:#fff; border:none;
        padding:13px; border-radius:8px; font-size:15px;
        font-weight:600; cursor:pointer; margin-top:4px; transition:background 0.2s;
      }
      .gt-btn:hover { background:#243d8f; }
      .gt-btn-outline {
        width:100%; background:#fff; color:#1a2b6b; border:2px solid #1a2b6b;
        padding:11px; border-radius:8px; font-size:14px;
        font-weight:600; cursor:pointer; margin-top:8px;
      }
      .gt-error {
        color:#e53e3e; font-size:13px; margin-bottom:10px; display:none;
        background:#fff5f5; padding:8px 12px; border-radius:6px;
        border-left:3px solid #e53e3e;
      }
      .gt-tabs {
        display:flex; gap:0; margin-bottom:20px; border-bottom:2px solid #eee;
      }
      .gt-tab {
        flex:1; background:none; border:none; padding:10px;
        font-size:14px; cursor:pointer; color:#888;
        border-bottom:2px solid transparent; margin-bottom:-2px; font-family:inherit;
      }
      .gt-tab.active { color:#1a2b6b; font-weight:700; border-bottom-color:#1a2b6b; }
      .gt-detail-img {
        width:100%; height:230px; object-fit:cover; border-radius:12px 12px 0 0;
      }
      .gt-detail-grid {
        display:grid; grid-template-columns:1fr 1fr; gap:12px; margin:16px 0;
      }
      .gt-detail-field label {
        display:block; font-size:11px; color:#888;
        text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;
      }
      .gt-price-box {
        background:#f0f4ff; border-radius:10px; padding:16px; margin:16px 0;
        display:flex; justify-content:space-between; align-items:center;
      }
      .gt-price-box .big-price { font-size:28px; font-weight:700; color:#1a2b6b; }
      .gt-badge-type {
        background:#1a2b6b; color:#fff; font-size:11px;
        padding:4px 10px; border-radius:20px; text-transform:uppercase; letter-spacing:0.5px;
      }
      .gt-booking-card {
        border:1px solid #e8ecf4; border-radius:12px;
        padding:16px; margin-bottom:12px; transition:box-shadow 0.2s;
      }
      .gt-booking-card:hover { box-shadow:0 4px 15px rgba(0,0,0,0.08); }
      .gt-booking-top {
        display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;
      }
      .gt-booking-title { font-size:15px; font-weight:600; color:#1a2b6b; }
      .gt-booking-sub { font-size:13px; color:#888; margin-top:3px; }
      .gt-status { font-size:11px; padding:4px 10px; border-radius:20px; font-weight:600; }
      .gt-status.confirmed { background:#d1fae5; color:#065f46; }
      .gt-status.cancelled { background:#fee2e2; color:#991b1b; }
      .gt-status.pending   { background:#fef3c7; color:#92400e; }
      .gt-booking-details {
        display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px;
        margin-top:10px; padding-top:10px; border-top:1px solid #f0f0f0;
      }
      .gt-booking-detail-item { font-size:12px; color:#333; }
      .gt-booking-detail-item span { display:block; color:#888; font-size:11px; margin-bottom:2px; }
      .gt-cancel-btn {
        margin-top:10px; background:none; border:1px solid #e53e3e;
        color:#e53e3e; padding:6px 14px; border-radius:6px;
        font-size:12px; cursor:pointer; font-family:inherit; transition:all 0.2s;
      }
      .gt-cancel-btn:hover { background:#e53e3e; color:#fff; }
      #gt-toast {
        position:fixed; bottom:28px; left:50%; transform:translateX(-50%);
        padding:13px 24px; border-radius:10px; font-size:14px;
        font-family:'Segoe UI',sans-serif; z-index:99999; max-width:380px;
        text-align:center; box-shadow:0 4px 20px rgba(0,0,0,0.2);
        animation: gtToastIn 0.3s ease;
      }
      @keyframes gtToastIn {
        from { opacity:0; transform:translateX(-50%) translateY(10px); }
        to   { opacity:1; transform:translateX(-50%) translateY(0); }
      }
    </style>

    <!-- AUTH MODAL -->
    <div class="gt-overlay" id="gt-auth-overlay">
      <div class="gt-modal">
        <div class="gt-modal-head">
          <h2 id="gt-auth-title">Welcome back!</h2>
          <button class="gt-close" onclick="closeModal('gt-auth-overlay')">✕</button>
        </div>
        <div class="gt-modal-body">
          <div class="gt-tabs">
            <button class="gt-tab active" id="tab-signin" onclick="switchTab('signin')">Sign In</button>
            <button class="gt-tab" id="tab-register" onclick="switchTab('register')">Register</button>
          </div>
          <div id="gt-signin-form">
            <input class="gt-input" id="si-email" type="email" placeholder="Email address" />
            <input class="gt-input" id="si-password" type="password" placeholder="Password" />
            <div class="gt-error" id="si-error"></div>
            <button class="gt-btn" id="si-btn" onclick="handleLogin()">Sign In</button>
          </div>
          <div id="gt-register-form" style="display:none;">
            <input class="gt-input" id="reg-name" type="text" placeholder="Full name" />
            <input class="gt-input" id="reg-email" type="email" placeholder="Email address" />
            <input class="gt-input" id="reg-password" type="password" placeholder="Password (min 6 chars)" />
            <div class="gt-error" id="reg-error"></div>
            <button class="gt-btn" id="reg-btn" onclick="handleRegister()">Create Account</button>
          </div>
        </div>
      </div>
    </div>

    <!-- BOOKING DETAIL MODAL -->
    <div class="gt-overlay" id="gt-detail-overlay">
      <div class="gt-modal gt-modal-wide">
        <button class="gt-close" style="position:absolute;top:14px;right:14px;z-index:2;background:rgba(255,255,255,0.9);border-radius:50%;width:34px;height:34px;display:flex;align-items:center;justify-content:center;" onclick="closeModal('gt-detail-overlay')">✕</button>
        <div id="gt-detail-content"></div>
      </div>
    </div>

    <!-- MY BOOKINGS MODAL -->
    <div class="gt-overlay" id="gt-bookings-overlay">
      <div class="gt-modal" style="max-width:600px;">
        <div class="gt-modal-head">
          <h2>My Bookings</h2>
          <button class="gt-close" onclick="closeModal('gt-bookings-overlay')">✕</button>
        </div>
        <div class="gt-modal-body">
          <div id="gt-bookings-list"></div>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(wrapper);
  ["gt-auth-overlay","gt-detail-overlay","gt-bookings-overlay"].forEach(id => {
    document.getElementById(id).addEventListener("click", function(e) {
      if (e.target === this) closeModal(id);
    });
  });
}

function openModal(id)  { document.getElementById(id).classList.add("active"); }
function closeModal(id) { document.getElementById(id).classList.remove("active"); }

function switchTab(tab) {
  document.getElementById("gt-signin-form").style.display   = tab === "signin"   ? "block" : "none";
  document.getElementById("gt-register-form").style.display = tab === "register" ? "block" : "none";
  document.getElementById("tab-signin").classList.toggle("active",   tab === "signin");
  document.getElementById("tab-register").classList.toggle("active", tab === "register");
  document.getElementById("gt-auth-title").textContent = tab === "signin" ? "Welcome back!" : "Create account";
  ["si-error","reg-error"].forEach(id => {
    const el = document.getElementById(id);
    if (el) { el.style.display="none"; el.textContent=""; }
  });
}

function showError(id, msg) {
  const el = document.getElementById(id);
  if (el) { 
    el.textContent = msg; 
    el.style.display = "block";
    // Auto-hide after 5 seconds (cool feature!)
    setTimeout(() => {
      el.style.display = "none";
    }, 5000);
  }
}

// Helper function to validate email (looks like hacking but it's just pattern matching!)
function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

async function handleLogin() {
  const email = document.getElementById("si-email").value.trim();
  const password = document.getElementById("si-password").value;
  if (!email || !password) return showError("si-error","Please fill in all fields.");
  if (!validateEmail(email)) return showError("si-error","Please enter a valid email address.");
  
  const btn = document.getElementById("si-btn");
  const originalText = btn.textContent;
  btn.textContent = "Signing in…"; 
  btn.disabled = true;
  btn.style.opacity = "0.6"; // Visual feedback!
  
  try {
    const res = await fetch(`${API}/auth/login`, {
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) {
      let errorMsg = data.error || "Login failed.";
      if (data.detail && Array.isArray(data.detail)) {
        errorMsg = data.detail[0].msg;
      } else if (data.detail) {
        errorMsg = data.detail;
      }
      showError("si-error", errorMsg);
    } else { 
      saveAuth(data.token, data.user); 
      closeModal("gt-auth-overlay"); 
      updateNavbar(); 
      showToast(`Welcome back, ${data.user.name}! 👋`); 
    }
  } catch (err) {
    showError("si-error","Cannot reach server. Make sure your backend is running!");
  }
  finally { 
    btn.textContent = originalText; 
    btn.disabled = false;
    btn.style.opacity = "1";
  }
}

async function handleRegister() {
  const name = document.getElementById("reg-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;
  if (!name || !email || !password) return showError("reg-error","Please fill in all fields.");
  if (!validateEmail(email)) return showError("reg-error","Please enter a valid email address.");
  if (password.length < 6) return showError("reg-error","Password must be at least 6 characters.");
  
  const btn = document.getElementById("reg-btn");
  const originalText = btn.textContent;
  btn.textContent = "Creating account…"; 
  btn.disabled = true;
  btn.style.opacity = "0.6"; // Visual feedback!
  
  try {
    const nameParts = name.trim().split(" ");
    const firstName = nameParts[0] || "User";
    const lastName = nameParts.slice(1).join(" ") || "Name";

    const res = await fetch(`${API}/auth/register`, {
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({ firstName, lastName, email, password }),
    });
    const data = await res.json();
    if (!res.ok) {
      let errorMsg = data.error || "Registration failed.";
      if (data.detail && Array.isArray(data.detail)) {
        errorMsg = data.detail[0].msg.replace("Value error, ", "");
      } else if (data.detail) {
        errorMsg = data.detail;
      }
      showError("reg-error", errorMsg);
    } else { 
      saveAuth(data.token, data.user); 
      closeModal("gt-auth-overlay"); 
      updateNavbar(); 
      showToast(`Account created! Welcome, ${data.user.name || firstName}! 🎉`); 
    }
  } catch (err) { 
    showError("reg-error","Cannot reach server. Make sure your backend is running!");
  }
  finally { 
    btn.textContent = originalText; 
    btn.disabled = false;
    btn.style.opacity = "1";
  }
}

function logout() { 
  clearAuth(); 
  updateNavbar(); 
  showToast("Signed out. See you soon!"); 
  setTimeout(() => {
    window.location.href = "index.html";
  }, 1000);
}

function updateNavbar() {
  const navButtons = document.querySelector(".nav-buttons");
  if (!navButtons) return;
  if (isLoggedIn()) {
    const user = getUser();
    const displayName = user.firstName || "User";
    const profileIcon = user.profilePicture ? `<img src="${user.profilePicture}" alt="Profile" style="width:24px;height:24px;border-radius:50%;object-fit:cover;">` : `👤`;
    
    const adminButton = (user.role === 'admin' || user.role === 'super_admin') 
      ? `<button class="btn-login" style="background:#e5c414;color:#1a2b6b;" onclick="window.location.href='admin.html'">Admin Panel</button>`
      : '';

    navButtons.innerHTML = `
      <a href="profile.html" style="font-size:14px;color:#1a2b6b;font-weight:600;text-decoration:none;display:flex;align-items:center;gap:6px;cursor:pointer;">
        ${profileIcon} <span style="border-bottom:1px solid transparent;transition:border 0.2s;" onmouseover="this.style.borderBottom='1px solid #1a2b6b'" onmouseout="this.style.borderBottom='1px solid transparent'">${displayName}</span>
      </a>
      ${adminButton}
      <button class="btn-register" onclick="window.location.href='profile.html#bookings'">My Bookings</button>
      <button class="btn-login" onclick="logout()">Sign Out</button>
    `;
  } else {
    navButtons.innerHTML = `
      <button class="btn-login" onclick="openModal('gt-auth-overlay');switchTab('signin')">Sign In</button>
      <button class="btn-register" onclick="openModal('gt-auth-overlay');switchTab('register')">Register</button>
    `;
  }
}

function buildFields(type, info) {
  if (type === "flight") return `
    <div class="gt-detail-field"><label>From</label>
      <input class="gt-input" id="bd-from" placeholder="Departure city" value="${info.from||''}" /></div>
    <div class="gt-detail-field"><label>To</label>
      <input class="gt-input" id="bd-to" placeholder="Arrival city" value="${info.to||''}" /></div>
    <div class="gt-detail-field"><label>Departure Date</label>
      <input class="gt-input" id="bd-dep" type="date" /></div>
    <div class="gt-detail-field"><label>Return Date</label>
      <input class="gt-input" id="bd-ret" type="date" /></div>
    <div class="gt-detail-field"><label>Passengers</label>
      <select class="gt-input" id="bd-guests"><option>1 Passenger</option><option>2 Passengers</option><option>3 Passengers</option><option>4 Passengers</option></select></div>
    <div class="gt-detail-field"><label>Class</label>
      <select class="gt-input" id="bd-class"><option>Economy</option><option>Business</option><option>First Class</option></select></div>`;

  if (type === "hotel") return `
    <div class="gt-detail-field"><label>Destination</label>
      <input class="gt-input" id="bd-dest" placeholder="City / Hotel" value="${info.destination||''}" /></div>
    <div class="gt-detail-field"><label>Check-in</label>
      <input class="gt-input" id="bd-checkin" type="date" /></div>
    <div class="gt-detail-field"><label>Check-out</label>
      <input class="gt-input" id="bd-checkout" type="date" /></div>
    <div class="gt-detail-field"><label>Guests</label>
      <select class="gt-input" id="bd-guests"><option>1 Guest</option><option>2 Guests</option><option>3 Guests</option><option>4 Guests</option></select></div>`;

  if (type === "car") return `
    <div class="gt-detail-field"><label>Pick-up Location</label>
      <input class="gt-input" id="bd-pickup" placeholder="Pick-up location" /></div>
    <div class="gt-detail-field"><label>Drop-off Location</label>
      <input class="gt-input" id="bd-dropoff" placeholder="Drop-off location" /></div>
    <div class="gt-detail-field"><label>Pick-up Date</label>
      <input class="gt-input" id="bd-pickdate" type="date" /></div>
    <div class="gt-detail-field"><label>Return Date</label>
      <input class="gt-input" id="bd-retdate" type="date" /></div>`;

  if (type === "cruise") return `
    <div class="gt-detail-field"><label>Destination</label>
      <input class="gt-input" id="bd-dest" placeholder="Cruise destination" value="${info.destination||''}" /></div>
    <div class="gt-detail-field"><label>Departure Date</label>
      <input class="gt-input" id="bd-date" type="date" /></div>
    <div class="gt-detail-field"><label>Duration</label>
      <select class="gt-input" id="bd-dur"><option>3-5 Days</option><option>7 Days</option><option>10 Days</option><option>14+ Days</option></select></div>
    <div class="gt-detail-field"><label>Guests</label>
      <select class="gt-input" id="bd-guests"><option>1 Guest</option><option>2 Guests</option><option>3 Guests</option><option>4 Guests</option></select></div>`;

  return `
    <div class="gt-detail-field"><label>Date</label>
      <input class="gt-input" id="bd-date" type="date" /></div>
    <div class="gt-detail-field"><label>Guests</label>
      <select class="gt-input" id="bd-guests"><option>1 Guest</option><option>2 Guests</option><option>3 Guests</option><option>4 Guests</option></select></div>
    <div class="gt-detail-field" style="grid-column:1/-1;"><label>Special Requests</label>
      <input class="gt-input" id="bd-notes" placeholder="Any special requests?" /></div>`;
}

function openBookingDetail(info) {
  const type = getPageType();
  const infoStr = encodeURIComponent(JSON.stringify(info));
  document.getElementById("gt-detail-content").innerHTML = `
    ${info.img ? `<img src="${info.img}" class="gt-detail-img" onerror="this.style.display='none'" />` : ''}
    <div style="padding:20px 25px 25px;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
        <span class="gt-badge-type">${type}</span>
        ${info.badge ? `<span style="background:#f5c518;color:#333;font-size:11px;padding:4px 10px;border-radius:20px;font-weight:600;">${info.badge}</span>` : ''}
      </div>
      <h2 style="color:#1a2b6b;font-size:22px;margin:8px 0 4px;">${info.name}</h2>
      ${info.location ? `<p style="color:#888;font-size:14px;margin-bottom:16px;">📍 ${info.location}</p>` : ''}
      <div class="gt-price-box">
        <div>
          <div style="font-size:12px;color:#888;margin-bottom:2px;">Price from</div>
          <div class="big-price">${info.price ? '$'+info.price : 'Get Quote'}</div>
          <div style="font-size:12px;color:#27ae60;margin-top:4px;">✓ Free cancellation available</div>
        </div>
        <div style="text-align:right;font-size:13px;color:#555;">
          <div>⭐ Top Rated</div>
          <div style="color:#4a90d9;margin-top:4px;font-size:12px;">Instant confirmation</div>
        </div>
      </div>
      <h4 style="color:#1a2b6b;margin-bottom:14px;font-size:15px;">📋 Fill in your details</h4>
      <div class="gt-detail-grid" style="margin-bottom: 20px;">${buildFields(type, info)}</div>
      
      <h4 style="color:#1a2b6b;margin-bottom:14px;font-size:15px;border-top:1px solid #eee;padding-top:15px;">💳 Payment Details</h4>
      <div class="gt-detail-grid">
        <div class="gt-detail-field" style="grid-column:1/-1;">
          <label>Name on Card</label>
          <input class="gt-input" id="bd-cc-name" placeholder="John Doe" />
        </div>
        <div class="gt-detail-field" style="grid-column:1/-1;">
          <label>Card Number</label>
          <input class="gt-input" id="bd-cc-num" placeholder="XXXX XXXX XXXX XXXX" maxlength="19" />
        </div>
        <div class="gt-detail-field">
          <label>Expiry Date</label>
          <input class="gt-input" id="bd-cc-exp" placeholder="MM/YY" maxlength="5" />
        </div>
        <div class="gt-detail-field">
          <label>CVV</label>
          <input class="gt-input" id="bd-cc-cvv" type="password" placeholder="123" maxlength="4" />
        </div>
      </div>
      
      <div id="gt-detail-error" class="gt-error"></div>
      <button class="gt-btn" style="margin-top: 10px;" onclick="submitBookingDetail('${infoStr}')">💳 Pay & Confirm Booking</button>
      <button class="gt-btn-outline" onclick="closeModal('gt-detail-overlay')">Cancel</button>
    </div>`;
  openModal("gt-detail-overlay");
}

async function submitBookingDetail(infoStr) {
  const info = JSON.parse(decodeURIComponent(infoStr));
  if (!isLoggedIn()) {
    closeModal("gt-detail-overlay");
    showToast("Please sign in to book! ✈️");
    setTimeout(() => { openModal("gt-auth-overlay"); switchTab("signin"); }, 800);
    return;
  }
  const type = getPageType();
  const g = (id) => { const el = document.getElementById(id); return el ? el.value : ""; };
  let details = { name: info.name };
  if (type === "flight")  details = { name:info.name, from:g("bd-from"), to:g("bd-to"), departureDate:g("bd-dep"), returnDate:g("bd-ret"), passengers:g("bd-guests"), travelClass:g("bd-class") };
  else if (type === "hotel")  details = { name:info.name, destination:g("bd-dest"), checkIn:g("bd-checkin"), checkOut:g("bd-checkout"), guests:g("bd-guests") };
  else if (type === "car")    details = { name:info.name, pickupLocation:g("bd-pickup"), dropoffLocation:g("bd-dropoff"), pickupDate:g("bd-pickdate"), returnDate:g("bd-retdate") };
  else if (type === "cruise") details = { name:info.name, destination:g("bd-dest"), date:g("bd-date"), duration:g("bd-dur"), guests:g("bd-guests") };
  else details = { name:info.name, date:g("bd-date"), guests:g("bd-guests"), notes:g("bd-notes") };

  const errEl = document.getElementById("gt-detail-error");
  try {
    const res  = await fetch(`${API}/bookings`, {
      method:"POST",
      headers:{"Content-Type":"application/json", Authorization:`Bearer ${getToken()}`},
      body: JSON.stringify({ type, details, price: info.price || 0 }),
    });
    const data = await res.json();
    if (!res.ok) { if(errEl){errEl.textContent=data.error||"Booking failed.";errEl.style.display="block";} }
    else { closeModal("gt-detail-overlay"); showToast("🎉 Booking confirmed! View it in 'My Bookings'."); }
  } catch { if(errEl){errEl.textContent="Cannot reach server.";errEl.style.display="block";} }
}

async function showMyBookings() {
  openModal("gt-bookings-overlay");
  const list = document.getElementById("gt-bookings-list");
  list.innerHTML = `<p style="text-align:center;color:#888;padding:30px;">Loading your bookings…</p>`;
  try {
    const res  = await fetch(`${API}/bookings/me`, { headers:{Authorization:`Bearer ${getToken()}`} });
    const data = await res.json();
    if (!res.ok || !data.length) {
      list.innerHTML = `<div style="text-align:center;padding:40px;">
        <div style="font-size:48px;margin-bottom:12px;">🗺️</div>
        <h3 style="color:#1a2b6b;margin-bottom:8px;">No bookings yet!</h3>
        <p style="color:#888;font-size:14px;">Start exploring and book your first adventure.</p></div>`;
      return;
    }
    list.innerHTML = data.map(b => {
      const title = b.details.name || (b.details.from ? `${b.details.from} → ${b.details.to}` : null) || b.details.destination || "Booking";
      const sub   = b.details.departureDate || b.details.checkIn || b.details.pickupDate || b.details.date || "";
      const guests = b.details.guests || b.details.passengers || "";
      const loc   = b.details.destination || b.details.to || b.details.dropoffLocation || "";
      return `
        <div class="gt-booking-card">
          <div class="gt-booking-top">
            <div>
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                <span style="background:#1a2b6b;color:#fff;font-size:10px;padding:2px 8px;border-radius:20px;text-transform:uppercase;">${b.type}</span>
                <span class="gt-status ${b.status}">${b.status}</span>
              </div>
              <div class="gt-booking-title">${title}</div>
              ${sub ? `<div class="gt-booking-sub">📅 ${sub}</div>` : ''}
            </div>
            <div style="text-align:right;">
              <div style="font-size:22px;font-weight:700;color:#1a2b6b;">$${b.price}</div>
              <div style="font-size:12px;color:#888;">total</div>
            </div>
          </div>
          <div class="gt-booking-details">
            ${loc    ? `<div class="gt-booking-detail-item"><span>Location</span>${loc}</div>` : ''}
            ${guests ? `<div class="gt-booking-detail-item"><span>Guests</span>${guests}</div>` : ''}
            <div class="gt-booking-detail-item"><span>Booked on</span>${new Date(b.createdAt).toLocaleDateString()}</div>
          </div>
          ${b.status !== 'cancelled' ? `<button class="gt-cancel-btn" onclick="cancelBooking('${b._id}')">✕ Cancel Booking</button>` : ''}
        </div>`;
    }).join("");
  } catch { list.innerHTML = `<p style="color:#e53e3e;text-align:center;padding:20px;">Could not load bookings.</p>`; }
}

async function cancelBooking(id) {
  if (!confirm("Are you sure you want to cancel this booking?")) return;
  try {
    const res = await fetch(`${API}/bookings/${id}`, { method:"DELETE", headers:{Authorization:`Bearer ${getToken()}`} });
    if (res.ok) { showToast("Booking cancelled successfully."); showMyBookings(); }
  } catch { showToast("Could not cancel booking.", true); }
}

function wireCards() {
  document.querySelectorAll(".card").forEach(card => {
    card.style.cursor = "pointer";
    card.addEventListener("click", function() {
      const name     = this.querySelector("h3")?.textContent?.trim() || "Item";
      const priceStr = this.querySelector(".price")?.textContent || "";
      const price    = parseInt(priceStr.replace(/[^0-9]/g,"")) || 0;
      const img      = this.querySelector("img")?.src || "";
      const location = this.querySelector("p:not(.price)")?.textContent?.replace(/[^\w\s,]/g,"").trim() || "";
      const badge    = this.querySelector(".badge")?.textContent?.trim() || "";
      openBookingDetail({ name, price, img, location, badge });
    });
  });
  // Flight row Book Now buttons
  document.querySelectorAll(".btn-register").forEach(btn => {
    if (btn.textContent.trim() === "Book Now") {
      btn.addEventListener("click", function(e) {
        e.stopPropagation();
        const row   = this.closest("div[style*='background']") || this.closest("div");
        const route = row?.querySelector("h4")?.textContent || "Flight";
        const price = parseInt(row?.querySelector("h3")?.textContent?.replace(/[^0-9]/g,"")) || 0;
        const parts = route.split("→");
        openBookingDetail({ name:route, from:parts[0]?.trim(), to:parts[1]?.trim(), price });
      });
    }
  });
}

function wireSearchBars() {
  // Legacy search modal logic removed.
  // Search is now handled by dedicated Live API logic in flights.html / hotel.html
}

function wireSubscribe() {
  document.querySelectorAll(".cta-input button").forEach(btn => {
    btn.addEventListener("click", function() {
      const input = this.previousElementSibling;
      const email = input?.value?.trim();
      if (!email || !email.includes("@")) { showToast("Please enter a valid email address.", true); return; }
      input.value = "";
      showToast("Thanks for subscribing! 📬 Best deals coming your way.");
    });
  });
}

function showToast(msg, isError = false) {
  const ex = document.getElementById("gt-toast");
  if (ex) ex.remove();
  const t = document.createElement("div");
  t.id = "gt-toast";
  t.textContent = msg;
  t.style.background = isError ? "#e53e3e" : "#1a2b6b";
  t.style.color = "#fff";
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

function wireFooterLinks() {
  // Map link text to popup content
  const pages = {
    "About Us": `<h3 style="color:#1a2b6b;margin-bottom:10px;">About GoTrip</h3>
      <p style="color:#555;line-height:1.7;">GoTrip is a world-leading travel booking platform helping millions of travelers find the best deals on flights, hotels, tours, car hire, cruises and more. Founded in 2020, we are passionate about making travel easy and affordable for everyone.</p>`,
    "Careers": `<h3 style="color:#1a2b6b;margin-bottom:10px;">Work With Us</h3>
      <p style="color:#555;line-height:1.7;">We're always looking for talented people to join our team. Send your CV to <strong>careers@gotrip.com</strong> and we'll be in touch!</p>`,
    "Blog": `<h3 style="color:#1a2b6b;margin-bottom:10px;">GoTrip Blog</h3>
      <p style="color:#555;line-height:1.7;">Our travel blog is coming soon! We'll be sharing tips, guides and inspiration for your next adventure. Stay tuned!</p>`,
    "Press": `<h3 style="color:#1a2b6b;margin-bottom:10px;">Press & Media</h3>
      <p style="color:#555;line-height:1.7;">For press inquiries, please contact us at <strong>press@gotrip.com</strong>. We'd love to hear from you!</p>`,
    "Gift Cards": `<h3 style="color:#1a2b6b;margin-bottom:10px;">GoTrip Gift Cards</h3>
      <p style="color:#555;line-height:1.7;">Give the gift of travel! GoTrip gift cards are available in any amount and can be used on any booking. Coming soon to our platform.</p>`,
    "Help Center": `<h3 style="color:#1a2b6b;margin-bottom:10px;">Help Center</h3>
      <p style="color:#555;line-height:1.7;">Need help? Email us at <strong>support@gotrip.com</strong> or call <strong>+1 800 GOTRIP</strong>. We're available 24/7 to assist you.</p>`,
    "Contact Us": `<h3 style="color:#1a2b6b;margin-bottom:10px;">Contact GoTrip</h3>
      <p style="color:#555;line-height:1.7;">📧 Email: <strong>hello@gotrip.com</strong><br/>📞 Phone: <strong>+1 800 GOTRIP</strong><br/>🕐 Available 24/7<br/><br/>We'll get back to you within 1 business day.</p>`,
    "Privacy Policy": `<h3 style="color:#1a2b6b;margin-bottom:10px;">Privacy Policy</h3>
      <p style="color:#555;line-height:1.7;">GoTrip respects your privacy. We collect only the data needed to process your bookings. We never sell your personal data to third parties. Full policy available soon.</p>`,
    "Terms of Service": `<h3 style="color:#1a2b6b;margin-bottom:10px;">Terms of Service</h3>
      <p style="color:#555;line-height:1.7;">By using GoTrip, you agree to our terms. Bookings are subject to availability. Cancellation policies vary by booking type. Full terms available soon.</p>`,
    "Travel Insurance": `<h3 style="color:#1a2b6b;margin-bottom:10px;">Travel Insurance</h3>
      <p style="color:#555;line-height:1.7;">Protect your trip with GoTrip Travel Insurance. Coverage for cancellations, medical emergencies, lost luggage and more. Coming soon!</p>`,
    "Airport Transfers": `<h3 style="color:#1a2b6b;margin-bottom:10px;">Airport Transfers</h3>
      <p style="color:#555;line-height:1.7;">Book reliable airport transfers to and from any destination. Private cars, shared shuttles and luxury options available. Coming soon!</p>`,
  };

  // Inject info modal if not already there
  if (!document.getElementById("gt-info-overlay")) {
    const infoModal = document.createElement("div");
    infoModal.className = "gt-overlay";
    infoModal.id = "gt-info-overlay";
    infoModal.innerHTML = `
      <div class="gt-modal" style="max-width:480px;">
        <div class="gt-modal-head">
          <h2 id="gt-info-title"></h2>
          <button class="gt-close" onclick="closeModal('gt-info-overlay')">✕</button>
        </div>
        <div class="gt-modal-body">
          <div id="gt-info-body"></div>
          <button class="gt-btn" style="margin-top:16px;" onclick="closeModal('gt-info-overlay')">Close</button>
        </div>
      </div>`;
    infoModal.addEventListener("click", function(e) { if (e.target === this) closeModal("gt-info-overlay"); });
    document.body.appendChild(infoModal);
  }

  // Wire all footer links
  document.querySelectorAll(".footer a, footer a").forEach(link => {
    const text = link.textContent.trim();
    if (pages[text]) {
      link.addEventListener("click", function(e) {
        e.preventDefault();
        document.getElementById("gt-info-body").innerHTML = pages[text];
        openModal("gt-info-overlay");
      });
    }
  });

  // Wire "View All" links - Show all items in a modal!
  // IMPORTANT: Production-ready behavior: let "View All" links navigate normally.
  // Only show the modal fallback if the link points to "#".
  document.querySelectorAll(".section-header a").forEach(link => {
    const href = (link.getAttribute("href") || "").trim();
    const text = link.textContent.trim();
    if ((text.includes("View All") || text.includes("View All →")) && (href === "" || href === "#")) {
      link.addEventListener("click", function(e) {
        e.preventDefault();
        const section = this.closest('.section');
        if (section) showViewAllModal(section);
      });
    }
  });
}

let gtViewAllItems = [];

function openViewAllItem(index) {
  const info = gtViewAllItems[index];
  if (!info) return;
  closeModal("gt-viewall-overlay");
  openBookingDetail(info);
}

// Show "View All" modal with all items from a section
function showViewAllModal(section) {
  const sectionTitle = section.querySelector("h2")?.textContent || "All Items";
  const cards = Array.from(section.querySelectorAll(".card"));

  if (cards.length === 0) {
    showToast("No items to display.");
    return;
  }

  gtViewAllItems = cards.map((card) => {
    const name = card.querySelector("h3")?.textContent?.trim() || "Item";
    const priceStr = card.querySelector(".price")?.textContent || "";
    const price = parseInt(priceStr.replace(/[^0-9]/g, "")) || 0;
    const img = card.querySelector("img")?.src || "";
    const location =
      card
        .querySelector("p:not(.price)")
        ?.textContent?.replace(/[^\w\s,]/g, "")
        .trim() || "";
    const badgeEl = card.querySelector(".badge");
    const badge = badgeEl?.textContent?.trim() || "";
    const badgeClass = badgeEl?.className || "badge";
    return { name, price, img, location, badge, badgeClass };
  });

  // Create modal HTML
  let modalHTML = `
    <div class="gt-modal" style="max-width:900px; max-height:90vh;">
      <div class="gt-modal-head">
        <h2>${sectionTitle}</h2>
        <button class="gt-close" onclick="closeModal('gt-viewall-overlay')">✕</button>
      </div>
      <div class="gt-modal-body" style="padding:20px;">
        <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap:20px; max-height:70vh; overflow-y:auto;">
  `;

  gtViewAllItems.forEach((info, idx) => {
    modalHTML += `
      <div class="card gt-viewall-card" data-gt-idx="${idx}" style="cursor:pointer;">
        <img src="${info.img}" style="height:150px; object-fit:cover;" onerror="this.style.display='none'" />
        <div class="card-body">
          ${info.badge ? `<span class="${info.badgeClass}">${info.badge}</span>` : ""}
          <h3>${info.name}</h3>
          <p>${info.location}</p>
          <p class="price">${info.price ? "$" + info.price : ""}</p>
        </div>
      </div>
    `;
  });

  modalHTML += `
        </div>
        <button class="gt-btn" style="margin-top:20px;" onclick="closeModal('gt-viewall-overlay')">Close</button>
      </div>
    </div>
  `;

  // Create overlay if it doesn't exist
  if (!document.getElementById("gt-viewall-overlay")) {
    const overlay = document.createElement("div");
    overlay.className = "gt-overlay";
    overlay.id = "gt-viewall-overlay";
    overlay.addEventListener("click", function (e) {
      if (e.target === this) closeModal("gt-viewall-overlay");
    });
    document.body.appendChild(overlay);
  }

  const overlayEl = document.getElementById("gt-viewall-overlay");
  overlayEl.innerHTML = modalHTML;
  overlayEl.querySelectorAll(".gt-viewall-card").forEach((el) => {
    el.addEventListener("click", () => openViewAllItem(parseInt(el.dataset.gtIdx, 10)));
  });

  openModal("gt-viewall-overlay");
}

// Set minimum dates to today (prevents selecting past dates - like time travel protection!)
function setMinDates() {
  const today = new Date().toISOString().split('T')[0];
  document.querySelectorAll('input[type="date"]').forEach(input => {
    input.setAttribute('min', today);
  });
  
  // Smart date validation: check-out must be after check-in
  const checkInInputs = document.querySelectorAll('#bd-checkin');
  const checkOutInputs = document.querySelectorAll('#bd-checkout');
  
  checkInInputs.forEach(checkIn => {
    checkIn.addEventListener('change', function() {
      checkOutInputs.forEach(checkOut => {
        if (this.value) {
          checkOut.setAttribute('min', this.value);
          if (checkOut.value && checkOut.value < this.value) {
            checkOut.value = ''; // Clear invalid date
          }
        }
      });
    });
  });
  
  // Same for flight dates
  const depInputs = document.querySelectorAll('#bd-dep');
  const retInputs = document.querySelectorAll('#bd-ret');
  
  depInputs.forEach(dep => {
    dep.addEventListener('change', function() {
      retInputs.forEach(ret => {
        if (this.value) {
          ret.setAttribute('min', this.value);
          if (ret.value && ret.value < this.value) {
            ret.value = '';
          }
        }
      });
    });
  });
}

// Back to top button magic (appears when you scroll down)
function initBackToTop() {
  const btn = document.querySelector('.back-to-top');
  if (!btn) return;
  
  window.addEventListener('scroll', function() {
    if (window.scrollY > 300) {
      btn.classList.add('show');
    } else {
      btn.classList.remove('show');
    }
  });
}

function initMobileMenu() {
  const navbar = document.querySelector(".navbar");
  const navLinks = document.querySelector(".nav-links");
  if (!navbar || !navLinks) return;

  if (navbar.querySelector(".mobile-menu-toggle")) return;

  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "mobile-menu-toggle";
  btn.setAttribute("aria-label", "Open menu");
  btn.setAttribute("aria-expanded", "false");
  btn.innerHTML = "<span></span><span></span><span></span>";

  const logo = navbar.querySelector(".logo");
  if (logo && logo.nextSibling) navbar.insertBefore(btn, logo.nextSibling);
  else navbar.appendChild(btn);

  const setOpen = (open) => {
    navLinks.classList.toggle("active", open);
    btn.classList.toggle("active", open);
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    btn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    document.body.classList.toggle("gt-menu-open", open);
  };

  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    setOpen(!navLinks.classList.contains("active"));
  });

  navLinks.querySelectorAll("a").forEach((a) => {
    a.addEventListener("click", () => setOpen(false));
  });

  document.addEventListener("click", (e) => {
    if (!navbar.contains(e.target)) setOpen(false);
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth > 768) setOpen(false);
  });
}

function initCookieConsent() {
  const KEY = "gotrip_cookie_consent_v1";
  if (localStorage.getItem(KEY) === "accepted") return;

  if (document.getElementById("gt-cookie")) return;

  const wrap = document.createElement("div");
  wrap.id = "gt-cookie";
  wrap.innerHTML = `
    <div style="
      position:fixed;left:0;right:0;bottom:0;z-index:99999;
      padding:14px 16px;
      background:rgba(15,29,78,0.96);
      color:#fff;
      box-shadow:0 -10px 30px rgba(0,0,0,0.2);
      backdrop-filter: blur(8px);
    ">
      <div style="
        max-width:1100px;margin:0 auto;
        display:flex;gap:12px;align-items:center;justify-content:space-between;
        flex-wrap:wrap;
      ">
        <div style="max-width:720px;">
          <div style="font-weight:700;margin-bottom:2px;">We use cookies</div>
          <div style="opacity:0.9;font-size:13px;line-height:1.5;">
            GoTrip uses cookies to improve your experience and analyze traffic. By clicking “Accept”, you consent to our use of cookies.
          </div>
        </div>
        <div style="display:flex;gap:10px;align-items:center;">
          <button id="gt-cookie-accept" style="
            min-width:120px;min-height:44px;
            background:#4a90d9;border:none;color:#fff;
            padding:10px 16px;border-radius:10px;font-weight:700;cursor:pointer;
          ">Accept</button>
          <button id="gt-cookie-dismiss" style="
            min-width:120px;min-height:44px;
            background:transparent;border:1px solid rgba(255,255,255,0.25);color:#fff;
            padding:10px 16px;border-radius:10px;font-weight:700;cursor:pointer;
          ">Dismiss</button>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(wrap);

  const close = () => {
    wrap.remove();
  };

  document.getElementById("gt-cookie-accept").addEventListener("click", () => {
    localStorage.setItem(KEY, "accepted");
    close();
  });
  document.getElementById("gt-cookie-dismiss").addEventListener("click", () => {
    localStorage.setItem(KEY, "accepted");
    close();
  });
}

function enhanceSearchLoading() {
  document.querySelectorAll(".btn-search").forEach((btn) => {
    if (btn.dataset.gtLoadingWired === "1") return;
    btn.dataset.gtLoadingWired = "1";

    btn.addEventListener("click", () => {
      if (btn.classList.contains("is-loading")) return;
      const original = btn.innerHTML;
      btn.classList.add("is-loading");
      btn.innerHTML = `<span class="gt-spinner" aria-hidden="true"></span>Searching…`;

      // Simulate async search UX (frontend-only)
      setTimeout(() => {
        btn.classList.remove("is-loading");
        btn.innerHTML = original;
      }, 900);
    });
  });
}

function initBackToTopClick() {
  const btn = document.querySelector(".back-to-top");
  if (!btn) return;
  if (btn.dataset.gtWired === "1") return;
  btn.dataset.gtWired = "1";
  btn.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
}

function initCategoryFilters() {
  const groups = document.querySelectorAll("[data-filter-group]");
  if (!groups.length) return;

  groups.forEach((groupEl) => {
    const group = groupEl.getAttribute("data-filter-group");
    const listEl = document.querySelector(`[data-filter-list="${group}"]`);
    if (!listEl) return;

    const btns = Array.from(groupEl.querySelectorAll("[data-filter]"));
    const items = Array.from(listEl.children).filter((el) => el.classList && el.classList.contains("card"));

    const setActive = (btn) => {
      btns.forEach((b) => {
        const active = b === btn;
        b.classList.toggle("active", active);
        b.style.background = active ? "#1a2b6b" : "#f0f3fa";
        b.style.color = active ? "#fff" : "#1a2b6b";
      });
    };

    const apply = (filter) => {
      items.forEach((card) => {
        const cat = (card.getAttribute("data-category") || "").toLowerCase();
        const show = filter === "all" || cat === filter;
        card.style.display = show ? "" : "none";
      });
    };

    btns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const filter = (btn.getAttribute("data-filter") || "all").toLowerCase();
        setActive(btn);
        apply(filter);
      });
    });
  });
}

function initTestimonials() {
  const data = [
    { name: "Amina K.", role: "Solo traveler", rating: 5, text: "Booked a last‑minute hotel in Rome in under 2 minutes. The mobile experience is clean and fast, and the price was better than I expected." },
    { name: "Daniel R.", role: "Business traveler", rating: 5, text: "Loved the quick filters and the booking flow. No confusing steps, and everything felt polished on my phone." },
    { name: "Mei L.", role: "Family trip", rating: 4, text: "We found a great family-friendly stay and the details were accurate. Support info was easy to find and the UI is very straightforward." },
    { name: "Carlos S.", role: "Weekend getaway", rating: 5, text: "The destination cards and recommendations are spot on. Smooth scrolling, no layout glitches, and the site looks premium." },
    { name: "Priya N.", role: "Couples trip", rating: 5, text: "The hotel images look great on every screen size. Booking felt trustworthy and professional." },
    { name: "Sophie M.", role: "Adventure traveler", rating: 4, text: "Great mix of tours and activities. The ‘View all reviews’ list helped me decide quickly." },
    { name: "Omar H.", role: "Frequent flyer", rating: 5, text: "Flights page is easy to scan on mobile. Tap targets are comfortable and nothing overflows." },
    { name: "Hannah P.", role: "First-time user", rating: 5, text: "Cookie consent is clear, the menu works perfectly, and the whole site feels modern." },
  ];

  function stars(n) {
    const full = "★".repeat(n);
    const empty = "☆".repeat(Math.max(0, 5 - n));
    return `<span style="color:#f5c518;font-size:13px;">${full}${empty}</span>`;
  }

  // Ensure overlay exists (reuses modal styles)
  if (!document.getElementById("gt-reviews-overlay")) {
    const overlay = document.createElement("div");
    overlay.className = "gt-overlay";
    overlay.id = "gt-reviews-overlay";
    overlay.addEventListener("click", function (e) {
      if (e.target === this) closeModal("gt-reviews-overlay");
    });
    document.body.appendChild(overlay);
  }

  const openReviews = () => {
    const overlay = document.getElementById("gt-reviews-overlay");
    overlay.innerHTML = `
      <div class="gt-modal" style="max-width:820px; max-height:90vh;">
        <div class="gt-modal-head">
          <h2>Customer Reviews</h2>
          <button class="gt-close" onclick="closeModal('gt-reviews-overlay')">✕</button>
        </div>
        <div class="gt-modal-body" style="padding:18px 18px 22px;">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">
            ${data.slice(0, 8).map(r => `
              <div style="border:1px solid #eef1f8;border-radius:12px;padding:14px;background:#fff;">
                <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px;">
                  <div style="font-weight:700;color:#1a2b6b;">${r.name}</div>
                  ${stars(r.rating)}
                </div>
                <div style="color:#888;font-size:12px;margin-bottom:8px;">${r.role}</div>
                <div style="color:#555;font-size:13px;line-height:1.7;">${r.text}</div>
              </div>
            `).join("")}
          </div>
          <button class="gt-btn" style="margin-top:16px;" onclick="closeModal('gt-reviews-overlay')">Close</button>
        </div>
      </div>
    `;
    openModal("gt-reviews-overlay");
  };

  // Add a Reviews CTA button to testimonial sections if missing
  document.querySelectorAll(".testimonial-section").forEach((section) => {
    if (section.querySelector("[data-open-reviews]")) return;
    const inner = section.querySelector(".testimonial-inner") || section;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn-register";
    btn.textContent = "View all reviews";
    btn.setAttribute("data-open-reviews", "1");
    btn.style.marginTop = "14px";
    btn.addEventListener("click", openReviews);

    // Prefer placing under the left text block when available
    const left = inner.querySelector("div");
    (left || inner).appendChild(btn);
  });

  // If there's any nav link to #reviews, open the modal instead
  document.querySelectorAll('a[href="#reviews"]').forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      openReviews();
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  injectModals();
  updateNavbar();
  wireCards();
  wireSearchBars();
  wireSubscribe();
  wireFooterLinks();
  setMinDates(); // Activate date protection!
  initBackToTop(); // Activate scroll spy!
  initBackToTopClick();
  initMobileMenu();
  initCookieConsent();
  enhanceSearchLoading();
  initCategoryFilters();
  initTestimonials();
});

// --- LIVE HOTELS FETCH (RAPIDAPI) ---
async function fetchLiveHotels(query = "Bali") {
  const grid = document.getElementById("live-hotels-grid");
  const loading = document.getElementById("live-hotels-loading");
  if (!grid || !loading) return;

  try {
    const res = await fetch(`${API}/hotels?query=${encodeURIComponent(query)}`);
    const data = await res.json();

    if (data.status === "success" && data.data && data.data.length > 0) {
      loading.style.display = "none";
      grid.style.display = "grid";
      grid.innerHTML = "";

      data.data.forEach(hotel => {
        const priceText = hotel.price ? `From ${Math.round(hotel.price)} ${hotel.currency}/night` : "Check prices";
        const ratingHtml = hotel.rating ? `<i class="fa-solid fa-star" style="color:#f5c518;"></i> ${hotel.rating}` : "New";
        const imgUrl = hotel.image || "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400&h=180&fit=crop";

        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `
          <img src="${imgUrl}" alt="${hotel.name}" onerror="this.src='https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400&h=180&fit=crop'" />
          <div class="card-body">
            <span class="badge blue">Live Rate</span>
            <h3>${hotel.name}</h3>
            <p>${ratingHtml} · ${hotel.reviews} reviews</p>
            <p class="price">${priceText}</p>
          </div>
        `;
        // Wire up the card to the details modal
        card.addEventListener("click", () => {
           showDetailModal("hotel", {
               destination: hotel.name,
               price: Math.round(hotel.price) || 250,
               rating: hotel.rating || 4.5,
               image: imgUrl
           });
        });
        grid.appendChild(card);
      });
    } else {
      loading.innerHTML = "<p>No hotels found for this destination at the moment.</p>";
    }
  } catch (error) {
    console.error("Error fetching live hotels:", error);
    loading.innerHTML = "<p>Error loading live hotel data. Please try again later.</p>";
  }
}

// Call fetchLiveHotels on page load if the container exists
document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("live-hotels-grid")) {
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('query') || 'Bali';
    fetchLiveHotels(query);
  }

  // Wire up Global Search Bar
  const searchBtn = document.getElementById("global-search-btn");
  const searchInput = document.getElementById("global-search-input");
  
  if (searchBtn && searchInput) {
    searchBtn.addEventListener("click", () => {
      const query = searchInput.value.trim();
      if (!query) return;
      
      // If we are already on hotel.html, just fetch and update
      if (window.location.pathname.endsWith("hotel.html")) {
        const loading = document.getElementById("live-hotels-loading");
        const grid = document.getElementById("live-hotels-grid");
        if (loading) loading.style.display = "block";
        if (grid) grid.style.display = "none";
        
        // Update URL without reloading page
        const newUrl = new URL(window.location);
        newUrl.searchParams.set('query', query);
        window.history.pushState({}, '', newUrl);
        
        fetchLiveHotels(query);
      } else {
        // Redirect to hotel.html with query
        window.location.href = `hotel.html?query=${encodeURIComponent(query)}`;
      }
    });

    // Also search on enter key
    searchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        searchBtn.click();
      }
    });
  }

  // Wire up Flight Search and Autocomplete
  const flightSearchBtn = document.getElementById("flight-search-btn");
  if (flightSearchBtn) {
    let globalIataMap = {
      "JFK": "New York", "LHR": "London", "DAC": "Dhaka", "KTM": "Kathmandu"
    };

    const setupAutocomplete = (inputId, dropdownId) => {
      const input = document.getElementById(inputId);
      const dropdown = document.getElementById(dropdownId);
      if (!input || !dropdown) return;

      let timeout = null;
      input.addEventListener("input", (e) => {
        clearTimeout(timeout);
        const val = e.target.value.trim();
        if (val.length < 2) {
          dropdown.style.display = "none";
          return;
        }

        timeout = setTimeout(async () => {
          try {
            const res = await fetch(`${API}/flights/places?query=${val}`);
            const data = await res.json();
            if (data.status === "success" && data.places.length > 0) {
              dropdown.innerHTML = "";
              data.places.forEach(p => {
                globalIataMap[p.iata_code] = p.name; // Cache the name
                const div = document.createElement("div");
                div.style = "padding:10px; border-bottom:1px solid #eee; cursor:pointer; font-size:13px; color:#333;";
                div.innerHTML = `<strong>${p.name}</strong> (${p.iata_code}) <span style="color:#888; font-size:11px; float:right;">${p.type === 'city' ? 'City' : 'Airport'}</span>`;
                div.addEventListener("click", () => {
                  input.value = p.name;
                  input.dataset.iata = p.iata_code;
                  dropdown.style.display = "none";
                });
                div.addEventListener("mouseenter", () => div.style.background = "#f0f3fa");
                div.addEventListener("mouseleave", () => div.style.background = "#fff");
                dropdown.appendChild(div);
              });
              dropdown.style.display = "block";
            } else {
              dropdown.style.display = "none";
            }
          } catch (err) {
            console.error("Places API error:", err);
          }
        }, 300);
      });

      // Close dropdown when clicking outside
      document.addEventListener("click", (e) => {
        if (e.target !== input && !dropdown.contains(e.target)) {
          dropdown.style.display = "none";
        }
      });
    };

    setupAutocomplete("flight-origin", "origin-autocomplete");
    setupAutocomplete("flight-dest", "dest-autocomplete");

    flightSearchBtn.addEventListener("click", () => {
      const originInput = document.getElementById("flight-origin");
      const destInput = document.getElementById("flight-dest");
      
      // Use dataset iata if selected from dropdown, otherwise fallback to typed text
      let origin = (originInput?.dataset.iata || originInput?.value.trim()).toUpperCase() || "LHR";
      let dest = (destInput?.dataset.iata || destInput?.value.trim()).toUpperCase() || "JFK";
      
      let date = document.getElementById("flight-date")?.value;
      const pass = document.getElementById("flight-passengers")?.value || 1;

      if (!date) {
        // default to 14 days from now if empty
        const d = new Date();
        d.setDate(d.getDate() + 14);
        date = d.toISOString().split('T')[0];
      }

      fetchLiveFlights(origin, dest, date, pass, globalIataMap);
    });

    // Automatically load default flights on page load if container exists
    if (document.getElementById("live-flights-container")) {
      const d = new Date();
      d.setDate(d.getDate() + 14);
      const dateStr = d.toISOString().split('T')[0];
      fetchLiveFlights("LHR", "JFK", dateStr, 1, globalIataMap);
    }
  }
});

// --- LIVE FLIGHTS FETCH (DUFFEL API) ---
async function fetchLiveFlights(origin, dest, date, passengers, iataToCity = {}) {
  const container = document.getElementById("live-flights-container");
  const loading = document.getElementById("live-flights-loading");
  if (!container || !loading) return;

  loading.style.display = "block";
  container.innerHTML = "";
  
  // Scroll to section
  document.getElementById("flights-section-title")?.scrollIntoView({ behavior: 'smooth', block: 'start' });

  try {
    const res = await fetch(`${API}/flights/search?origin=${origin}&destination=${dest}&departure_date=${date}&passengers=${passengers}`);
    const data = await res.json();

    loading.style.display = "none";

    const displayOrigin = iataToCity[origin] || origin;
    const displayDest = iataToCity[dest] || dest;

    if (data.status === "success" && data.flights && data.flights.length > 0) {
      data.flights.forEach(flight => {
        // Parse ISO duration e.g., PT7H30M
        let durStr = flight.duration.replace("PT", "");
        durStr = durStr.replace("H", "h ").replace("M", "m");

        // Format dates
        const depTime = new Date(flight.departure_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const arrTime = new Date(flight.arrival_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

        const priceText = flight.price ? `$${flight.price}` : "Check prices";

        let segmentsHtml = "";
        if (flight.segments && flight.segments.length > 0) {
          segmentsHtml = `<div id="seg-${flight.id}" style="width: 100%; font-size: 12px; color: #555; background: #f9f9f9; padding: 10px; border-radius: 6px; margin-top: 10px; display: none; line-height: 1.5;"><strong>Flight Details:</strong><br/>`;
          flight.segments.forEach((seg, i) => {
            const sDep = new Date(seg.departing_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            const sArr = new Date(seg.arriving_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            const segOrigin = iataToCity[seg.origin] || seg.origin;
            const segDest = iataToCity[seg.destination] || seg.destination;
            segmentsHtml += `• ${segOrigin} (${seg.origin}) → ${segDest} (${seg.destination}) | ${seg.airline} ${seg.flight_number} | ${sDep} - ${sArr}<br/>`;
          });
          segmentsHtml += `</div>`;
        }

        const card = document.createElement("div");
        card.style = "background:#fff; border-radius:10px; padding:20px 25px; display:flex; align-items:center; justify-content:space-between; box-shadow:0 2px 10px rgba(0,0,0,0.06); flex-wrap:wrap; gap:15px;";
        card.innerHTML = `
          <div style="display:flex; align-items:center; gap:20px; min-width: 250px;">
            <div style="background:#f0f3fa; padding:10px 15px; border-radius:8px; text-align:center;">
              <i class="fa-solid fa-plane" style="color:#1a2b6b; font-size:20px;"></i>
              <p style="font-size:11px; color:#777; margin-top:4px;">${flight.airline}</p>
            </div>
            <div>
              <h4 style="color:#1a2b6b; font-size:15px;">${displayOrigin} → ${displayDest}</h4>
              <p style="color:#777; font-size:13px;"><i class="fa-solid fa-clock" style="color:#4a90d9;"></i> ${durStr} &nbsp; ${flight.stops}</p>
              <span onclick="document.getElementById('seg-${flight.id}').style.display = document.getElementById('seg-${flight.id}').style.display === 'none' ? 'block' : 'none';" style="font-size: 12px; color: #4a90d9; text-decoration: underline; cursor: pointer; display: inline-block; margin-top: 4px;">View Details</span>
            </div>
          </div>
          <div style="text-align:center;">
            <p style="color:#777; font-size:13px;">Departure</p>
            <h4 style="color:#1a2b6b;">${depTime}</h4>
          </div>
          <div style="text-align:center;">
            <p style="color:#777; font-size:13px;">Arrival</p>
            <h4 style="color:#1a2b6b;">${arrTime}</h4>
          </div>
          <div style="text-align:right;">
            <h3 style="color:#1a2b6b; font-size:22px; font-weight:700;">${priceText} ${flight.currency}</h3>
            <p style="color:#777; font-size:12px;">total price</p>
            <button class="btn-register" id="book-btn-${flight.id}" style="margin-top:8px; padding:8px 18px; font-size:13px;">Book Now</button>
          </div>
          ${segmentsHtml}
        `;
        container.appendChild(card);

        // Wire up the button to openBookingDetail
        const btn = document.getElementById(`book-btn-${flight.id}`);
        if (btn) {
          btn.addEventListener("click", () => {
            openBookingDetail({
              name: flight.airline + " Flight",
              price: flight.price,
              location: displayOrigin + " to " + displayDest,
              badge: flight.stops
            });
          });
        }
      });
    } else {
      container.innerHTML = "<p style='text-align:center; padding: 20px;'>No flights found for this route. Try different IATA codes or dates (e.g. LHR to JFK).</p>";
    }
  } catch (error) {
    console.error("Error fetching live flights:", error);
    loading.style.display = "none";
    container.innerHTML = "<p style='text-align:center; padding: 20px;'>Error loading live flight data. Please try again later.</p>";
  }
}

