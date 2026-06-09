import os
import glob
import re

modal_html = """
<!-- AUTH MODAL -->
<div id="authModal" class="fixed inset-0 bg-black/60 z-50 hidden flex items-center justify-center p-4 backdrop-blur-sm transition-opacity">
  <div class="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden relative transform transition-all scale-95 opacity-0 duration-300" id="authModalContent">
    <button id="closeAuthModal" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors z-10">
      <i class="fa-solid fa-xmark text-xl"></i>
    </button>
    
    <div class="flex border-b border-gray-100">
      <button id="tabLogin" class="flex-1 py-4 text-sm font-semibold text-[#1a2b6b] border-b-2 border-[#1a2b6b] transition-colors">Sign In</button>
      <button id="tabRegister" class="flex-1 py-4 text-sm font-semibold text-gray-400 border-b-2 border-transparent hover:text-gray-600 transition-colors">Register</button>
    </div>

    <!-- Login Form -->
    <div id="formLogin" class="p-8">
      <h2 class="text-2xl font-bold text-gray-800 mb-6 text-center">Welcome Back</h2>
      <form class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input type="email" class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:border-[#1a2b6b] focus:ring-1 focus:ring-[#1a2b6b]" placeholder="you@example.com" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input type="password" class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:border-[#1a2b6b] focus:ring-1 focus:ring-[#1a2b6b]" placeholder="••••••••" />
        </div>
        <div class="flex items-center justify-between text-sm">
          <label class="flex items-center gap-2 cursor-pointer text-gray-600">
            <input type="checkbox" class="rounded text-[#1a2b6b] focus:ring-[#1a2b6b]" /> Remember me
          </label>
          <a href="#" class="text-[#1a2b6b] hover:underline font-medium">Forgot Password?</a>
        </div>
        <button type="button" class="w-full bg-[#1a2b6b] hover:bg-[#2d4a9e] text-white font-semibold py-3 rounded-lg transition-colors mt-4">Sign In</button>
        
        <div class="relative flex items-center justify-center mt-6">
          <span class="absolute bg-white px-2 text-xs text-gray-400">OR CONTINUE WITH</span>
          <div class="w-full border-t border-gray-200"></div>
        </div>
        
        <div class="grid grid-cols-2 gap-3 mt-6">
          <button type="button" class="flex items-center justify-center gap-2 border border-gray-300 rounded-lg py-2 hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700">
            <i class="fa-brands fa-google text-red-500"></i> Google
          </button>
          <button type="button" class="flex items-center justify-center gap-2 border border-gray-300 rounded-lg py-2 hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700">
            <i class="fa-brands fa-facebook text-blue-600"></i> Facebook
          </button>
        </div>
      </form>
    </div>

    <!-- Register Form -->
    <div id="formRegister" class="p-8 hidden">
      <h2 class="text-2xl font-bold text-gray-800 mb-6 text-center">Create an Account</h2>
      <form class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">First Name</label>
            <input type="text" class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:border-[#1a2b6b] focus:ring-1 focus:ring-[#1a2b6b]" placeholder="John" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
            <input type="text" class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:border-[#1a2b6b] focus:ring-1 focus:ring-[#1a2b6b]" placeholder="Doe" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input type="email" class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:border-[#1a2b6b] focus:ring-1 focus:ring-[#1a2b6b]" placeholder="you@example.com" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input type="password" class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:border-[#1a2b6b] focus:ring-1 focus:ring-[#1a2b6b]" placeholder="••••••••" />
        </div>
        <button type="button" class="w-full bg-[#1a2b6b] hover:bg-[#2d4a9e] text-white font-semibold py-3 rounded-lg transition-colors mt-4">Create Account</button>
      </form>
      <p class="text-xs text-center text-gray-500 mt-6">By signing up, you agree to our <a href="#" class="text-[#1a2b6b] hover:underline">Terms of Service</a> and <a href="#" class="text-[#1a2b6b] hover:underline">Privacy Policy</a>.</p>
    </div>
  </div>
</div>
"""

