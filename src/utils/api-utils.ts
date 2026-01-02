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
    // 使用 process['env'] 语法防止 Vite 在构建时尝试静态替换这些变量
    // 即使在本地构建时没有设置这些变量，服务器运行时也可以从 docker-compose 中读取
    const env = typeof process !== 'undefined' ? process['env'] : {};
    const internalApiUrl = env.INTERNAL_API_URL;

    // 优先使用内部地址，如果没有定义且在服务器端，则尝试降级
    // 注意：如果本地构建时 PUBLIC_API_URL 已被硬编码，这里的 || 会使用硬编码的值
    return internalApiUrl || import.meta.env.PUBLIC_API_URL;
}
