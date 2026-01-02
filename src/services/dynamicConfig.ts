import { getApiUrl } from "@/utils/api-utils";

// API 基础地址（从环境变量读取）
const API_URL = getApiUrl();

// 缓存配置
let configCache: Record<string, any> | null = null;

/**
 * 从 API 获取所有站点设置
 */
async function fetchSettings(): Promise<Record<string, any>> {
    if (configCache) {
        return configCache;
    }

    try {
        const response = await fetch(`${API_URL}/settings/public`, {
            headers: {
                'Accept': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        configCache = data;
        console.log('[DynamicConfig] 成功从 API 加载配置');
        return data;
    } catch (error) {
        console.warn('[DynamicConfig] 无法从 API 加载配置，使用静态配置:', error);
        return {};
    }
}

/**
 * 获取动态站点配置
 * 与静态配置合并，API 配置优先
 */
export async function getDynamicSiteConfig(staticConfig: any): Promise<any> {
    const apiSettings = await fetchSettings();

    // 如果 API 没有返回数据，直接返回静态配置
    if (Object.keys(apiSettings).length === 0) {
        return staticConfig;
    }

    // 合并配置，API 配置优先
    return {
        ...staticConfig,
        // 基本信息
        title: apiSettings.site_title || staticConfig.title,
        subtitle: apiSettings.site_subtitle || staticConfig.subtitle,
        description: apiSettings.site_description || staticConfig.description,
        keywords: apiSettings.site_keywords
            ? apiSettings.site_keywords.split(',').map((k: string) => k.trim())
            : staticConfig.keywords,
        site_url: apiSettings.site_url || staticConfig.site_url,
        lang: apiSettings.site_lang || staticConfig.lang,
        siteStartDate: apiSettings.site_start_date || staticConfig.siteStartDate,

        // 主题设置
        themeColor: {
            ...staticConfig.themeColor,
            hue: apiSettings.theme_hue ?? staticConfig.themeColor?.hue ?? 165,
            fixed: apiSettings.theme_fixed ?? staticConfig.themeColor?.fixed ?? false,
            defaultMode: apiSettings.theme_default_mode || staticConfig.themeColor?.defaultMode || 'system',
        },

        // 导航栏设置
        navbarTitle: apiSettings.brand_navbar_title || staticConfig.navbarTitle,
        navbarLogo: apiSettings.brand_logo
            ? {
                type: apiSettings.brand_logo_type || 'image',
                value: apiSettings.brand_logo,
                alt: staticConfig.navbarLogo?.alt || 'Logo',
            }
            : staticConfig.navbarLogo,

        // Favicon
        favicon: apiSettings.brand_favicon
            ? [{ src: apiSettings.brand_favicon, sizes: '32x32' }]
            : staticConfig.favicon,

        // 分页配置
        pagination: {
            ...staticConfig.pagination,
            postsPerPage: apiSettings.post_per_page ?? staticConfig.pagination?.postsPerPage ?? 10,
        },

        // 文章列表布局
        postListLayout: {
            ...staticConfig.postListLayout,
            defaultMode: apiSettings.post_default_layout || staticConfig.postListLayout?.defaultMode || 'list',
        },

        // 文章设置
        showLastModified: apiSettings.post_show_updated ?? staticConfig.showLastModified ?? true,
    };
}

/**
 * 获取动态个人资料配置
 */
export async function getDynamicProfileConfig(staticConfig: any): Promise<any> {
    const apiSettings = await fetchSettings();

    if (Object.keys(apiSettings).length === 0) {
        return staticConfig;
    }

    return {
        ...staticConfig,
        avatar: apiSettings.profile_avatar || staticConfig.avatar,
        name: apiSettings.profile_name || staticConfig.name,
        bio: apiSettings.profile_bio || staticConfig.bio,
    };
}

/**
 * 获取动态页脚配置
 */
export async function getDynamicFooterConfig(staticConfig: any): Promise<any> {
    const apiSettings = await fetchSettings();

    if (Object.keys(apiSettings).length === 0) {
        return staticConfig;
    }

    // 构建自定义 HTML
    let customHtml = '';

    // ICP 备案号
    if (apiSettings.footer_icp) {
        const icpUrl = apiSettings.footer_icp_url || 'https://beian.miit.gov.cn/';
        customHtml += `<a href="${icpUrl}" target="_blank" rel="noopener noreferrer" class="footer-icp">${apiSettings.footer_icp}</a>`;
    }

    // 版权信息
    if (apiSettings.footer_copyright) {
        customHtml += `<span class="footer-copyright">${apiSettings.footer_copyright}</span>`;
    }

    // 自定义 HTML
    if (apiSettings.footer_custom_html) {
        customHtml += apiSettings.footer_custom_html;
    }

    return {
        ...staticConfig,
        enable: customHtml.length > 0 || staticConfig.enable,
        customHtml: customHtml || staticConfig.customHtml,
        poweredBy: apiSettings.footer_powered_by ?? staticConfig.poweredBy ?? true,
    };
}

/**
 * 获取功能开关配置
 */
export async function getFeatureFlags(): Promise<Record<string, boolean>> {
    const apiSettings = await fetchSettings();

    return {
        comment: apiSettings.feature_comment ?? true,
        search: apiSettings.feature_search ?? true,
        rss: apiSettings.feature_rss ?? true,
        archive: apiSettings.feature_archive ?? true,
        friends: apiSettings.feature_friends ?? true,
    };
}

/**
 * 清除配置缓存
 */
export function clearConfigCache(): void {
    configCache = null;
}

/**
 * 导出原始 API 设置获取函数
 */
export { fetchSettings };
