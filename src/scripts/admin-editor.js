/**
 * 后台编辑器管理逻辑
 * 封装 Vditor 初始化和配置
 */
import Vditor from 'vditor';

export function initVditor(id, options = {}) {
    const container = document.getElementById(id);
    if (!container) return null;

    const isDark = document.documentElement.classList.contains("dark");

    const defaultOptions = {
        height: "100%",
        mode: "ir",
        placeholder: "Write your story here...",
        cdn: "/assets/vendor/vditor", // 这里可能需要根据实际情况调整，如果使用了 npm，有些资源可能需要通过 vite 处理
        cache: {
            enable: false,
        },
        theme: isDark ? "dark" : "classic",
        preview: {
            theme: {
                current: isDark ? "dark" : "light",
            },
        },
        toolbarConfig: {
            pin: true,
        },
        counter: {
            enable: true,
        },
        after: function () {
            // 强制设置内容区域样式
            const resetEl = container.querySelector('.vditor-reset');
            if (resetEl) {
                resetEl.style.color = isDark ? '#f4f4f5' : '#18181b';
                resetEl.style.caretColor = isDark ? '#f4f4f5' : '#18181b';
            }
        },
    };

    const finalOptions = { ...defaultOptions, ...options };
    const vditor = new Vditor(id, finalOptions);

    return vditor;
}

/**
 * 同步编辑器头部高度到 CSS 变量
 */
export function syncEditorHeaderHeight() {
    const header = document.querySelector('[data-editor-header]');
    if (!header) return;
    const height = header.offsetHeight || 0;
    document.documentElement.style.setProperty('--admin-editor-header-height', height + 'px');
}

/**
 * 销毁编辑器实例
 */
export function destroyVditor(instance) {
    if (instance && typeof instance.destroy === 'function') {
        try {
            instance.destroy();
        } catch (e) {
            console.error('Failed to destroy Vditor:', e);
        }
    }
}