js_code = """
  // Modal Logic
  const authModal = document.getElementById('authModal');
  const authModalContent = document.getElementById('authModalContent');
  const closeAuthModal = document.getElementById('closeAuthModal');
  
  const tabLogin = document.getElementById('tabLogin');
  const tabRegister = document.getElementById('tabRegister');
  const formLogin = document.getElementById('formLogin');
  const formRegister = document.getElementById('formRegister');
  
  const btnLogins = document.querySelectorAll('.btn-login');
  const btnRegisters = document.querySelectorAll('.btn-register');

  function openModal(isRegister = false) {
    if(authModal) {
      authModal.classList.remove('hidden');
      // small delay for transition
      setTimeout(() => {
        authModalContent.classList.remove('scale-95', 'opacity-0');
        authModalContent.classList.add('scale-100', 'opacity-100');
      }, 10);
      
      if(isRegister) {
        switchToRegister();
      } else {
        switchToLogin();
      }
    }
  }

  function closeModal() {
    if(authModal) {
      authModalContent.classList.remove('scale-100', 'opacity-100');
      authModalContent.classList.add('scale-95', 'opacity-0');
      setTimeout(() => {
        authModal.classList.add('hidden');
      }, 300);
    }
  }

  function switchToLogin() {
    tabLogin.classList.replace('text-gray-400', 'text-[#1a2b6b]');
    tabLogin.classList.replace('border-transparent', 'border-[#1a2b6b]');
    tabRegister.classList.replace('text-[#1a2b6b]', 'text-gray-400');
    tabRegister.classList.replace('border-[#1a2b6b]', 'border-transparent');
    formLogin.classList.remove('hidden');
    formRegister.classList.add('hidden');
  }

  function switchToRegister() {
    tabRegister.classList.replace('text-gray-400', 'text-[#1a2b6b]');
    tabRegister.classList.replace('border-transparent', 'border-[#1a2b6b]');
    tabLogin.classList.replace('text-[#1a2b6b]', 'text-gray-400');
    tabLogin.classList.replace('border-[#1a2b6b]', 'border-transparent');
    formRegister.classList.remove('hidden');
    formLogin.classList.add('hidden');
  }

  btnLogins.forEach(btn => btn.addEventListener('click', (e) => {
    e.preventDefault();
    openModal(false);
  }));
  
  btnRegisters.forEach(btn => btn.addEventListener('click', (e) => {
    e.preventDefault();
    openModal(true);
  }));

  if(closeAuthModal) closeAuthModal.addEventListener('click', closeModal);
  if(tabLogin) tabLogin.addEventListener('click', switchToLogin);
  if(tabRegister) tabRegister.addEventListener('click', switchToRegister);
  
  // Close on outside click
  if(authModal) {
    authModal.addEventListener('click', (e) => {
      if (e.target === authModal) {
        closeModal();
      }
    });
  }
"""

def inject_modal_html():
    html_files = glob.glob('c:/Users/user/Desktop/mytravelproject/*.html')
    for f in html_files:
        if 'admin' in f or 'checkout' in f or 'profile' in f:
            continue # skip admins and checkout/profile for now
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        if 'id="authModal"' not in content:
            # Inject before </body>
            content = content.replace('</body>', modal_html + '\n</body>')
            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)

def inject_modal_js():
    js_file = 'c:/Users/user/Desktop/mytravelproject/js/script.js'
    if os.path.exists(js_file):
        with open(js_file, 'r', encoding='utf-8') as file:
            content = file.read()
        
        if 'id="authModal"' not in content:
            with open(js_file, 'a', encoding='utf-8') as file:
                file.write('\n' + js_code)

if __name__ == "__main__":
    inject_modal_html()
    inject_modal_js()
    print("Modal injected successfully!")
