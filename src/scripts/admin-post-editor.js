/**
 * 后台文章编辑器逻辑
 * 封装文章创建和编辑的所有交互
 */
import { initVditor, destroyVditor } from './admin-editor';
import flatpickr from 'flatpickr';
import { Chinese } from 'flatpickr/dist/l10n/zh.js';
import 'flatpickr/dist/flatpickr.min.css';

export function initPostEditor(postId = null) {
    const API_URL = window.API_URL;
    const t = window.adminI18n || window.editI18n || {};

    // State
    let vditor = null;
    let postStatus = "draft";
    let isPinned = false;
    let selectedTagIds = [];
    let allTags = [];
    let allCategories = [];
    let selectedCategory = '';

    // Elements
    const elements = {
        title: document.getElementById("title"),
        slug: document.getElementById("slug"),
        category: document.getElementById("category"),
        selectedTags: document.getElementById("selectedTags"),
        description: document.getElementById("description"),
        image: document.getElementById("image"),
        imagePreview: document.getElementById("imagePreview"),
        password: document.getElementById("password"),
        passwordToggle: document.getElementById("password-toggle"),
        pinnedToggle: document.getElementById("pinnedToggle"),
        pinnedToggleTrack: document.getElementById("pinnedToggleTrack"),
        pinnedToggleHandle: document.getElementById("pinnedToggleHandle"),
        pinOrderContainer: document.getElementById("pinOrderContainer"),
        pinOrder: document.getElementById("pinOrder"),
        statusSelect: document.getElementById("statusSelect"),
        statusValue: document.getElementById("statusValue"),
        scheduledWrapper: document.getElementById("scheduledWrapper"),
        scheduledAt: document.getElementById("scheduledAt"),
        publishedAt: document.getElementById("publishedAt"),
        saveBtn: document.getElementById("saveBtn"),
        backBtn: document.querySelector('[data-admin-back="posts"]'),
        categorySelector: document.getElementById('categorySelector'),
        tagsContainer: document.getElementById('tagsContainer'),
    };

    // --- Utilities ---
    const convertLocalToISO = (value) => {
        if (!value) return null;
        const date = new Date(value);
        return isNaN(date.getTime()) ? null : date.toISOString();
    };

    const formatDatetimeForInput = (value) => {
        if (!value) return "";
        const date = new Date(value);
        if (isNaN(date.getTime())) return "";
        const tzOffset = date.getTimezoneOffset() * 60000;
        return new Date(date.getTime() - tzOffset).toISOString().slice(0, 16);
    };

    // --- Media Picker ---
    const setupMediaPicker = () => {
        const modal = document.getElementById("mediaPickerModal");
        if (!modal || modal.dataset.bound === "true") return;
        modal.dataset.bound = "true";

        const openCoverBtn = document.getElementById("openCoverPicker");
        const openEditorBtn = document.getElementById("openEditorImagePicker");
        const closeBtn = document.getElementById("mediaPickerClose");
        const grid = document.getElementById("mediaPickerGrid");
        const countEl = document.getElementById("mediaPickerCount");
        const prevBtn = document.getElementById("mediaPickerPrev");
        const nextBtn = document.getElementById("mediaPickerNext");
        const pageEl = document.getElementById("mediaPickerPage");
        const searchInput = document.getElementById("mediaPickerSearch");

        let pickerMode = "cover";
        let currentPage = 1;
        let totalPages = 1;
        let keyword = "";
        let searchTimer = null;

        const loadMedia = async () => {
            if (!grid) return;
            grid.innerHTML = '<div class="col-span-full text-center text-sm text-zinc-500 py-10">加载中...</div>';
            try {
                let url = `${API_URL}/upload/media?page=${currentPage}&page_size=40`;
                if (keyword) url += `&keyword=${encodeURIComponent(keyword)}`;

                const result = await window.adminRequest(url);
                if (!result.ok) throw new Error(result.msg || "加载失败");

                const data = result.data || {};
                const items = (data.items || []).filter(item => {
                    if (item.mime_type && item.mime_type.startsWith("image/")) return true;
                    const ext = (item.filename || "").toLowerCase().split(".").pop();
                    return ["jpg", "jpeg", "png", "gif", "webp", "svg"].includes(ext);
                });

                if (countEl) countEl.textContent = `共 ${data.pagination?.total || items.length} 张图片`;
                if (pageEl) pageEl.textContent = `${currentPage}/${data.pagination?.total_pages || 1}`;
                if (prevBtn) prevBtn.disabled = currentPage <= 1;
                if (nextBtn) nextBtn.disabled = currentPage >= (data.pagination?.total_pages || 1);
                totalPages = data.pagination?.total_pages || 1;

                if (items.length === 0) {
                    grid.innerHTML = '<div class="col-span-full text-center text-sm text-zinc-500 py-10">暂无图片</div>';
                    return;
                }

                grid.innerHTML = items.map(item => `
                    <button type="button" class="group text-left rounded-xl border border-zinc-200 dark:border-zinc-800 overflow-hidden bg-white dark:bg-zinc-900 media-card-hover transition-all" data-url="${item.url}" data-name="${item.original_name || item.filename || 'image'}">
                        <div class="aspect-square bg-zinc-100 dark:bg-zinc-800 overflow-hidden">
                            <img src="${item.url}" alt="${item.filename}" loading="lazy" class="w-full h-full object-cover group-hover:scale-105 transition-transform" />
                        </div>
                        <div class="px-2 py-1.5 text-xs text-zinc-600 dark:text-zinc-300 truncate">${item.original_name || item.filename}</div>
                    </button>
                `).join("");

                grid.querySelectorAll("button[data-url]").forEach(btn => {
                    btn.addEventListener("click", () => {
                        const { url, name } = btn.dataset;
                        if (pickerMode === "cover") {
                            if (elements.image) {
                                elements.image.value = url;
                                elements.image.dispatchEvent(new Event("input"));
                            }
                        } else if (vditor) {
                            vditor.insertValue(`![${(name || 'image').replace(/\]/g, '\\]')}](${url})`);
                        }
                        modal.classList.add("hidden");
                        modal.classList.remove("flex");
                    });
                });
            } catch (err) {
                console.error("加载媒体失败:", err);
                grid.innerHTML = '<div class="col-span-full text-center text-sm text-red-500 py-10">加载失败</div>';
            }
        };

        const openPicker = (mode) => {
            pickerMode = mode;
            currentPage = 1;
            keyword = "";
            if (searchInput) searchInput.value = "";
            modal.classList.remove("hidden");
            modal.classList.add("flex");
            loadMedia();
        };

        openCoverBtn?.addEventListener("click", () => openPicker("cover"));
        openEditorBtn?.addEventListener("click", () => openPicker("editor"));
        closeBtn?.addEventListener("click", () => {
            modal.classList.add("hidden");
            modal.classList.remove("flex");
        });

        searchInput?.addEventListener("input", () => {
            keyword = searchInput.value.trim();
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                currentPage = 1;
                loadMedia();
            }, 300);
        });

        prevBtn?.addEventListener("click", () => { if (currentPage > 1) { currentPage--; loadMedia(); } });
        nextBtn?.addEventListener("click", () => { if (currentPage < totalPages) { currentPage++; loadMedia(); } });
    };

    // --- UI Helpers ---
    const updateStatusUI = (value) => {
        postStatus = value;
        if (elements.scheduledWrapper) {
            elements.scheduledWrapper.classList.toggle("hidden", value !== "scheduled");
        }
        if (elements.statusValue) {
            const option = document.querySelector(`.custom-select-option[data-value="${value}"]`);
            if (option) {
                elements.statusValue.textContent = option.querySelector('.custom-select-option-name')?.textContent || value;
            }
        }
        if (elements.statusSelect) elements.statusSelect.value = value;
    };

    const updatePinnedUI = (active) => {
        isPinned = active;
        elements.pinnedToggle?.setAttribute("aria-pressed", active ? "true" : "false");
        elements.pinnedToggleTrack?.classList.toggle("is-active", active);
        elements.pinnedToggleHandle?.classList.toggle("translate-x-4", active);
        elements.pinOrderContainer?.classList.toggle("hidden", !active);
    };

    const renderTags = () => {
        if (!elements.tagsContainer) return;
        if (allTags.length === 0) {
            elements.tagsContainer.innerHTML = '<span class="text-sm text-zinc-400">暂无可用标签</span>';
            return;
        }

        elements.tagsContainer.innerHTML = allTags.filter(t => t.enabled).map(tag => {
            const isSelected = selectedTagIds.includes(tag.id);
            const style = isSelected
                ? `background-color: ${tag.color || '#6366f1'}; color: #fff; border-color: ${tag.color || '#6366f1'}`
                : `background-color: transparent; color: ${tag.color || '#71717a'}; border-color: ${tag.color || '#d4d4d8'}`;
            return `<button type="button" class="tag-btn px-3 py-1.5 text-xs font-medium rounded-full border transition-all hover:opacity-80" data-tag-id="${tag.id}" data-tag-color="${tag.color || '#6366f1'}" style="${style}">${tag.name}</button>`;
        }).join('');

        elements.tagsContainer.querySelectorAll('.tag-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.dataset.tagId;
                const idx = selectedTagIds.indexOf(id);
                if (idx === -1) {
                    selectedTagIds.push(id);
                } else {
                    selectedTagIds.splice(idx, 1);
                }
                renderTags();
                if (elements.selectedTags) {
                    elements.selectedTags.value = selectedTagIds.map(sid => allTags.find(t => t.id === sid)?.name).filter(Boolean).join(',');
                }
            });
        });
    };

    const renderCategoryOptions = (filter = '') => {
        const container = document.getElementById('categoryOptions');
        if (!container) return;

        const filtered = filter ? allCategories.filter(c => c.name.toLowerCase().includes(filter.toLowerCase())) : allCategories;
        if (filtered.length === 0) {
            container.innerHTML = `<div class="custom-select-empty">${filter ? '未找到匹配的分类' : '暂无分类'}</div>`;
            return;
        }

        container.innerHTML = filtered.map(cat => {
            const isSelected = selectedCategory === cat.name;
            return `
                <div class="custom-select-option${isSelected ? ' selected' : ''}" data-value="${cat.name}">
                    <span class="custom-select-option-name">${cat.name}</span>
                    <svg xmlns="http://www.w3.org/2000/svg" class="custom-select-option-check" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                </div>
            `;
        }).join('');

        container.querySelectorAll('.custom-select-option').forEach(option => {
            option.addEventListener('click', () => {
                const val = option.dataset.value;
                selectedCategory = val;
                if (elements.category) elements.category.value = val;
                const valDisplay = document.getElementById('categoryValue');
                if (valDisplay) {
                    valDisplay.textContent = val || valDisplay.dataset.placeholder;
                    valDisplay.classList.toggle('placeholder', !val);
                }
                document.getElementById('categorySelector')?.classList.remove('open');
                document.getElementById('categoryDropdown')?.classList.add('hidden');
                renderCategoryOptions();
            });
        });
    };

    const setupDatePickers = () => {
        const config = {
            enableTime: true,
            dateFormat: "Y-m-d H:i",
            time_24hr: true,
            locale: Chinese,
            allowInput: true,
            disableMobile: true
        };

        if (elements.publishedAt) flatpickr(elements.publishedAt, config);
        if (elements.scheduledAt) flatpickr(elements.scheduledAt, config);

        // Date Shortcuts
        document.querySelectorAll('.shortcut-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const targetId = btn.dataset.target;
                const action = btn.dataset.action;
                const input = document.getElementById(targetId);
                if (!input) return;

                const fp = input._flatpickr;
                if (!fp) return;

                const now = new Date();
                if (action === 'now') fp.setDate(now);
                else if (action === 'tomorrow') {
                    const tomorrow = new Date();
                    tomorrow.setDate(tomorrow.getDate() + 1);
                    tomorrow.setHours(9, 0, 0, 0);
                    fp.setDate(tomorrow);
                } else if (action === 'week') {
                    const week = new Date();
                    week.setDate(week.getDate() + 7);
                    week.setHours(9, 0, 0, 0);
                    fp.setDate(week);
                } else if (action === 'clear') fp.clear();
            });
        });
    };

    const AUTOSAVE_INTERVAL = 60000; // 1 minute
    let autosaveTimer = null;
    let lastAutosaveSignature = '';
    let cachedAutosavePayload = null;
    let cachedAutosaveTime = null;

    // Elements extensions
    elements.autosaveNotice = document.getElementById("autosaveNotice");
    elements.autosaveStatus = document.getElementById("autosaveStatus");
    elements.loadAutosaveBtn = document.getElementById("loadAutosaveBtn");
    elements.discardAutosaveBtn = document.getElementById("discardAutosaveBtn");
    elements.revisionList = document.getElementById("revisionList");

    // --- Autosave Logics ---
    const updateAutosaveStatus = (savedAt) => {
        if (!elements.autosaveStatus) return;
        if (!savedAt) {
            elements.autosaveStatus.textContent = "";
            return;
        }
        const date = new Date(savedAt);
        elements.autosaveStatus.textContent = "最后自动保存：" + date.toLocaleString();
    };

    const showAutosaveNotice = (savedAt) => {
        elements.autosaveNotice?.classList.remove("hidden");
        updateAutosaveStatus(savedAt || cachedAutosaveTime);
    };

    const hideAutosaveNotice = () => {
        elements.autosaveNotice?.classList.add("hidden");
        updateAutosaveStatus(null);
        cachedAutosavePayload = null;
        cachedAutosaveTime = null;
    };

    const fetchAutosaveData = async (pid) => {
        try {
            const result = await window.adminRequest(`${API_URL}/posts/${pid}/autosave`);
            if (result.ok && result.data && result.data.data) {
                cachedAutosavePayload = result.data.data;
                cachedAutosaveTime = result.data.saved_at;
                showAutosaveNotice(result.data.saved_at);
            } else {
                hideAutosaveNotice();
            }
        } catch (err) {
            console.error("加载自动保存内容失败:", err);
        }
    };

    const applyAutosavePayload = (payload) => {
        if (!payload) return;
        if (elements.title) elements.title.value = payload.title || "";
        if (elements.slug) elements.slug.value = payload.slug || "";
        if (elements.description) elements.description.value = payload.description || "";
        if (elements.image) {
            elements.image.value = payload.image || "";
            elements.image.dispatchEvent(new Event('input'));
        }
        if (elements.password) elements.password.value = payload.password || "";

        if (payload.category_name) {
            selectedCategory = payload.category_name;
            renderCategoryOptions();
        }
        if (payload.tags && payload.tags.length) {
            // Need to map names back to IDs if possible
            selectedTagIds = payload.tags.map(tagName => allTags.find(t => t.name === tagName)?.id).filter(Boolean);
            renderTags();
        }
        if (payload.content && vditor) {
            vditor.setValue(payload.content);
        }
    };

    const autosaveDraft = async (pid) => {
        if (!pid || !vditor) return;
        const content = vditor.getValue();
        if (!content) return;

        const payload = {
            title: elements.title?.value || "",
            slug: elements.slug?.value || "",
            category_name: elements.category?.value || "General",
            tags: elements.selectedTags?.value ? elements.selectedTags.value.split(',').map(t => t.trim()).filter(Boolean) : [],
            description: elements.description?.value || "",
            content: content,
            image: elements.image?.value || "",
            password: elements.password?.value || "",
            pinned: isPinned,
            pin_order: parseInt(elements.pinOrder?.value || 0),
        };

        const signature = JSON.stringify({
            title: payload.title,
            slug: payload.slug,
            description: payload.description,
            content: payload.content,
            category: payload.category_name,
            tags: payload.tags.join(",")
        });

        if (signature === lastAutosaveSignature) return;

        try {
            const result = await window.adminRequest(`${API_URL}/posts/${pid}/autosave`, {
                method: "POST",
                body: JSON.stringify(payload)
            });
            if (result.ok && result.data) {
                lastAutosaveSignature = signature;
                cachedAutosaveTime = result.data.saved_at;
                showAutosaveNotice(result.data.saved_at);
            }
        } catch (err) {
            console.error("自动保存失败:", err);
        }
    };

    const startAutosaveLoop = (pid) => {
        stopAutosaveLoop();
        if (!pid) return;
        autosaveTimer = setInterval(() => autosaveDraft(pid), AUTOSAVE_INTERVAL);
    };

    const stopAutosaveLoop = () => {
        if (autosaveTimer) {
            clearInterval(autosaveTimer);
            autosaveTimer = null;
        }
    };

    // --- Revisions ---
    const loadRevisions = async (pid) => {
        if (!elements.revisionList || !pid) return;
        try {
            const result = await window.adminRequest(`${API_URL}/posts/${pid}/revisions`);
            if (result.ok) {
                const revisions = result.data || [];
                if (!revisions.length) {
                    elements.revisionList.innerHTML = '<p class="text-xs text-zinc-400">暂无历史版本</p>';
                    return;
                }
                elements.revisionList.innerHTML = revisions.map(rev => {
                    const date = new Date(rev.created_at).toLocaleString();
                    return `
                        <div class="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-900/40 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                            <div class="min-w-0">
                                <p class="font-medium text-zinc-800 dark:text-zinc-100 text-sm truncate">${rev.title}</p>
                                <p class="text-[11px] text-zinc-400 truncate">${date}${rev.editor ? ' · ' + rev.editor : ''}</p>
                            </div>
                            <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:shrink-0">
                                <button type="button" class="w-full sm:w-auto px-3 py-1 text-xs rounded-lg border border-zinc-300 text-zinc-600 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800 whitespace-nowrap" data-revision-restore="${rev.id}">恢复</button>
                                <button type="button" class="w-full sm:w-auto px-3 py-1 text-xs rounded-lg border border-rose-300 text-rose-600 hover:bg-rose-50 dark:border-rose-400/40 dark:text-rose-300 dark:hover:bg-rose-900/20 whitespace-nowrap" data-revision-delete="${rev.id}">删除</button>
                            </div>
                        </div>`;
                }).join('');
            } else {
                elements.revisionList.innerHTML = '<p class="text-xs text-red-400">加载版本记录失败</p>';
            }
        } catch (err) {
            console.error("加载版本记录失败:", err);
            elements.revisionList.innerHTML = '<p class="text-xs text-red-400">加载版本记录失败</p>';
        }
    };

    const restoreRevision = async (pid, revisionId) => {
        if (!pid || !revisionId) return;
        try {
            const result = await window.adminRequest(`${API_URL}/posts/${pid}/revisions/${revisionId}/restore`, { method: "POST" });
            if (result.ok) {
                window.showAdminAlert("文章已恢复到选定版本", "success");
                init(); // Re-load data
            } else {
                window.showAdminAlert("恢复失败: " + (result.msg || "未知错误"), "error");
            }
        } catch (err) {
            console.error("恢复版本失败:", err);
            window.showAdminAlert("恢复失败: " + err.message, "error");
        }
    };

    const deleteRevision = async (pid, revisionId) => {
        if (!pid || !revisionId) return;
        const confirmed = await window.showAdminConfirm?.("确定删除该历史版本吗？") || window.confirm("确定删除该历史版本吗？");
        if (!confirmed) return;

        try {
            const result = await window.adminRequest(`${API_URL}/posts/${pid}/revisions/${revisionId}`, { method: "DELETE" });
            if (result.ok) {
                window.showAdminAlert("历史版本已删除", "success");
                loadRevisions(pid);
            } else {
                window.showAdminAlert("删除失败: " + (result.msg || "未知错误"), "error");
            }
        } catch (err) {
            console.error("删除版本失败:", err);
            window.showAdminAlert("删除失败: " + err.message, "error");
        }
    };

    const syncEditorHeaderHeight = () => {
        const header = document.querySelector('[data-editor-header]');
        if (header) {
            const height = header.offsetHeight || 0;
            document.documentElement.style.setProperty('--admin-editor-header-height', height + 'px');
        }
    };

    // --- Init ---
    const init = async () => {
        syncEditorHeaderHeight();
        setupDatePickers();
        setupMediaPicker();

        if (elements.backBtn) {
            elements.backBtn.addEventListener('click', (e) => {
                e.preventDefault();
                if (window.__adminTabManager) window.__adminTabManager.closeCurrentAndNavigate('/admin/posts');
                else window.location.href = '/admin/posts';
            });
        }

        // Title to Slug
        elements.title?.addEventListener('input', (e) => {
            if (elements.slug && !elements.slug.dataset.manual) {
                elements.slug.value = e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
            }
        });
        elements.slug?.addEventListener('input', () => { elements.slug.dataset.manual = "true"; });

        // Image Preview
        elements.image?.addEventListener('input', (e) => {
            const url = e.target.value;
            if (elements.imagePreview) {
                const img = elements.imagePreview.querySelector('img');
                if (url && img) {
                    img.src = url;
                    elements.imagePreview.classList.remove('hidden');
                } else {
                    elements.imagePreview.classList.add('hidden');
                }
            }
        });

        // Password Toggle
        if (elements.passwordToggle && elements.password) {
            const showIcon = elements.passwordToggle.querySelector('[data-eye="show"]');
            const hideIcon = elements.passwordToggle.querySelector('[data-eye="hide"]');
            elements.passwordToggle.addEventListener('click', () => {
                const isVisible = elements.password.type === 'text';
                elements.password.type = isVisible ? 'password' : 'text';
                showIcon?.classList.toggle('hidden', !isVisible);
                hideIcon?.classList.toggle('hidden', isVisible);
            });
        }

        // Pinned Toggle
        elements.pinnedToggle?.addEventListener('click', () => updatePinnedUI(!isPinned));

        // Status Selector
        document.getElementById('statusTrigger')?.addEventListener('click', (e) => {
            e.stopPropagation();
            const open = document.getElementById('statusSelector')?.classList.toggle('open');
            document.getElementById('statusDropdown')?.classList.toggle('hidden', !open);
        });
        document.querySelectorAll('#statusOptions .custom-select-option').forEach(opt => {
            opt.addEventListener('click', () => {
                updateStatusUI(opt.dataset.value);
                document.getElementById('statusSelector')?.classList.remove('open');
                document.getElementById('statusDropdown')?.classList.add('hidden');
            });
        });

        // Category Selector
        document.getElementById('categorySelectorTrigger')?.addEventListener('click', (e) => {
            e.stopPropagation();
            const open = document.getElementById('categorySelector')?.classList.toggle('open');
            document.getElementById('categoryDropdown')?.classList.toggle('hidden', !open);
            if (open) document.getElementById('categorySearch')?.focus();
        });

        const catSearch = document.getElementById('categorySearch');
        if (catSearch) {
            catSearch.addEventListener('input', () => renderCategoryOptions(catSearch.value));
        }

        // Autosave Buttons
        elements.loadAutosaveBtn?.addEventListener('click', () => {
            if (cachedAutosavePayload) {
                applyAutosavePayload(cachedAutosavePayload);
                hideAutosaveNotice();
                window.showAdminAlert("已恢复自动保存内容", "success");
            }
        });
        elements.discardAutosaveBtn?.addEventListener('click', async () => {
            if (!postId) return;
            try {
                await window.adminRequest(`${API_URL}/posts/${postId}/autosave`, { method: "DELETE" });
            } catch (err) { }
            hideAutosaveNotice();
        });

        // Revision Events
        elements.revisionList?.addEventListener('click', (e) => {
            const restoreBtn = e.target.closest('[data-revision-restore]');
            if (restoreBtn) restoreRevision(postId, restoreBtn.dataset.revisionRestore);
            const deleteBtn = e.target.closest('[data-revision-delete]');
            if (deleteBtn) deleteRevision(postId, deleteBtn.dataset.revisionDelete);
        });

        // Load Initial Data
        try {
            const [tagsRes, catsRes] = await Promise.all([
                window.adminRequest(`${API_URL}/tags`),
                window.adminRequest(`${API_URL}/categories`)
            ]);
            if (tagsRes.ok) {
                allTags = tagsRes.data || [];
                renderTags();
            }
            if (catsRes.ok) {
                allCategories = (catsRes.data || []).filter(c => c.enabled);
                renderCategoryOptions();
            }

            if (postId) {
                const postRes = await window.adminRequest(`${API_URL}/posts/${postId}`);
                if (postRes.ok) {
                    const post = postRes.data;
                    if (elements.title) elements.title.value = post.title || '';
                    if (elements.slug) elements.slug.value = post.slug || '';
                    if (elements.description) elements.description.value = post.description || '';
                    if (elements.image) {
                        elements.image.value = post.image || '';
                        elements.image.dispatchEvent(new Event('input'));
                    }
                    if (elements.password) elements.password.value = post.password || '';
                    if (elements.pinOrder) elements.pinOrder.value = post.pin_order || 0;

                    updateStatusUI(post.status || (post.is_draft ? 'draft' : 'published'));
                    updatePinnedUI(post.pinned || false);

                    selectedCategory = post.category || '';
                    if (elements.category) elements.category.value = selectedCategory;
                    const valDisplay = document.getElementById('categoryValue');
                    if (valDisplay) {
                        valDisplay.textContent = selectedCategory || valDisplay.dataset.placeholder;
                        valDisplay.classList.toggle('placeholder', !selectedCategory);
                    }

                    if (post.tags) {
                        selectedTagIds = post.tags.map(tagName => allTags.find(t => t.name === tagName)?.id).filter(Boolean);
                        renderTags();
                        if (elements.selectedTags) elements.selectedTags.value = post.tags.join(',');
                    }

                    if (elements.publishedAt) {
                        const fp = elements.publishedAt._flatpickr;
                        if (fp && post.published_at) fp.setDate(new Date(post.published_at));
                    }
                    if (elements.scheduledAt) {
                        const fp = elements.scheduledAt._flatpickr;
                        if (fp && post.scheduled_at) fp.setDate(new Date(post.scheduled_at));
                    }

                    // Vditor
                    vditor = initVditor('vditor', {
                        value: post.content || '',
                        after: () => { console.log('Vditor initialized with content'); }
                    });

                    // Autosave & Revisions
                    if (post.autosave_available) {
                        fetchAutosaveData(postId);
                    }
                    loadRevisions(postId);
                    startAutosaveLoop(postId);
                }
            } else {
                vditor = initVditor('vditor');
            }
        } catch (err) {
            console.error("Failed to load initial data:", err);
        }

        // Save Button
        elements.saveBtn?.addEventListener('click', async () => {
            const payload = {
                title: elements.title?.value,
                slug: elements.slug?.value,
                content: vditor?.getValue(),
                category_name: elements.category?.value || "General",
                tags: elements.selectedTags?.value ? elements.selectedTags.value.split(',').map(t => t.trim()).filter(Boolean) : [],
                description: elements.description?.value,
                image: elements.image?.value,
                password: elements.password?.value,
                pinned: isPinned,
                pin_order: parseInt(elements.pinOrder?.value || 0),
                status: postStatus,
                is_draft: postStatus !== "published",
                published_at: convertLocalToISO(elements.publishedAt?.value),
                scheduled_at: postStatus === 'scheduled' ? convertLocalToISO(elements.scheduledAt?.value) : null,
            };

            if (!payload.title || !payload.slug) {
                window.showAdminAlert("请填写标题和别名", "warning");
                return;
            }
            if (!payload.content) {
                window.showAdminAlert("内容不能为空", "warning");
                return;
            }

            try {
                const method = postId ? 'PUT' : 'POST';
                const url = postId ? `${API_URL}/posts/${postId}` : `${API_URL}/posts`;
                const result = await window.adminRequest(url, {
                    method,
                    body: JSON.stringify(payload)
                });
                if (result.ok) {
                    window.showAdminAlert(postId ? "保存成功" : "发布成功", "success");
                    if (window.adminClearCache) window.adminClearCache('posts');
                    if (!postId || result.data?.id) {
                        setTimeout(() => {
                            if (window.__adminTabManager) window.__adminTabManager.closeCurrentAndNavigate('/admin/posts');
                            else window.location.href = '/admin/posts';
                        }, 1000);
                    }
                } else {
                    window.showAdminAlert(result.msg || "保存失败", "error");
                }
            } catch (err) {
                console.error("Save error:", err);
                window.showAdminAlert("网络错误，保存失败", "error");
            }
        });
    };

    init();
    window.addEventListener('resize', syncEditorHeaderHeight);

    return {
        getVditor: () => vditor,
        destroy: () => {
            stopAutosaveLoop();
            window.removeEventListener('resize', syncEditorHeaderHeight);
            if (vditor) destroyVditor(vditor);
        }
    };
}

