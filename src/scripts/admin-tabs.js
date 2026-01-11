/**
 * 标签页管理系统
 */
export function initAdminTabs() {
    (function () {
        function setupTabBar() {
            var tabBar = document.getElementById('admin-tab-bar');
            if (!tabBar) return false;

            function getTabList() {
                return document.getElementById('admin-tab-list');
            }

            function bindControlButtons() {
                var refreshBtnEl = document.getElementById('admin-tab-refresh');
                if (refreshBtnEl && !refreshBtnEl.dataset.tabBound) {
                    refreshBtnEl.addEventListener('click', function () {
                        window.location.reload();
                    });
                    refreshBtnEl.dataset.tabBound = "1";
                }

                var closeOthersBtnEl = document.getElementById('admin-tab-close-others');
                if (closeOthersBtnEl && !closeOthersBtnEl.dataset.tabBound) {
                    closeOthersBtnEl.addEventListener('click', function () {
                        closeOthers();
                    });
                    closeOthersBtnEl.dataset.tabBound = "1";
                }
            }

            var storageKey = 'firefly_admin_tabs_v1';
            var maxTabs = 8;
            var menuMap = window.adminMenuMap || {};
            var menuIcons = window.adminMenuIcons || {};

            function normalize(path) {
                if (!path) return '/';
                var clean = path.split('?')[0].split('#')[0];
                if (clean.length > 1 && clean.endsWith('/')) {
                    clean = clean.slice(0, -1);
                }
                return clean || '/';
            }

            function encodePath(path) {
                return encodeURIComponent(path);
            }

            function decodePath(value) {
                try {
                    return decodeURIComponent(value || '');
                } catch (err) {
                    return value || '/';
                }
            }

            var defaultPath = normalize('/admin');
            var defaultTab = {
                path: defaultPath,
                title: menuMap[defaultPath] || '仪表盘',
                closable: false
            };

            var tabs = [];
            var activePath = normalize(window.location.pathname);

            function readStorage() {
                var raw = null;
                try {
                    raw = window.localStorage ? localStorage.getItem(storageKey) : null;
                } catch (err) {
                    raw = null;
                }

                if (raw) {
                    try {
                        var parsed = JSON.parse(raw);
                        if (Array.isArray(parsed)) {
                            tabs = parsed
                                .filter(function (tab) {
                                    return tab && tab.path;
                                })
                                .map(function (tab) {
                                    return {
                                        path: normalize(tab.path),
                                        title: tab.title || menuMap[normalize(tab.path)] || '页面',
                                        closable: tab.closable === false ? false : true
                                    };
                                });
                        }
                    } catch (err) {
                        tabs = [];
                    }
                }

                if (!tabs.length) {
                    tabs = [defaultTab];
                }

                if (!tabs.some(function (tab) {
                    return normalize(tab.path) === defaultTab.path;
                })) {
                    tabs.unshift(defaultTab);
                } else {
                    tabs = tabs.map(function (tab) {
                        return normalize(tab.path) === defaultTab.path
                            ? Object.assign({}, defaultTab)
                            : tab;
                    });
                }
            }

            function persist() {
                try {
                    window.localStorage && localStorage.setItem(storageKey, JSON.stringify(tabs));
                } catch (err) {
                    // ignore storage errors
                }
            }

            function getPageTitle(explicitTitle) {
                if (explicitTitle) return explicitTitle;
                var mainEl = document.querySelector('main[data-page-title]');
                if (mainEl && mainEl.dataset.pageTitle) {
                    return mainEl.dataset.pageTitle;
                }
                if (document.title) {
                    var parts = document.title.split(' - ');
                    if (parts.length) {
                        return parts[0].trim();
                    }
                }
                return '';
            }

            function resolveTitle(path, explicitTitle) {
                var normalized = normalize(path);
                if (menuMap[normalized]) {
                    return menuMap[normalized];
                }
                var fallback = getPageTitle(explicitTitle);
                if (fallback) return fallback;
                var segments = normalized.split('/');
                return segments[segments.length - 1] || '页面';
            }

            function limitTabs() {
                if (tabs.length <= maxTabs) return;
                var attempts = 0;
                while (tabs.length > maxTabs && attempts < 20) {
                    attempts++;
                    var removableIndex = tabs.findIndex(function (tab) {
                        var normalized = normalize(tab.path);
                        return tab.closable !== false && normalized !== activePath;
                    });
                    if (removableIndex === -1) {
                        break;
                    }
                    tabs.splice(removableIndex, 1);
                }
            }

            function renderTabs() {
                var tabListEl = getTabList();
                if (!tabListEl) return;
                if (!tabs.length) {
                    tabListEl.innerHTML = '<span class="text-xs text-zinc-400 px-2">暂无标签</span>';
                    bindControlButtons();
                    return;
                }

                var activeEncoded = encodePath(activePath);
                var html = tabs
                    .map(function (tab) {
                        var normalized = normalize(tab.path);
                        var encoded = encodePath(normalized);
                        var isActive = normalized === activePath;
                        var closable = tab.closable !== false;
                        var pillClass = 'admin-tab-pill' + (isActive ? ' admin-tab-pill-active' : '');
                        var iconPath = menuIcons[normalized];
                        var iconHtml = iconPath
                            ? '<span class="admin-tab-pill-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="' + iconPath + '" /></svg></span>'
                            : '<span class="admin-tab-dot"></span>';
                        var closeBtn = closable
                            ? '<button type="button" class="admin-tab-close" data-close-path="' + encoded + '" title="关闭标签">' +
                            '<svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor">' +
                            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>' +
                            '</svg>' +
                            '</button>'
                            : '';
                        return (
                            '<div class="' + pillClass + '" data-tab-wrapper="' + encoded + '">' +
                            '<button type="button" class="admin-tab-trigger" data-tab-path="' + encoded + '" title="' + tab.title + '">' +
                            iconHtml +
                            '<span class="truncate max-w-[8rem]">' + tab.title + '</span>' +
                            '</button>' +
                            closeBtn +
                            '</div>'
                        );
                    })
                    .join('');
                tabListEl.innerHTML = html;
                try {
                    sessionStorage.setItem('firefly_admin_tab_snapshot', html);
                } catch (err) {
                    // ignore storage
                }

                tabListEl.querySelectorAll('[data-tab-path]').forEach(function (btn) {
                    btn.addEventListener('click', function () {
                        var path = decodePath(btn.getAttribute('data-tab-path'));
                        if (!path || path === activePath) return;
                        navigate(path);
                    });
                });

                tabListEl.querySelectorAll('[data-close-path]').forEach(function (btn) {
                    btn.addEventListener('click', function (event) {
                        event.stopPropagation();
                        var path = decodePath(btn.getAttribute('data-close-path'));
                        closeTab(path);
                    });
                });

                requestAnimationFrame(function () {
                    var activeEl = tabListEl.querySelector('[data-tab-path="' + activeEncoded + '"]');
                    if (activeEl && activeEl.scrollIntoView) {
                        activeEl.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
                    }
                });
                bindControlButtons();
            }

            function setActive(path, title) {
                var normalized = normalize(path);
                activePath = normalized;
                var existing = tabs.find(function (tab) {
                    return normalize(tab.path) === normalized;
                });
                var resolvedTitle = resolveTitle(path, title || (existing && existing.title));
                if (existing) {
                    existing.title = resolvedTitle;
                } else {
                    tabs.push({
                        path: normalized,
                        title: resolvedTitle,
                        closable: normalized !== defaultTab.path
                    });
                    limitTabs();
                }
                persist();
                renderTabs();
            }

            function closeTab(path) {
                var normalized = normalize(path);
                var index = tabs.findIndex(function (tab) {
                    return normalize(tab.path) === normalized;
                });
                if (index === -1 || tabs[index].closable === false) return;
                var closingActive = normalized === activePath;
                tabs.splice(index, 1);
                if (!tabs.length) {
                    tabs = [defaultTab];
                    activePath = defaultTab.path;
                }
                persist();
                renderTabs();

                if (closingActive) {
                    var target = tabs[index] || tabs[index - 1] || tabs[0] || defaultTab;
                    navigate(target.path);
                }
            }

            function closeOthers() {
                tabs = tabs.filter(function (tab) {
                    var normalized = normalize(tab.path);
                    return tab.closable === false || normalized === activePath;
                });
                if (!tabs.some(function (tab) {
                    return normalize(tab.path) === activePath;
                })) {
                    tabs.push({
                        path: activePath,
                        title: resolveTitle(activePath),
                        closable: activePath !== defaultTab.path
                    });
                }
                persist();
                renderTabs();
            }

            function closeCurrentAndNavigate(targetPath) {
                var target = normalize(targetPath || defaultTab.path);
                var current = activePath;
                var index = tabs.findIndex(function (tab) {
                    return normalize(tab.path) === current;
                });
                if (index !== -1 && tabs[index].closable !== false) {
                    tabs.splice(index, 1);
                }
                if (!tabs.length) {
                    tabs = [defaultTab];
                }
                if (!tabs.some(function (tab) {
                    return normalize(tab.path) === target;
                })) {
                    tabs.push({
                        path: target,
                        title: resolveTitle(target),
                        closable: target !== defaultTab.path
                    });
                    limitTabs();
                }
                activePath = target;
                persist();
                renderTabs();
                navigate(target, { skipRender: true });
            }

            function navigate(path, options) {
                var normalized = normalize(path);
                activePath = normalized;
                if (!options || !options.skipRender) {
                    renderTabs();
                }
                if (window.Astro && typeof window.Astro.navigate === 'function') {
                    window.Astro.navigate(normalized);
                } else if (window.Astro && window.Astro.router && typeof window.Astro.router.navigate === 'function') {
                    window.Astro.router.navigate(normalized);
                } else {
                    window.location.href = normalized;
                }
            }

            readStorage();
            setActive(window.location.pathname);

            document.addEventListener('astro:page-load', function () {
                setActive(window.location.pathname);
            });

            window.__adminTabManager = {
                close: closeTab,
                closeOthers: closeOthers,
                closeCurrentAndNavigate: closeCurrentAndNavigate,
                navigate: navigate,
                refresh: function () {
                    window.location.reload();
                }
            };

            renderTabs();
            return true;
        }

        var initialized = setupTabBar();
        if (!initialized) {
            var onReady = function () {
                if (setupTabBar()) {
                    document.removeEventListener('DOMContentLoaded', onReady);
                    document.removeEventListener('astro:page-load', onReady);
                }
            };
            document.addEventListener('DOMContentLoaded', onReady);
            document.addEventListener('astro:page-load', onReady);
        }
    })();
}
