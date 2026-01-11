/**
 * 后台特定页面逻辑
 * 包含文章列表加载、分页渲染等
 */
import { getCachedData, setCachedData, isCacheValid, clearCache, togglePin, deletePost } from "./admin-data";
import { initDashboardCharts } from "./admin-charts";

export function initAdminPages() {
    const API_URL = window.API_URL;
    const t = window.adminI18n || {};

    let isLoading = false;
    let currentPage = 1;
    let pageSize = 10;
    let totalPages = 1;
    let totalPosts = 0;

    async function loadPosts(page = 1, forceRefresh = false) {
        const tableBody = document.getElementById("postsTableBody");
        if (!tableBody) return;

        if (isLoading) return;
        isLoading = true;
        currentPage = page;

        try {
            let posts;
            if (!forceRefresh && isCacheValid('posts')) {
                posts = getCachedData('posts');
            } else {
                const result = await window.adminRequest(`${API_URL}/posts?all=true`);
                if (!result.ok) throw new Error(result.msg || '获取文章列表失败');
                posts = result.data || [];
                setCachedData('posts', posts);
            }

            if (typeof window.postsFilterUpdate === 'function') {
                posts = window.postsFilterUpdate(posts);
            }

            totalPosts = posts.length;
            totalPages = Math.ceil(totalPosts / pageSize) || 1;
            const startIndex = (currentPage - 1) * pageSize;
            const pagedPosts = posts.slice(startIndex, startIndex + pageSize);

            if (pagedPosts.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="6" class="px-6 py-12 text-center text-zinc-500">${t.empty || '暂无数据'}</td></tr>`;
            } else {
                tableBody.innerHTML = pagedPosts.map(post => renderPostRow(post)).join("");
            }
            renderPagination();
        } catch (err) {
            console.error("Failed to load post list:", err);
            tableBody.innerHTML = `<tr><td colspan="6" class="px-6 py-12 text-center text-zinc-500">${t.loadFailed || '加载失败'}</td></tr>`;
        } finally {
            isLoading = false;
        }
    }

    function renderPostRow(post) {
        const statusBadges = [];
        if (post.pinned) statusBadges.push('<span class="px-2 py-0.5 bg-zinc-100 dark:bg-zinc-800 text-[var(--primary)] text-[10px] font-bold rounded uppercase tracking-wider">' + (t.pinned || '置顶') + '</span>');
        if (post.is_draft) statusBadges.push('<span class="px-2 py-0.5 bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 text-[10px] font-bold rounded uppercase tracking-wider">' + (t.draft || '草稿') + '</span>');
        if (post.has_password) statusBadges.push('<span class="px-2 py-0.5 bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 text-[10px] font-bold rounded uppercase tracking-wider">' + (t.protected || '加密') + '</span>');
        if (!post.is_draft && !post.has_password) statusBadges.push('<span class="px-2 py-0.5 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 text-[10px] font-bold rounded uppercase tracking-wider">' + (t.public || '公开') + '</span>');

        const pinIcon = post.pinned
            ? '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>'
            : '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>';

        const dateLabel = new Date(post.published_at).toLocaleDateString();
        return `
            <tr class="hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors ${post.pinned ? 'pinned-row' : ''}">
                <td class="px-4 md:px-6 py-4 align-top">
                    <div class="font-medium text-zinc-900 dark:text-zinc-100">${post.title}</div>
                    <div class="text-xs text-zinc-400 font-mono mt-1">${post.slug}</div>
                </td>
                <td class="px-4 md:px-6 py-4 text-center hidden md:table-cell">
                    <div class="flex flex-wrap gap-1 justify-center">${statusBadges.join("")}</div>
                </td>
                <td class="px-4 md:px-6 py-4 text-center hidden md:table-cell">
                    <span class="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 text-xs rounded">${post.category || (t.uncategorized || '未分类')}</span>
                </td>
                <td class="px-4 md:px-6 py-4 text-center hidden lg:table-cell">
                    <span class="inline-flex items-center gap-1 text-sm text-zinc-500">👁 ${post.view_count || 0}</span>
                </td>
                <td class="px-4 md:px-6 py-4 text-sm text-zinc-500 text-center hidden md:table-cell">${dateLabel}</td>
                <td class="px-4 md:px-6 py-4 text-center">
                    <div class="flex items-center gap-1 justify-start md:justify-center">
                        <button onclick="adminTogglePin('${post.id}')" class="p-2 ${post.pinned ? 'text-[var(--primary)]' : 'text-zinc-400'} hover:bg-[var(--primary)]/10 rounded-lg transition-colors">${pinIcon}</button>
                        <a href="/admin/edit/${post.id}" class="p-2 text-[var(--primary)] hover:bg-[var(--primary)]/10 rounded-lg transition-colors">
                            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                        </a>
                        <button onclick="adminDeletePost('${post.id}')" class="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors">
                            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    function renderPagination() {
        const container = document.getElementById("paginationContainer");
        if (!container) return;
        const pageInfo = (t.paginationInfo || '第 {page} 页 / 共 {total} 页').replace('{page}', currentPage).replace('{total}', totalPages);
        container.innerHTML = `
            <div class="flex items-center justify-between px-6 py-4 bg-zinc-50 dark:bg-zinc-800/50 border-t border-zinc-200 dark:border-zinc-800">
                <div class="text-sm text-zinc-500">${pageInfo} (${totalPosts} 条记录)</div>
                <div class="flex items-center gap-2">
                    <button onclick="adminGoToPage(${currentPage - 1})" ${currentPage <= 1 ? 'disabled' : ''} class="px-3 py-1.5 text-sm font-medium rounded-lg text-zinc-600 disabled:opacity-50">上一页</button>
                    <button onclick="adminGoToPage(${currentPage + 1})" ${currentPage >= totalPages ? 'disabled' : ''} class="px-3 py-1.5 text-sm font-medium rounded-lg text-zinc-600 disabled:opacity-50">下一页</button>
                </div>
            </div>
        `;
    }

    window.adminGoToPage = (page) => { if (page >= 1 && page <= totalPages) loadPosts(page); };
    window.adminTogglePin = (id) => togglePin(id, API_URL, () => loadPosts(currentPage, true));
    window.adminDeletePost = (id) => deletePost(id, API_URL, () => loadPosts(currentPage, true), t.confirmDelete);

    // Dashboard initialization
    async function loadDashboardStats() {
        const dashboardEl = document.getElementById('totalPosts');
        if (!dashboardEl) return;

        try {
            const result = await window.adminRequest(`${API_URL}/dashboard/stats`);
            if (!result.ok) throw new Error(result.msg || '获取统计信息失败');
            const data = result.data || {};

            // Update stats
            const updateText = (id, val) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val;
            };

            updateText('totalPosts', data.posts.total);
            updateText('publishedPosts', data.posts.published);
            updateText('draftPosts', data.posts.draft);
            updateText('encryptedPosts', data.posts.encrypted || 0);
            updateText('recentPostsBadge', '+' + data.posts.recent);
            updateText('totalCategories', data.categories.total);
            updateText('totalTags', data.tags.total);
            updateText('totalFriends', data.friends.total);
            updateText('enabledFriends', data.friends.enabled);

            // Update recent posts list
            const recentPostsList = document.getElementById('recentPostsList');
            if (recentPostsList) {
                if (!data.latest_posts || data.latest_posts.length === 0) {
                    recentPostsList.innerHTML = `<div class="p-6 text-center text-zinc-500">${t.empty || '暂无文章'}</div>`;
                } else {
                    recentPostsList.innerHTML = data.latest_posts.map(post => `
                        <a href="/admin/edit/${post.id}" class="flex items-center justify-between p-4 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors">
                            <div class="flex-1 min-w-0">
                                <h3 class="font-medium text-zinc-900 dark:text-zinc-100 truncate">${post.title}</h3>
                                <p class="text-sm text-zinc-500 mt-1">${post.category || (t.uncategorized || '未分类')} · ${new Date(post.published_at).toLocaleDateString()}</p>
                            </div>
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                            </svg>
                        </a>
                    `).join('');
                }
            }

            // Update category stats
            const categoryStats = document.getElementById('categoryStats');
            if (categoryStats) {
                if (!data.categories.stats || data.categories.stats.length === 0) {
                    categoryStats.innerHTML = `<div class="text-center text-zinc-500">${t.noCategories || '暂无分类统计'}</div>`;
                } else {
                    const maxCount = Math.max(...data.categories.stats.map(c => c.count), 1);
                    categoryStats.innerHTML = data.categories.stats.map(cat => {
                        const widthPercent = (cat.count / maxCount) * 100;
                        return `
                            <div class="space-y-2">
                                <div class="flex items-center justify-between text-sm">
                                    <span class="text-zinc-700 dark:text-zinc-300">${cat.name}</span>
                                    <span class="font-medium" style="color: var(--primary)">${cat.count}</span>
                                </div>
                                <div class="h-2 bg-zinc-100 dark:bg-zinc-700 rounded-full overflow-hidden">
                                    <div class="h-full rounded-full transition-all" style="width: ${widthPercent}%; background-color: var(--primary)"></div>
                                </div>
                            </div>
                        `;
                    }).join('');
                }
            }

            // Update analytics Card
            const analytics = data.analytics || {};
            updateText('totalViews', (analytics.total_views || 0).toLocaleString());

            const topViewList = document.getElementById('topViewList');
            if (topViewList) {
                const topPosts = analytics.top_posts || [];
                if (topPosts.length === 0) {
                    topViewList.innerHTML = '<div class="p-6 text-center text-zinc-500">暂无访问数据</div>';
                } else {
                    topViewList.innerHTML = topPosts.map((item, index) => `
                        <div class="flex items-center justify-between px-6 py-4">
                            <div class="flex items-center gap-3 min-w-0">
                                <span class="w-8 h-8 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center font-semibold text-sm text-zinc-600 dark:text-zinc-300">${index + 1}</span>
                                <div class="min-w-0">
                                    <p class="font-medium text-zinc-900 dark:text-zinc-100 truncate">${item.title || '未命名文章'}</p>
                                    <p class="text-xs text-zinc-500 dark:text-zinc-400">浏览 ${(item.views || 0).toLocaleString()}</p>
                                </div>
                            </div>
                            <a href="/admin/edit/${item.id}" class="text-xs text-[var(--primary)] hover:underline flex-shrink-0">管理</a>
                        </div>
                    `).join('');
                }
            }

            // Render charts via separate module
            initDashboardCharts(data.charts);

        } catch (err) {
            console.error('Failed to load dashboard stats:', err);
        }
    }

    // Page initialization
    const path = window.location.pathname;
    if (path.startsWith("/admin/posts") || path === "/admin/posts") {
        loadPosts();
    } else if (path === "/admin" || path === "/admin/") {
        loadDashboardStats();
    }
}
