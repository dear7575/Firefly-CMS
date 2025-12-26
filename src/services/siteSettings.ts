/**
 * 站点设置服务
 * 从后端 API 获取站点配置，支持缓存和默认值
 */

// API 基础地址（可以从环境变量或配置文件获取）
const API_URL = import.meta.env.PUBLIC_API_URL || 'http://localhost:8000';

// 缓存配置
let settingsCache: Record<string, any> | null = null;
let cacheTimestamp: number = 0;
const CACHE_TTL = 60 * 1000; // 1分钟缓存（开发时可以更短）

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

    // 文章设置
    post_per_page: 10,
    post_default_layout: 'list',
    post_show_toc: true,
    post_show_updated: true,

    // API设置
    api_url: 'http://localhost:8000',
};

/**
 * 从 API 获取所有站点设置
 */
export async function fetchSiteSettings(): Promise<Record<string, any>> {
    // 检查缓存是否有效
    if (settingsCache && Date.now() - cacheTimestamp < CACHE_TTL) {
        return settingsCache;
    }

    try {
        const response = await fetch(`${API_URL}/settings/public`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // 合并默认值和 API 返回的值
        settingsCache = {...DEFAULT_SETTINGS, ...data};
        cacheTimestamp = Date.now();

        return settingsCache;
    } catch (error) {
        console.error('Failed to fetch site settings:', error);
        // 返回默认值
        return DEFAULT_SETTINGS;
    }
}

/**
 * 获取单个设置值
 */
export async function getSetting<T = any>(key: string, defaultValue?: T): Promise<T> {
    const settings = await fetchSiteSettings();
    return settings[key] ?? defaultValue ?? DEFAULT_SETTINGS[key];
}

/**
 * 获取分组的设置
 */
export async function getSettingsByGroup(group: string): Promise<Record<string, any>> {
    try {
        const response = await fetch(`${API_URL}/settings/public/by-group/${group}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch settings for group ${group}:`, error);
        // 返回该分组的默认值
        const prefix = group + '_';
        const result: Record<string, any> = {};
        for (const [key, value] of Object.entries(DEFAULT_SETTINGS)) {
            if (key.startsWith(prefix)) {
                result[key.substring(prefix.length)] = value;
            }
        }
        return result;
    }
}

/**
 * 清除缓存
 */
export function clearSettingsCache(): void {
    settingsCache = null;
    cacheTimestamp = 0;
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
export {DEFAULT_SETTINGS};
