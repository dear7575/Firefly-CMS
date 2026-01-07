/**
 * 站点设置服务
 * 从后端 API 获取站点配置，支持智能缓存和默认值
 */

import { getApiUrl } from "@/utils/api-utils";
import { parseApiResponse } from "@/utils/api-response";

// API 基础地址（从工具类动态获取）
const getBaseUrl = () => getApiUrl();

// 缓存配置
interface CacheEntry<T> {
    data: T;
    timestamp: number;
    isStale: boolean;
}

// 主缓存
let settingsCache: CacheEntry<Record<string, any>> | null = null;

// 分组缓存
const groupCache: Map<string, CacheEntry<Record<string, any>>> = new Map();

// 请求去重：防止并发请求
let pendingRequest: Promise<Record<string, any>> | null = null;
const pendingGroupRequests: Map<string, Promise<Record<string, any>>> = new Map();

// 缓存时间配置
const CACHE_CONFIG = {
    // 新鲜数据有效期（5分钟）
    FRESH_TTL: 5 * 60 * 1000,
    // 过期数据最大保留时间（30分钟）- 用于 stale-while-revalidate
    STALE_TTL: 30 * 60 * 1000,
    // 分组缓存有效期（3分钟）
    GROUP_TTL: 3 * 60 * 1000,
};

// 默认配置值
const DEFAULT_SETTINGS: Record<string, any> = {
    // 基本信息
    site_title: 'Firefly',
    site_subtitle: 'A beautiful blog',
    site_description: 'A modern blog powered by Firefly',
    site_keywords: 'blog,firefly,astro',
    site_url: 'http://localhost:4321',
    site_lang: 'zh_CN',
    site_start_date: '',

    // 品牌设置
    brand_logo: '',
    brand_logo_type: 'icon',
    brand_favicon: '/assets/images/favicon.ico',
    brand_navbar_title: '',

    // 个人资料
    profile_avatar: '/assets/images/avatar.webp',
    profile_name: 'Firefly',
    profile_bio: 'Hello, I\'m Firefly.',

    // 主题设置
    theme_hue: 165,
    theme_fixed: false,
    theme_default_mode: 'system',

    // 页脚设置
    footer_icp: '',
    footer_icp_url: 'https://beian.miit.gov.cn/',
    footer_copyright: '',
    footer_powered_by: true,
    footer_custom_html: '',

    // 功能开关
    feature_comment: true,
    feature_search: true,
    feature_rss: true,
    feature_archive: true,
    feature_friends: true,

    // 统计埋点
    analytics_google_id: '',
    analytics_clarity_id: '',

    // 评论设置
    comment_type: "none",
    comment_twikoo_env_id: "",
    comment_twikoo_lang: "zh-CN",
    comment_twikoo_visitor_count: true,

    // 文章设置
    post_per_page: 10,
    post_default_layout: 'list',
    post_show_toc: true,
    post_show_updated: true,

    // API设置
    // api_url: 'http://localhost:8001',

    // Banner 设置
    banner_enable: true,
    banner_title: '',
    banner_subtitle: '',
    banner_image: '',
};

/**
 * 检查缓存是否新鲜
 */
function isCacheFresh(cache: CacheEntry<any> | null): boolean {
    if (!cache) return false;
    return Date.now() - cache.timestamp < CACHE_CONFIG.FRESH_TTL;
}

/**
 * 检查缓存是否可用（包括过期但未超时的数据）
 */
function isCacheUsable(cache: CacheEntry<any> | null): boolean {
    if (!cache) return false;
    return Date.now() - cache.timestamp < CACHE_CONFIG.STALE_TTL;
}

/**
 * 从 API 获取设置（内部方法）
 */
