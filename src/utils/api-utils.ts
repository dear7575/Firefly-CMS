/**
 * API 工具类
 * 用于处理 SSR 和客户端环境下的 API 地址切换
 */

/**
 * 获取当前的 API 基础地址
 * 如果在服务器端 (SSR) 且定义了 INTERNAL_API_URL，则使用内部地址
 * 其他情况（客户端）使用 PUBLIC_API_URL
 */
export function getApiUrl(): string {
    // 浏览器环境
    if (typeof window !== 'undefined') {
        return import.meta.env.PUBLIC_API_URL;
    }

    // SSR 环境 (Node.js)
    // 优先使用 INTERNAL_API_URL，如果没有则回退到 PUBLIC_API_URL
    return import.meta.env.INTERNAL_API_URL || import.meta.env.PUBLIC_API_URL;
}
