import { getApiUrl } from "@/utils/api-utils";
import { parseApiResponse } from "@/utils/api-response";

/** API 基础地址（从工具类动态获取） */
const getBaseUrl = () => getApiUrl();

/**
 * 文章数据接口
 */
export interface Post {
    /** 文章唯一标识（UUID） */
    id: string;
    /** 文章标题 */
    title: string;
    /** 文章 URL 别名 */
    slug: string;
    /** 文章摘要描述 */
    description: string;
    /** 发布时间（ISO 格式） */
    published_at: string | null;
    /** 所属分类名称 */
    category: string;
    /** 标签列表 */
    tags: string[];
    /** 是否为草稿 */
    is_draft: boolean;
    /** 是否有密码保护 */
    has_password: boolean;
    /** 发布状态 */
    status: string;
    /** 定时发布时间 */
    scheduled_at?: string | null;
    /** 是否存在自动保存内容 */
    autosave_available?: boolean;
    /** 文章密码（仅编辑时返回） */
    password?: string;
}

/**
 * 友链数据接口（后端返回格式）
 */
export interface FriendLinkAPI {
    id: string;
    title: string;
    url: string;
    avatar: string;
    description: string;
    tags: string;
    weight: number;
    enabled: boolean;
}

/**
 * 友链数据接口（前端使用格式）
 */
export interface FriendLink {
    title: string;
    imgurl: string;
    desc: string;
    siteurl: string;
    tags: string[];
    weight: number;
    enabled: boolean;
}

/**
 * 获取所有文章列表
 *
 * @returns Promise<Post[]> 文章列表
 * @throws Error 请求失败时抛出错误
 */
export async function fetchPosts(): Promise<Post[]> {
    const response = await fetch(`${getBaseUrl()}/posts`);
    const payload = await parseApiResponse<Post[]>(response);
    if (!response.ok || payload.code >= 400) {
        throw new Error(payload.msg || '获取文章列表失败');
    }
    return payload.data || [];
}

/**
 * 获取启用的友链列表（从后端 API）
 *
 * @returns Promise<FriendLink[]> 友链列表（已转换为前端格式）
 */
export async function fetchEnabledFriends(): Promise<FriendLink[]> {
    try {
        const response = await fetch(`${getBaseUrl()}/friends`);
        const payload = await parseApiResponse<FriendLinkAPI[]>(response);
        if (!response.ok || payload.code >= 400) {
            console.error('获取友链列表失败');
            return [];
        }
        const data: FriendLinkAPI[] = payload.data || [];

        // 过滤启用的友链，转换字段格式，按权重排序
        return data
            .filter(friend => friend.enabled)
            .map(friend => ({
                title: friend.title,
                imgurl: friend.avatar || '/assets/images/avatar.webp',
                desc: friend.description || '',
                siteurl: friend.url,
                tags: friend.tags ? friend.tags.split(',').map(t => t.trim()) : [],
                weight: friend.weight || 0,
                enabled: friend.enabled,
            }))
            .sort((a, b) => b.weight - a.weight);
    } catch (error) {
        console.error('获取友链列表出错:', error);
        return [];
    }
}

/**
 * 创建新文章
 *
 * @param postData 文章数据
 * @param token JWT 认证令牌
 * @returns Promise<{message: string, id: string}> 创建结果
 * @throws Error 请求失败时抛出错误
 */
export async function createPost(postData: any, token: string) {
    const response = await fetch(`${getBaseUrl()}/posts`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(postData),
    });
    const payload = await parseApiResponse<any>(response);
    if (!response.ok || payload.code >= 400) {
        throw new Error(payload.msg || '创建文章失败');
    }
    return payload.data;
}
