document.addEventListener("DOMContentLoaded", () => {
  if (!getToken()) {
    window.location.href = "index.html";
    return;
  }
  initProfile();
  setupTabs();
});

function setupTabs() {
  const tabs = document.querySelectorAll(".profile-tab");
  const sections = document.querySelectorAll(".profile-section");

  // Check URL hash on load
  const hash = window.location.hash || "#personal";
  
  function switchTab(targetHash) {
    let targetTab = Array.from(tabs).find(t => t.getAttribute("href") === targetHash);
    if (!targetTab) targetTab = tabs[0];
    
    // Update active tab styles
    tabs.forEach(t => {
      t.classList.remove("bg-blue-50", "border-[#1a2b6b]", "text-[#1a2b6b]", "active");
      t.classList.add("text-gray-600", "border-transparent", "hover:bg-gray-50", "hover:text-[#1a2b6b]");
    });
    
    targetTab.classList.remove("text-gray-600", "border-transparent", "hover:bg-gray-50", "hover:text-[#1a2b6b]");
    targetTab.classList.add("bg-blue-50", "border-[#1a2b6b]", "text-[#1a2b6b]", "active");
    
    // Show correct section
    const targetId = targetTab.getAttribute("data-target");
    sections.forEach(s => {
      s.classList.remove("block");
      s.classList.add("hidden");
    });
    
    const activeSection = document.getElementById(targetId);
    if (activeSection) {
      activeSection.classList.remove("hidden");
      activeSection.classList.add("block");
    }

    // Load bookings if that tab is clicked
    if (targetId === "section-bookings") {
      loadProfileBookings();
    }
  }

  // Handle click events
  tabs.forEach(tab => {
    tab.addEventListener("click", (e) => {
      // Don't prevent default if it's a hash link, let URL update
      if (tab.getAttribute("href").startsWith("#")) {
        // Just let it change the hash, the hashchange event will catch it
        // Or we can manually switch it and prevent default to avoid scrolling jumping
        e.preventDefault();
        window.history.pushState(null, null, tab.getAttribute("href"));
        switchTab(tab.getAttribute("href"));
      }
    });
  });

  // Handle browser back/forward
  window.addEventListener("hashchange", () => {
    switchTab(window.location.hash || "#personal");
  });

  // Initial setup
  switchTab(hash);
}

