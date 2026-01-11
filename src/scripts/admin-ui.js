/**
 * 后台 UI 交互逻辑
 * 包含主题切换、侧边栏折叠、弹框管理、用户信息加载等
 */

export function initAdminUI() {
    // ============== 弹框系统 (Modals) ==============
    (function initModals() {
        if (window.adminAlert) return;

        window._adminModalState = {
            currentMode: "alert",
            resolveCallback: null
        };

        const iconBgMap = {
            success: 'bg-green-100 dark:bg-green-500/20',
            error: 'bg-red-100 dark:bg-red-500/20',
            warning: 'bg-orange-100 dark:bg-orange-500/20',
            info: 'bg-blue-100 dark:bg-blue-500/20',
            confirm: 'bg-zinc-100 dark:bg-zinc-800'
        };

        function getElements() {
            return {
                modal: document.getElementById('adminModal'),
                modalContent: document.getElementById('adminModalContent'),
                modalIcon: document.getElementById('adminModalIcon'),
                modalTitle: document.getElementById('adminModalTitle'),
                modalMessage: document.getElementById('adminModalMessage'),
                modalConfirm: document.getElementById('adminModalConfirm'),
                modalCancel: document.getElementById('adminModalCancel'),
                modalInputWrapper: document.getElementById('adminModalInputWrapper'),
                modalInput: document.getElementById('adminModalInput'),
                icons: {
                    success: document.getElementById('iconSuccess'),
                    error: document.getElementById('iconError'),
                    warning: document.getElementById('iconWarning'),
                    info: document.getElementById('iconInfo'),
                    confirm: document.getElementById('iconConfirm') || document.getElementById('iconInfo')
                }
            };
        }

        function showModal(options) {
            const els = getElements();
            if (!els.modal) return Promise.resolve(false);

            const { type, title, message, showCancel, confirmText, cancelText, mode, input: inputOptions } = options;
            window._adminModalState.currentMode = mode || "alert";

            if (els.modalTitle) els.modalTitle.textContent = title || "";
            if (els.modalMessage) els.modalMessage.textContent = message || "";
            if (els.modalConfirm) els.modalConfirm.textContent = confirmText || "确定";
            if (els.modalCancel) {
                els.modalCancel.textContent = cancelText || "取消";
                els.modalCancel.classList.toggle('hidden', !showCancel);
            }

            if (mode === "prompt" && els.modalInputWrapper && els.modalInput) {
                els.modalInputWrapper.classList.remove('hidden');
                els.modalInput.type = inputOptions.type || "text";
                els.modalInput.placeholder = inputOptions.placeholder || "";
                els.modalInput.value = inputOptions.value || "";
            } else if (els.modalInputWrapper && els.modalInput) {
                els.modalInputWrapper.classList.add('hidden');
                els.modalInput.value = "";
            }

            Object.keys(els.icons).forEach(key => {
                if (els.icons[key]) els.icons[key].classList.add('hidden');
            });
            if (els.icons[type] && els.modalIcon) {
                els.icons[type].classList.remove('hidden');
                els.modalIcon.className = 'w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center ' + (iconBgMap[type] || iconBgMap.info);
            }

            els.modal.classList.remove('hidden');
            els.modal.classList.add('flex');

            setTimeout(() => {
                els.modalContent.classList.remove('scale-95', 'opacity-0');
                els.modalContent.classList.add('scale-100', 'opacity-100');
                if (mode === "prompt" && els.modalInput) {
                    els.modalInput.focus();
                    els.modalInput.select();
                }
            }, 10);

            return new Promise(resolve => {
                window._adminModalState.resolveCallback = resolve;
            });
        }

        function hideModal(result) {
            const els = getElements();
            if (!els.modal || !els.modalContent) return;

            els.modalContent.classList.remove('scale-100', 'opacity-100');
            els.modalContent.classList.add('scale-95', 'opacity-0');

            setTimeout(() => {
                els.modal.classList.add('hidden');
                els.modal.classList.remove('flex');
                if (window._adminModalState.resolveCallback) {
                    let finalResult = result;
                    if (window._adminModalState.currentMode === "prompt") {
                        finalResult = result ? (els.modalInput ? els.modalInput.value : "") : null;
                    }
                    window._adminModalState.resolveCallback(finalResult);
                    window._adminModalState.resolveCallback = null;
                }
                window._adminModalState.currentMode = "alert";
            }, 200);
        }

        if (!window._adminModalEventsInitialized) {
            window._adminModalEventsInitialized = true;
            document.addEventListener('click', e => {
                const target = e.target;
                if (target.id === 'adminModalConfirm' || target.closest('#adminModalConfirm')) hideModal(true);
                else if (target.id === 'adminModalCancel' || target.closest('#adminModalCancel')) hideModal(false);
                else if (target.id === 'adminModal') hideModal(false);
            });
            document.addEventListener('keydown', e => {
                if (e.key === 'Enter' && e.target.id === 'adminModalInput') {
                    e.preventDefault();
                    hideModal(true);
                }
            });
        }

        window.adminAlert = (message, type, title) => showModal({
            type: type || 'info',
            title: title || (type === 'success' ? '成功' : type === 'error' ? '错误' : '提示'),
            message: message,
            showCancel: false,
            mode: "alert"
        });

        window.adminConfirm = (message, title) => showModal({
            type: 'confirm',
            title: title || '确认操作',
            message: message,
            showCancel: true,
            confirmText: '确定',
            cancelText: '取消',
            mode: "confirm"
        });

        window.adminPrompt = (message, options) => {
            const opts = options || {};
            return showModal({
                type: opts.type || 'info',
                title: opts.title || '请输入',
                message: message || '',
                showCancel: true,
                confirmText: opts.confirmText || '确定',
                cancelText: opts.cancelText || '取消',
                mode: "prompt",
                input: {
                    type: opts.inputType || "text",
                    placeholder: opts.placeholder || "",
                    value: opts.defaultValue || ""
                }
            });
        };

        window.showAdminAlert = (message, type, title) => window.adminAlert ? window.adminAlert(message, type, title) : (console.warn(message), Promise.resolve());
        window.showAdminConfirm = (message, title) => window.adminConfirm ? window.adminConfirm(message, title) : (console.warn(message), Promise.resolve(false));
        window.showAdminPrompt = (message, options) => window.adminPrompt ? window.adminPrompt(message, options) : (console.warn(message), Promise.resolve(null));
    })();

    // ============== 主体逻辑 (Theme, Sidebar, Dropdown) ==============
    function setupUI() {
        // --- Theme Color Picker ---
        (function initThemePicker() {
            const btn = document.getElementById('themeColorBtn');
            const dropdown = document.getElementById('themePickerDropdown');
            const slider = document.getElementById('headerHueSlider');
            const thumb = document.getElementById('sliderThumb');
            const display = document.getElementById('currentHueDisplay');
            const resetBtn = document.getElementById('resetThemeBtn');
            const defaultHue = "165";

            const updateThumb = (val) => {
                if (thumb) thumb.style.left = (val / 360 * 100) + '%';
                if (display) display.textContent = val;
            };

            const updateResetState = (val) => {
                if (!resetBtn) return;
                const isDefault = String(val) === defaultHue;
                resetBtn.classList.toggle('hidden', isDefault);
            };

            const updateTheme = (val) => {
                const hue = String(val);
                document.documentElement.style.setProperty('--hue', hue);
                document.documentElement.style.setProperty('--configHue', hue);
                document.documentElement.style.setProperty('--primary', `oklch(0.70 0.14 ${hue})`);
                document.documentElement.style.setProperty('--primary-light', `oklch(0.75 0.14 ${hue})`);
                document.documentElement.style.setProperty('--primary-dark', `oklch(0.65 0.14 ${hue})`);
                document.documentElement.style.setProperty('--page-bg', `oklch(0.97 0.012 ${hue})`);
                document.documentElement.style.setProperty('--page-bg-dark', `oklch(0.16 0.015 ${hue})`);
                document.documentElement.style.setProperty('--sidebar-bg', `oklch(0.98 0.008 ${hue})`);
                document.documentElement.style.setProperty('--sidebar-bg-dark', `oklch(0.18 0.012 ${hue})`);
                document.documentElement.style.setProperty('--btn-bg', `oklch(0.95 0.025 ${hue})`);
                document.documentElement.style.setProperty('--btn-bg-hover', `oklch(0.9 0.05 ${hue})`);
                document.documentElement.style.setProperty('--btn-bg-dark', `oklch(0.33 0.035 ${hue})`);
                document.documentElement.style.setProperty('--btn-bg-hover-dark', `oklch(0.38 0.04 ${hue})`);
                updateResetState(hue);
            };

            let saveTimeout;
            const saveTheme = (val) => {
                const hue = String(val);
                localStorage.setItem('hue', hue);
                if (saveTimeout) clearTimeout(saveTimeout);
                saveTimeout = setTimeout(async () => {
                    const API_URL = window.API_URL;
                    if (!API_URL) return;
                    try {
                        await window.adminRequest(`${API_URL}/settings/by-key/theme_hue`, {
                            method: 'PUT',
                            body: JSON.stringify({ value: hue })
                        });
                    } catch (e) { console.error("Failed to save theme hue", e); }
                }, 500);
            };

            const stored = localStorage.getItem('hue');
            if (stored) updateTheme(stored);
            else {
                const style = getComputedStyle(document.documentElement);
                const currentHue = style.getPropertyValue('--hue').trim() || defaultHue;
                updateResetState(currentHue);
            }

            if (btn && dropdown) {
                btn.onclick = (e) => {
                    e.stopPropagation();
                    const isHidden = dropdown.classList.toggle('hidden');
                    if (!isHidden) {
                        const style = getComputedStyle(document.documentElement);
                        const hue = style.getPropertyValue('--hue').trim() || defaultHue;
                        if (slider) { slider.value = hue; updateThumb(hue); }
                    }
                };
                document.addEventListener('click', (e) => {
                    if (!dropdown.contains(e.target) && !btn.contains(e.target)) dropdown.classList.add('hidden');
                });
            }

            slider?.addEventListener('input', (e) => {
                const h = e.target.value;
                updateThumb(h);
                updateTheme(h);
                saveTheme(h);
            });

            resetBtn?.addEventListener('click', () => {
                updateThumb(defaultHue);
                updateTheme(defaultHue);
                saveTheme(defaultHue);
                if (slider) slider.value = defaultHue;
            });
        })();

        // --- Custom Color Pickers ---
        function initColorPickers() {
            const presetHues = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330];
            const hueToHex = (hue) => {
                const h = hue / 360, s = 0.7, l = 0.6;
                const hue2rgb = (p, q, t) => {
                    if (t < 0) t += 1; if (t > 1) t -= 1;
                    if (t < 1 / 6) return p + (q - p) * 6 * t;
                    if (t < 1 / 2) return q;
                    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
                    return p;
                };
                const q = l < 0.5 ? l * (1 + s) : l + s - l * s, p = 2 * l - q;
                const r = Math.round(hue2rgb(p, q, h + 1 / 3) * 255);
                const g = Math.round(hue2rgb(p, q, h) * 255);
                const b = Math.round(hue2rgb(p, q, h - 1 / 3) * 255);
                return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
            };
            const hexToHue = (hex) => {
                const r = parseInt(hex.slice(1, 3), 16) / 255, g = parseInt(hex.slice(3, 5), 16) / 255, b = parseInt(hex.slice(5, 7), 16) / 255;
                const max = Math.max(r, g, b), min = Math.min(r, g, b);
                let h = 0;
                if (max !== min) {
                    const d = max - min;
                    switch (max) {
                        case r: h = (g - b) / d + (g < b ? 6 : 0); break;
                        case g: h = (b - r) / d + 2; break;
                        case b: h = (r - g) / d + 4; break;
                    }
                    h /= 6;
                }
                return Math.round(h * 360);
            };

            document.querySelectorAll('input[type="color"]').forEach(input => {
                if (input.dataset.colorPickerInit) return;
                input.dataset.colorPickerInit = 'true';
                input.style.display = 'none';

                const wrapper = document.createElement('div');
                wrapper.className = 'color-picker-wrapper';
                input.parentNode.insertBefore(wrapper, input);
                wrapper.appendChild(input);

                const preview = document.createElement('div');
                preview.className = 'color-picker-preview';
                preview.innerHTML = `<div class="color-picker-swatch" style="background-color: ${input.value}"></div><span class="color-picker-value">${input.value.toUpperCase()}</span>`;
                wrapper.appendChild(preview);

                const dropdown = document.createElement('div');
                dropdown.className = 'color-picker-dropdown';
                dropdown.innerHTML = `
                    <div class="color-picker-slider-container">
                        <div class="color-picker-gradient"></div>
                        <input type="range" class="color-picker-slider" min="0" max="360" step="5" value="${hexToHue(input.value)}">
                        <div class="color-picker-thumb" style="left: ${hexToHue(input.value) / 360 * 100}%"></div>
                    </div>
                    <div class="color-picker-presets">
                        ${presetHues.map(h => `<div class="color-picker-preset" style="background-color: ${hueToHex(h)}" data-hue="${h}"></div>`).join('')}
                    </div>
                `;
                wrapper.appendChild(dropdown);

                const swatch = preview.querySelector('.color-picker-swatch');
                const valueDisplay = preview.querySelector('.color-picker-value');
                const slider = dropdown.querySelector('.color-picker-slider');
                const thumb = dropdown.querySelector('.color-picker-thumb');

                const update = (h) => {
                    const hex = hueToHex(h);
                    input.value = hex;
                    swatch.style.backgroundColor = hex;
                    valueDisplay.textContent = hex.toUpperCase();
                    thumb.style.left = (h / 360 * 100) + '%';
                    slider.value = h;
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                };

                preview.onclick = (e) => { e.stopPropagation(); dropdown.classList.toggle('open'); };
                slider.oninput = (e) => update(parseInt(e.target.value));
                dropdown.onclick = (e) => { if (e.target.classList.contains('color-picker-preset')) update(parseInt(e.target.dataset.hue)); };
                document.addEventListener('click', (e) => { if (!wrapper.contains(e.target)) dropdown.classList.remove('open'); });
            });
        }
        initColorPickers();
        window.initColorPickers = initColorPickers;

        // --- Change Password ---
        (function initChangePassword() {
            const cpBtn = document.getElementById('changePasswordBtn');
            const cpModal = document.getElementById('changePwModal');
            const cpContent = document.getElementById('changePwModalContent');
            const cpForm = document.getElementById('globalChangePasswordForm');

            const openModal = () => {
                document.getElementById('userDropdownMenu')?.classList.add('hidden');
                if (cpModal && cpContent) {
                    cpModal.classList.replace('hidden', 'flex');
                    setTimeout(() => cpContent.classList.replace('opacity-0', 'opacity-100'), 10);
                    setTimeout(() => cpContent.classList.replace('scale-95', 'scale-100'), 10);
                }
            };
            const closeModal = () => {
                if (cpModal && cpContent) {
                    cpContent.classList.replace('opacity-100', 'opacity-0');
                    cpContent.classList.replace('scale-100', 'scale-95');
                    setTimeout(() => { cpModal.classList.replace('flex', 'hidden'); cpForm?.reset(); }, 200);
                }
            };

            cpBtn?.addEventListener('click', openModal);
            document.getElementById('closeChangePwBtn')?.addEventListener('click', closeModal);
            document.getElementById('cancelChangePwBtn')?.addEventListener('click', closeModal);
            cpModal?.addEventListener('click', (e) => { if (e.target === cpModal) closeModal(); });

            document.querySelectorAll('.admin-password-toggle').forEach(btn => {
                btn.onclick = (e) => {
                    e.preventDefault();
                    const input = document.getElementById(btn.dataset.target);
                    if (!input) return;
                    const isPw = input.type === 'password';
                    input.type = isPw ? 'text' : 'password';
                    btn.querySelector('.eye-open')?.classList.toggle('hidden', isPw);
                    btn.querySelector('.eye-closed')?.classList.toggle('hidden', !isPw);
                };
            });

            cpForm?.addEventListener('submit', async (e) => {
                e.preventDefault();
                const current = document.getElementById('globalCurrentPassword').value;
                const newPw = document.getElementById('globalNewPassword').value;
                const confirmPw = document.getElementById('globalConfirmPassword').value;

                if (newPw.length < 6) return window.showAdminAlert?.('新密码长度至少6位', 'warning');
                if (newPw !== confirmPw) return window.showAdminAlert?.('两次输入密码不一致', 'warning');

                try {
                    const result = await window.adminRequest(`${window.API_URL}/auth/change-password`, {
                        method: 'POST',
                        body: JSON.stringify({ old_password: current, new_password: newPw, new_password_confirm: confirmPw })
                    });
                    if (result.ok) {
                        await window.showAdminAlert?.('密码修改成功，请重新登录', 'success');
                        localStorage.removeItem('adminToken');
                        window.location.href = '/admin/login';
                    } else {
                        window.showAdminAlert?.(result.msg || '修改失败', 'error');
                    }
                } catch (e) { window.showAdminAlert?.('网络错误', 'error'); }
            });
        })();

        // ============== Theme initialization ==============
        const LIGHT_MODE = 'LIGHT_MODE', DARK_MODE = 'DARK_MODE', SYSTEM_MODE = 'SYSTEM_MODE';
        const iconLight = document.getElementById('iconLight'), iconDark = document.getElementById('iconDark'), iconSystem = document.getElementById('iconSystem');

        function updateThemeIcon(mode) {
            [iconLight, iconDark, iconSystem].forEach(i => i?.classList.add('hidden'));
            if (mode === LIGHT_MODE) iconLight?.classList.remove('hidden');
            else if (mode === DARK_MODE) iconDark?.classList.remove('hidden');
            else iconSystem?.classList.remove('hidden');
        }

        function applyTheme(isDark) {
            document.documentElement.classList.toggle("dark", isDark);
            document.documentElement.setAttribute('data-theme', isDark ? 'github-dark' : 'github-light');
        }

        const getSystemPreference = () => window.matchMedia("(prefers-color-scheme: dark)").matches;
        const savedTheme = localStorage.getItem("theme") || SYSTEM_MODE;
        applyTheme(savedTheme === DARK_MODE || (savedTheme === SYSTEM_MODE && getSystemPreference()));
        updateThemeIcon(savedTheme);

        document.getElementById("themeToggle")?.addEventListener("click", () => {
            const current = localStorage.getItem("theme") || SYSTEM_MODE;
            let next, isDark;
            if (current === LIGHT_MODE) { next = DARK_MODE; isDark = true; }
            else if (current === DARK_MODE) { next = SYSTEM_MODE; isDark = getSystemPreference(); }
            else { next = LIGHT_MODE; isDark = false; }
            localStorage.setItem("theme", next);
            applyTheme(isDark);
            updateThemeIcon(next);
        });

        const sidebar = document.getElementById("sidebar"), overlay = document.getElementById("sidebarOverlay");
        document.getElementById("menuToggle")?.addEventListener('click', () => { sidebar?.classList.remove("-translate-x-full"); overlay?.classList.remove("hidden"); });
        overlay?.addEventListener('click', () => { sidebar?.classList.add("-translate-x-full"); overlay?.classList.add("hidden"); });

        const collapseBtn = document.getElementById("sidebarCollapseBtn");
        const updateCollapseIcon = (c) => {
            collapseBtn?.querySelector(".collapse-icon-left")?.classList.toggle("hidden", c);
            collapseBtn?.querySelector(".collapse-icon-right")?.classList.toggle("hidden", !c);
        };
        const isCollapsed = localStorage.getItem("sidebarCollapsed") === "true";
        if (isCollapsed && sidebar) { sidebar.classList.add("collapsed"); updateCollapseIcon(true); }

        collapseBtn?.addEventListener('click', () => {
            if (!sidebar) return;
            const c = sidebar.classList.toggle("collapsed");
            localStorage.setItem("sidebarCollapsed", c.toString());
            updateCollapseIcon(c);
        });

        const userDropdownBtn = document.getElementById("userDropdownBtn"), userDropdownMenu = document.getElementById("userDropdownMenu");
        if (userDropdownBtn && userDropdownMenu) {
            userDropdownBtn.onclick = (e) => {
                e.stopPropagation();
                if (userDropdownMenu.classList.toggle("hidden")) {
                    userDropdownMenu.classList.add("opacity-0", "scale-95");
                } else {
                    setTimeout(() => userDropdownMenu.classList.remove("opacity-0", "scale-95"), 10);
                }
            };
            document.addEventListener("click", (e) => {
                if (!document.getElementById("userDropdownContainer")?.contains(e.target)) {
                    userDropdownMenu.classList.add("opacity-0", "scale-95");
                    setTimeout(() => userDropdownMenu.classList.add("hidden"), 200);
                }
            });
        }

        document.getElementById("logoutBtn")?.addEventListener("click", () => {
            ['adminToken', 'admin_username', 'admin_avatar'].forEach(k => localStorage.removeItem(k));
            window.location.href = "/admin/login";
        });

        (function loadUserInfo() {
            const token = localStorage.getItem("adminToken");
            const name = localStorage.getItem('admin_username'), avatar = localStorage.getItem('admin_avatar');
            if (name) {
                if (document.getElementById("usernameDisplay")) document.getElementById("usernameDisplay").textContent = name;
                if (document.getElementById("dropdownUsername")) document.getElementById("dropdownUsername").textContent = name;
            }
            if (!token) return;
            try {
                const decoded = JSON.parse(atob(token.split('.')[1]));
                const username = decoded.sub || "管理员";
                if (document.getElementById("usernameDisplay")) document.getElementById("usernameDisplay").textContent = username;
                localStorage.setItem('admin_username', username);
            } catch (e) { }

            if (window.API_URL && window.adminRequest) {
                window.adminRequest(`${window.API_URL}/settings`).then(res => {
                    if (!res.ok) return;
                    const avatarVal = res.data?.find(s => ['profile_avatar', 'avatar', 'site_avatar'].includes(s.key))?.value;
                    if (avatarVal && avatarVal !== avatar) {
                        const container = document.getElementById("userAvatarContainer"), def = document.getElementById("defaultAvatarIcon");
                        if (container && def) {
                            const img = document.createElement('img'); img.src = avatarVal; img.className = "w-full h-full object-cover";
                            img.onload = () => { def.style.display = 'none'; container.querySelector('img')?.remove(); container.appendChild(img); localStorage.setItem('admin_avatar', avatarVal); };
                        }
                    }
                }).catch(() => { });
            }
        })();
    }

    const updateBannerExtend = () => {
        let offset = Math.floor(window.innerHeight * 0.3);
        offset = offset - (offset % 4);
        document.documentElement.style.setProperty("--banner-height-extend", `${offset}px`);
    };
    updateBannerExtend();
    window.addEventListener('resize', updateBannerExtend);

    setupUI();
    document.addEventListener('astro:page-load', setupUI);
}
