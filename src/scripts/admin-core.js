/**
 * 核心后台功能库
 * 包含 API 请求封装、全局错误处理和认证管理
 */

export function initAdminCore() {
    if (window.adminRequest) return;

    window.safeJson = async function (response) {
        try {
            return await response.json();
        } catch (e) {
            return null;
        }
    };

    window.parseApiResponse = async function (response) {
        const payload = await window.safeJson(response);
        if (payload && typeof payload === "object" && "code" in payload && "msg" in payload && "data" in payload) {
            return {
                ok: payload.code >= 200 && payload.code < 300,
                code: payload.code,
                msg: payload.msg,
                data: payload.data,
                raw: payload
            };
        }

        const message =
            payload && typeof payload === "object"
                ? (payload.msg || payload.message || payload.detail)
                : null;

        return {
            ok: response.ok,
            code: response.status,
            msg: message || (response.ok ? "操作成功" : "操作失败"),
            data: payload,
            raw: payload
        };
    };

    window.adminRequest = async function (url, options) {
        options = options || {};
        options.headers = options.headers || {};

        // 自动添加 Authorization header
        const token = localStorage.getItem('adminToken');
        if (token && !options.headers['Authorization']) {
            options.headers['Authorization'] = 'Bearer ' + token;
        }

        const response = await fetch(url, options);
        return window.parseApiResponse(response);
    };

    // 全局错误处理器，忽略 Vditor 和浏览器扩展相关的错误
    window.addEventListener('unhandledrejection', function (event) {
        var msg = '';
        if (event.reason) {
            if (typeof event.reason === 'string') {
                msg = event.reason;
            } else if (event.reason.message) {
                msg = event.reason.message;
            } else if (event.reason.toString) {
                msg = event.reason.toString();
            }
        }
        if (msg.includes('tagName') || msg.includes('innerHTML') || msg.includes('toLowerCase') || msg.includes('autofill')) {
            event.preventDefault();
            event.stopImmediatePropagation();
            return false;
        }
    }, true);

    const oldOnerror = window.onerror;
    window.onerror = function (message, source, lineno, colno, error) {
        var msg = (message || '') + ' ' + (source || '');
        if (msg.includes('tagName') || msg.includes('innerHTML') || msg.includes('toLowerCase') || msg.includes('autofill') || msg.includes('bootstrap-autofill')) {
            return true;
        }
        if (oldOnerror) return oldOnerror(message, source, lineno, colno, error);
        return false;
    };

    // ============== Authentication Check ==============
    function checkAuth() {
        if (!localStorage.getItem("adminToken") && !window.location.pathname.includes("/admin/login")) {
            window.location.href = "/admin/login";
        }
    }

    // ============== Fetch Interceptor (401 Handling) ==============
    const originalFetch = window.fetch;
    window.fetch = async function (...args) {
        const response = await originalFetch.apply(this, args);
        if (response.status === 401) {
            const url = typeof args[0] === 'string' ? args[0] : args[0]?.url || '';
            const API_URL = window.API_URL;
            if (url.includes('/api/') || (API_URL && url.includes(API_URL))) {
                if (!window._isRedirectingToLogin) {
                    window._isRedirectingToLogin = true;
                    localStorage.removeItem("adminToken");
                    localStorage.removeItem("admin_username");
                    localStorage.removeItem("admin_avatar");
                    if (window.adminAlert) {
                        await window.adminAlert('登录已过期，请重新登录', 'warning', '登录过期');
                    }
                    window.location.href = "/admin/login";
                }
            }
        }
        return response;
    };

    // ============== Token Expiry Check ==============
    window.checkTokenExpiry = function () {
        const token = localStorage.getItem("adminToken");
        if (!token || window.location.pathname.includes("/admin/login")) return;

        try {
            const payload = token.split('.')[1];
            if (payload) {
                const decoded = JSON.parse(atob(payload));
                const exp = decoded.exp;
                if (exp) {
                    const now = Math.floor(Date.now() / 1000);
                    if (exp < now) {
                        localStorage.removeItem("adminToken");
                        localStorage.removeItem("admin_username");
                        localStorage.removeItem("admin_avatar");
                        if (window.adminAlert) {
                            window.adminAlert('登录已过期，请重新登录', 'warning', '登录过期').then(() => {
                                window.location.href = "/admin/login";
                            });
                        } else {
                            setTimeout(() => {
                                if (window.adminAlert) {
                                    window.adminAlert('登录已过期，请重新登录', 'warning', '登录过期').then(() => {
                                        window.location.href = "/admin/login";
                                    });
                                } else {
                                    window.location.href = "/admin/login";
                                }
                            }, 100);
                        }
                    }
                }
            }
        } catch (e) {
            console.error("Token 解析失败:", e);
        }
    };

    checkAuth();
    window.checkTokenExpiry();

    document.addEventListener('astro:page-load', () => {
        checkAuth();
        window.checkTokenExpiry();
    });
}