async function loadProfileBookings() {
  const list = document.getElementById("profile-bookings-list");
  list.innerHTML = `<p class="text-gray-500">Loading bookings...</p>`;
  try {
    const res = await fetch(`${window.ELITE_API_URL || "https://travel-xyyl.onrender.com"}/api/bookings/me`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    if (!res.ok) throw new Error("Failed to load");
    const data = await res.json();
    if (data.length === 0) {
      list.innerHTML = `<p class="text-gray-500">You have no active bookings.</p>`;
      return;
    }
    list.innerHTML = data.map(b => `
      <div class="border border-gray-100 rounded-lg p-4 flex justify-between items-center hover:bg-gray-50 transition-colors">
        <div>
          <p class="font-bold text-[#1a2b6b]">${b.itemName || b.itemType || (b.details && b.details.name) || "Booking"}</p>
          <p class="text-sm text-gray-500">Date: ${b.bookingDate || (b.details && (b.details.departureDate || b.details.checkIn || b.details.pickupDate || b.details.date)) || 'N/A'}</p>
          <p class="text-sm text-gray-500">Status: <span class="text-green-600 font-medium">${b.status}</span></p>
        </div>
        <div class="text-right">
          <p class="font-bold text-gray-800">$${b.totalPrice || b.price}</p>
          <p class="text-xs text-gray-400">ID: ${(b._id || b.id || "000000").substring(0,6)}...</p>
        </div>
      </div>
    `).join("");
  } catch (err) {
    list.innerHTML = `<p class="text-red-500">Error loading bookings: ${err.message}</p>`;
  }
}

async function initProfile() {
  await loadCountries();

  // Load Profile Data
  await loadProfile();

  // Event Listeners
  document.getElementById("profile-upload").addEventListener("change", handleProfilePictureUpload);
  document.getElementById("prof-edit-btn").addEventListener("click", toggleEditMode);
  document.getElementById("prof-save-btn").addEventListener("click", handleProfileSave);
  document.getElementById("pw-save-btn").addEventListener("click", handleChangePassword);
}

function toggleEditMode() {
  const inputs = ["prof-firstName", "prof-lastName", "prof-phone", "prof-address", "prof-city"];
  const select = document.getElementById("prof-country");
  
  inputs.forEach(id => {
    const el = document.getElementById(id);
    el.removeAttribute("readonly");
    el.classList.remove("border-transparent", "bg-transparent");
    el.classList.add("border-gray-300", "bg-white");
  });
  
  select.removeAttribute("disabled");
  select.classList.remove("border-transparent", "bg-transparent", "appearance-none", "cursor-default");
  select.classList.add("border-gray-300", "bg-white");

  document.getElementById("prof-edit-btn").classList.add("hidden");
  document.getElementById("prof-save-btn").classList.remove("hidden");
}

function disableEditMode() {
  const inputs = ["prof-firstName", "prof-lastName", "prof-phone", "prof-address", "prof-city"];
  const select = document.getElementById("prof-country");
  
  inputs.forEach(id => {
    const el = document.getElementById(id);
    el.setAttribute("readonly", "readonly");
    el.classList.remove("border-gray-300", "bg-white");
    el.classList.add("border-transparent", "bg-transparent");
  });
  
  select.setAttribute("disabled", "disabled");
  select.classList.remove("border-gray-300", "bg-white");
  select.classList.add("border-transparent", "bg-transparent", "appearance-none", "cursor-default");

  document.getElementById("prof-save-btn").classList.add("hidden");
  document.getElementById("prof-edit-btn").classList.remove("hidden");
}

async function loadCountries() {
  const countrySelect = document.getElementById("prof-country");
  try {
    const res = await fetch("https://restcountries.com/v3.1/all?fields=name,cca2");
    let countries = await res.json();
    countries.sort((a, b) => a.name.common.localeCompare(b.name.common));
    
    countrySelect.innerHTML = "";
    countries.forEach(c => {
      const option = document.createElement("option");
      option.value = c.name.common;
      option.textContent = c.name.common;
      countrySelect.appendChild(option);
    });
  } catch (err) {
    console.error("Failed to load countries:", err);
  }
}

async function loadProfile() {
  try {
    const res = await fetch(`${API}/user/me?token=${getToken()}`);
    if (!res.ok) throw new Error("Failed to fetch profile");
    const user = await res.json();
    
    // Populate Sidebar
    document.getElementById("sidebar-name").textContent = `${user.firstName} ${user.lastName}`;
    document.getElementById("sidebar-member-since").textContent = `Member since ${new Date(user.created_at || Date.now()).getFullYear()}`;
    if (user.profilePicture) {
      document.getElementById("sidebar-avatar").src = user.profilePicture;
    }
    
    // Populate Form
    document.getElementById("prof-firstName").value = user.firstName || "";
    document.getElementById("prof-lastName").value = user.lastName || "";
    document.getElementById("prof-email").value = user.email || "";
    document.getElementById("prof-phone").value = user.phoneNumber || "";
    document.getElementById("prof-address").value = user.address || "";
    document.getElementById("prof-city").value = user.city || "";
    if (user.country) {
      document.getElementById("prof-country").value = user.country;
    }
  } catch (err) {
    showToast("Could not load profile data.");
  }
}

async function handleProfilePictureUpload(e) {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("token", getToken());
  formData.append("profilePictureFile", file);

  try {
    showToast("Uploading picture...");
    const res = await fetch(`${API}/user/update`, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload failed");
    
    if (data.user && data.user.profilePicture) {
      document.getElementById("sidebar-avatar").src = data.user.profilePicture;
      
      // Update local storage user caching
      const localUser = getUser();
      localUser.profilePicture = data.user.profilePicture;
      localStorage.setItem("gotrip_user", JSON.stringify(localUser));
      updateNavbar();
      
      showToast("Profile picture updated! 🎉");
    }
  } catch (err) {
    showToast("Upload failed: " + err.message);
  }
}

async function handleProfileSave() {
  const btn = document.getElementById("prof-save-btn");
  btn.textContent = "Saving...";
  btn.disabled = true;

  const formData = new FormData();
  formData.append("token", getToken());
  formData.append("firstName", document.getElementById("prof-firstName").value);
  formData.append("lastName", document.getElementById("prof-lastName").value);
  formData.append("phoneNumber", document.getElementById("prof-phone").value);
  formData.append("address", document.getElementById("prof-address").value);
  formData.append("city", document.getElementById("prof-city").value);
  formData.append("country", document.getElementById("prof-country").value);

  try {
    const res = await fetch(`${API}/user/update`, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to save");
    
    showToast("Profile saved successfully!");
    
    // Update local user and sidebar
    const localUser = getUser();
    localUser.firstName = data.user.firstName;
    localUser.lastName = data.user.lastName;
    localUser.phoneNumber = data.user.phoneNumber;
    localUser.address = data.user.address;
    localUser.city = data.user.city;
    localUser.country = data.user.country;
    localStorage.setItem("gotrip_user", JSON.stringify(localUser));
    
    document.getElementById("sidebar-name").textContent = `${data.user.firstName} ${data.user.lastName}`;
    updateNavbar();
    
    // Switch back to read-only mode
    disableEditMode();
  } catch (err) {
    showToast("Save failed: " + err.message);
  } finally {
    btn.textContent = "Save Changes";
    btn.disabled = false;
  }
}

async function handleChangePassword() {
  const current = document.getElementById("pw-current").value;
  const newPw = document.getElementById("pw-new").value;
  const confirmPw = document.getElementById("pw-confirm").value;

  if (!current || !newPw || !confirmPw) return showToast("Please fill all password fields.");
  if (newPw !== confirmPw) return showToast("New passwords do not match.");

  const btn = document.getElementById("pw-save-btn");
  btn.textContent = "Updating...";
  btn.disabled = true;

  try {
    const res = await fetch(`${API}/user/change-password?token=${getToken()}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ oldPassword: current, newPassword: newPw })
    });
    const data = await res.json();
    
    if (!res.ok) {
      let errorMsg = data.detail || "Password update failed";
      if (Array.isArray(data.detail)) errorMsg = data.detail[0].msg;
      throw new Error(errorMsg);
    }
    
    showToast("Password updated successfully! 🔒");
    document.getElementById("pw-current").value = "";
    document.getElementById("pw-new").value = "";
    document.getElementById("pw-confirm").value = "";
  } catch (err) {
    showToast(err.message.replace("Value error, ", ""));
  } finally {
    btn.textContent = "Update Password";
    btn.disabled = false;
  }
}
