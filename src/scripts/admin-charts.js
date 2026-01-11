/**
 * 后台图表管理逻辑
 * 封装 Chart.js 初始化和更新
 */
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

export function initDashboardCharts(chartsData) {
    if (!chartsData) return;

    const isDark = document.documentElement.classList.contains('dark');
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)';
    const textColor = isDark ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)';

    // 获取主题色（从 CSS 变量）
    const style = getComputedStyle(document.documentElement);
    const hue = style.getPropertyValue('--primary-hue').trim() || '252';
    const hueNum = parseFloat(hue);
    const primaryColor = `hsl(${hueNum}, 82%, 56%)`;
    const primaryColorLight = `hsla(${hueNum}, 82%, 56%, 0.1)`;

    // Daily Chart - 发布趋势
    const dailyCtx = document.getElementById('dailyChart');
    if (dailyCtx && chartsData.daily) {
        const labels = chartsData.daily.map(d => {
            const date = new Date(d.date);
            return (date.getMonth() + 1) + '/' + date.getDate();
        });
        const counts = chartsData.daily.map(d => d.count);

        new Chart(dailyCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '发布文章数',
                    data: counts,
                    borderColor: primaryColor,
                    backgroundColor: primaryColorLight,
                    fill: true,
                    tension: 0.4,
                    pointRadius: counts.length > 20 ? 0 : 3,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: isDark ? 'rgba(24, 24, 27, 0.9)' : 'rgba(255, 255, 255, 0.9)',
                        titleColor: isDark ? '#fff' : '#000',
                        bodyColor: isDark ? '#fff' : '#000',
                        borderColor: gridColor,
                        borderWidth: 1,
                        padding: 10,
                        displayColors: false,
                        callbacks: {
                            label: (context) => `发布: ${context.parsed.y} 篇`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: gridColor, drawBorder: false },
                        ticks: { color: textColor, maxRotation: 0, autoSkipPadding: 20 }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: gridColor, drawBorder: false },
                        ticks: { color: textColor, stepSize: 1 }
                    }
                },
                interaction: { intersect: false, mode: 'index' }
            }
        });
    }

    // Login Chart - 登录统计
    const loginCtx = document.getElementById('loginChart');
    if (loginCtx && chartsData.login) {
        const loginLabels = chartsData.login.map(d => {
            const date = new Date(d.date);
            return (date.getMonth() + 1) + '/' + date.getDate();
        });
        const successData = chartsData.login.map(d => d.success);
        const failedData = chartsData.login.map(d => d.failed);

        new Chart(loginCtx, {
            type: 'bar',
            data: {
                labels: loginLabels,
                datasets: [
                    {
                        label: '成功',
                        data: successData,
                        backgroundColor: 'rgba(34, 197, 94, 0.8)',
                        borderRadius: 4
                    },
                    {
                        label: '失败',
                        data: failedData,
                        backgroundColor: 'rgba(239, 68, 68, 0.8)',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        align: 'end',
                        labels: { color: textColor, usePointStyle: true, padding: 20 }
                    },
                    tooltip: {
                        backgroundColor: isDark ? 'rgba(24, 24, 27, 0.9)' : 'rgba(255, 255, 255, 0.9)',
                        titleColor: isDark ? '#fff' : '#000',
                        bodyColor: isDark ? '#fff' : '#000',
                        borderColor: gridColor,
                        borderWidth: 1,
                        padding: 10
                    }
                },
                scales: {
                    x: {
                        grid: { display: false, drawBorder: false },
                        ticks: { color: textColor }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: gridColor, drawBorder: false },
                        ticks: { color: textColor, stepSize: 1 }
                    }
                }
            }
        });
    }
}
