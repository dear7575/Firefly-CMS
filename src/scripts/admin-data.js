/**
 * 后台数据管理
 * 包含缓存系统和通用的数据操作（如文章置顶、删除等）
 */

const CACHE_DURATION = 5 * 60 * 1000;
if (!window._adminDataCache) {
    window._adminDataCache = {
        posts: { data: null, timestamp: 0 },
        categories: { data: null, timestamp: 0 },
        tags: { data: null, timestamp: 0 },
        settings: { data: null, timestamp: 0 }
    };
}

export function isCacheValid(cacheKey) {
    const cache = window._adminDataCache[cacheKey];
    if (!cache || !cache.data) return false;
    return (Date.now() - cache.timestamp) < CACHE_DURATION;
}

export function getCachedData(cacheKey) {
    return isCacheValid(cacheKey) ? window._adminDataCache[cacheKey].data : null;
}

export function setCachedData(cacheKey, data) {
    window._adminDataCache[cacheKey] = { data: data, timestamp: Date.now() };
}

export function clearCache(cacheKey) {
    if (cacheKey) window._adminDataCache[cacheKey] = { data: null, timestamp: 0 };
    else Object.keys(window._adminDataCache).forEach(key => window._adminDataCache[key] = { data: null, timestamp: 0 });
}

window.adminClearCache = clearCache;

export async function togglePin(id, API_URL, onUpdate) {
    try {
        const getResult = await window.adminRequest(`${API_URL}/posts/${id}`);
        if (!getResult.ok) {
            if (getResult.code !== 401) window.showAdminAlert(getResult.msg || '获取文章信息失败', "error");
            return;
        }

        const post = getResult.data;
        const updateResult = await window.adminRequest(`${API_URL}/posts/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title: post.title,
                slug: post.slug,
                description: post.description || "",
                content: post.content,
                image: post.image || "",
                category_name: post.category || "",
                tags: post.tags || [],
                password: post.password || "",
                is_draft: post.is_draft || false,
                pinned: !post.pinned
            }),
        });

        if (updateResult.ok) {
            clearCache('posts');
            if (onUpdate) onUpdate();
        } else if (updateResult.code !== 401) {
            window.showAdminAlert(updateResult.msg || '操作失败', "error");
        }
    } catch (err) {
        console.error("Failed to toggle pin:", err);
        window.showAdminAlert('操作失败', "error");
    }
}

export async function deletePost(id, API_URL, onUpdate, confirmMsg) {
    const confirmed = await window.showAdminConfirm(confirmMsg || '确定要删除吗？');
    if (!confirmed) return;

    try {
        const result = await window.adminRequest(`${API_URL}/posts/${id}`, { method: "DELETE" });
        if (result.ok) {
            clearCache('posts');
            if (onUpdate) onUpdate();
        } else if (result.code !== 401) {
            window.showAdminAlert(result.msg || '删除失败', "error");
        }
    } catch (err) {
        console.error("Failed to delete post:", err);
        window.showAdminAlert('删除失败', "error");
    }
}