async function fetchFromAPI(): Promise<Record<string, any>> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5秒超时

    try {
        const response = await fetch(`${getBaseUrl()}/settings/public`, {
            signal: controller.signal,
            headers: {
                'Accept': 'application/json',
            },
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const payload = await parseApiResponse<Record<string, any>>(response);
        return payload.data || {};
    } catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
}

/**
 * 从 API 获取所有站点设置
 * 实现 stale-while-revalidate 策略
 */
export async function fetchSiteSettings(): Promise<Record<string, any>> {
    // 1. 如果缓存新鲜，直接返回
    if (isCacheFresh(settingsCache)) {
        return settingsCache!.data;
    }

    // 2. 如果有正在进行的请求，等待它完成
    if (pendingRequest) {
        try {
            return await pendingRequest;
        } catch {
            // 如果等待的请求失败，继续尝试
        }
    }

    // 3. 如果缓存可用但过期，先返回过期数据，后台刷新
    if (isCacheUsable(settingsCache)) {
        // 标记为过期
        settingsCache!.isStale = true;

        // 后台刷新（不阻塞）
        refreshCacheInBackground();

        return settingsCache!.data;
    }

    // 4. 没有可用缓存，必须等待新数据
    pendingRequest = fetchFromAPI()
        .then(data => {
            const mergedSettings = { ...DEFAULT_SETTINGS, ...data };
            settingsCache = {
                data: mergedSettings,
                timestamp: Date.now(),
                isStale: false,
            };
            return mergedSettings;
        })
        .catch(error => {
            console.error('Failed to fetch site settings:', error);
            return DEFAULT_SETTINGS;
        })
        .finally(() => {
            pendingRequest = null;
        });

    return pendingRequest;
}

/**
 * 后台刷新缓存
 */
function refreshCacheInBackground(): void {
    if (pendingRequest) return; // 已有请求在进行

    pendingRequest = fetchFromAPI()
        .then(data => {
            const mergedSettings = { ...DEFAULT_SETTINGS, ...data };
            settingsCache = {
                data: mergedSettings,
                timestamp: Date.now(),
                isStale: false,
            };
            return mergedSettings;
        })
        .catch(error => {
            console.error('Background cache refresh failed:', error);
            // 保持现有缓存
            return settingsCache?.data || DEFAULT_SETTINGS;
        })
        .finally(() => {
            pendingRequest = null;
        });
}

/**
 * 获取单个设置值
 */
export async function getSetting<T = any>(key: string, defaultValue?: T): Promise<T> {
    const settings = await fetchSiteSettings();
    return settings[key] ?? defaultValue ?? DEFAULT_SETTINGS[key];
}

/**
 * 获取分组的设置（带缓存）
 */
export async function getSettingsByGroup(group: string): Promise<Record<string, any>> {
    // 检查分组缓存
    const cached = groupCache.get(group);
    if (cached && Date.now() - cached.timestamp < CACHE_CONFIG.GROUP_TTL) {
        return cached.data;
    }

    // 检查是否有正在进行的请求
    const pending = pendingGroupRequests.get(group);
    if (pending) {
        return pending;
    }

    // 发起新请求
    const request = fetchGroupFromAPI(group);
    pendingGroupRequests.set(group, request);

    try {
        const data = await request;
        groupCache.set(group, {
            data,
            timestamp: Date.now(),
            isStale: false,
        });
        return data;
    } catch (error) {
        console.error(`Failed to fetch settings for group ${group}:`, error);
        return getDefaultSettingsForGroup(group);
    } finally {
        pendingGroupRequests.delete(group);
    }
}

/**
 * 从 API 获取分组设置
 */
async function fetchGroupFromAPI(group: string): Promise<Record<string, any>> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    try {
        const response = await fetch(`${getBaseUrl()}/settings/public/by-group/${group}`, {
            signal: controller.signal,
            headers: {
                'Accept': 'application/json',
            },
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const payload = await parseApiResponse<Record<string, any>>(response);
        return payload.data || {};
    } catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
}

/**
 * 获取指定分组的默认设置
 */
function getDefaultSettingsForGroup(group: string): Record<string, any> {
    const prefix = group + '_';
    const result: Record<string, any> = {};
    for (const [key, value] of Object.entries(DEFAULT_SETTINGS)) {
        if (key.startsWith(prefix)) {
            result[key.substring(prefix.length)] = value;
        }
    }
    return result;
}

/**
 * 清除所有缓存
 */
export function clearSettingsCache(): void {
    settingsCache = null;
    groupCache.clear();
}

/**
 * 清除指定分组的缓存
 */
export function clearGroupCache(group: string): void {
    groupCache.delete(group);
}

/**
 * 预热缓存（在应用启动时调用）
 */
export async function warmupCache(): Promise<void> {
    try {
        await fetchSiteSettings();
    } catch (error) {
        console.error('Cache warmup failed:', error);
    }
}

/**
 * 获取缓存状态（用于调试）
 */
export function getCacheStatus(): {
    hasCachedSettings: boolean;
    isStale: boolean;
    cacheAge: number | null;
    groupCacheCount: number;
} {
    return {
        hasCachedSettings: settingsCache !== null,
        isStale: settingsCache?.isStale ?? false,
        cacheAge: settingsCache ? Date.now() - settingsCache.timestamp : null,
        groupCacheCount: groupCache.size,
    };
}

/**
 * 获取基本信息设置
 */
export async function getBasicSettings() {
    return getSettingsByGroup('basic');
}

/**
 * 获取品牌设置
 */
export async function getBrandSettings() {
    return getSettingsByGroup('brand');
}

/**
 * 获取个人资料设置
 */
export async function getProfileSettings() {
    return getSettingsByGroup('profile');
}

/**
 * 获取主题设置
 */
export async function getThemeSettings() {
    return getSettingsByGroup('theme');
}

/**
 * 获取页脚设置
 */
export async function getFooterSettings() {
    return getSettingsByGroup('footer');
}

/**
 * 获取功能开关设置
 */
export async function getFeatureSettings() {
    return getSettingsByGroup('feature');
}

/**
 * 获取文章设置
 */
export async function getPostSettings() {
    return getSettingsByGroup('post');
}

// 导出默认设置供参考
export { DEFAULT_SETTINGS };
