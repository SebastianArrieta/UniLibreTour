/* ============================================================================
   UniLibreTour — UI renderers (port del prototipo React: src/components/UI.tsx)
   Builders que devuelven HTML como string. Cada ficha/tarjeta se emite como un
   <a href> para navegación server-side real.

   API global: window.UI
   - UI.statusBadge(status)
   - UI.categoryBadge(category)
   - UI.tagList(tags)
   - UI.contentCard(item, { showStatus, baseHref })  -> HTML string
   - UI.emptyState(message, icon)
   - UI.statCard({ label, value, sub, color })
   - UI.sectionHeader({ label, title, subtitle })
   - UI.cardSkeleton()
   - UI.stepIndicator(steps, currentStep)
   - UI.checkboxHtml({ checked, name, label, value })
   - UI.fmtDate(dateStr)  -> 'sep 2026' (es-CO)
   - UI.readonly helpers: STATUS_LABELS, CATEGORY_LABELS, ICONS
   ============================================================================ */

(function (global) {
    'use strict';

    var STATUS_CONFIG = {
        publicado:   { label: 'Publicado',     color: '#22c55e', bg: 'rgba(34,197,94,0.1)' },
        pendiente:   { label: 'En Revisión',   color: '#f97316', bg: 'rgba(249,115,22,0.1)' },
        institucional: { label: 'Institucional', color: '#3b82f6', bg: 'rgba(59,130,246,0.1)' },
        devuelto:    { label: 'Devuelto',      color: '#ef4444', bg: 'rgba(239,68,68,0.1)' },
    };

    var CATEGORY_LABELS = {
        historia: 'Historia', investigacion: 'Investigación', proyectos: 'Proyectos',
        eventos: 'Eventos', logros: 'Logros', docentes: 'Docentes',
    };

    function esc(s) {
        if (s === null || s === undefined) return '';
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function fmtDate(dateStr) {
        try {
            var d = new Date(dateStr);
            if (isNaN(d.getTime())) return '';
            return d.toLocaleDateString('es-CO', { year: 'numeric', month: 'short' });
        } catch (e) { return ''; }
    }

    function statusBadge(status) {
        var c = STATUS_CONFIG[status] || STATUS_CONFIG.pendiente;
        return '<span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-mono font-medium" style="color:' + c.color + ';background:' + c.bg + ';border:1px solid ' + c.color + '30">' +
            '<span class="w-1.5 h-1.5 rounded-full flex-shrink-0" style="background:' + c.color + '"></span>' + c.label + '</span>';
    }

    function categoryBadge(category) {
        var label = CATEGORY_LABELS[category] || category || '';
        return '<span class="text-xs px-2 py-0.5 rounded font-mono" style="background:rgba(211,47,47,0.1);color:#d32f2f;border:1px solid rgba(211,47,47,0.2)">' + esc(label) + '</span>';
    }

    function tagList(tags) {
        if (!tags || !tags.length) return '';
        return '<div class="flex flex-wrap gap-1.5">' + tags.map(function (t) {
            return '<span class="text-xs px-2 py-0.5 rounded font-mono" style="background:rgba(255,255,255,0.04);color:var(--muted-foreground);border:1px solid rgba(255,255,255,0.08)">#' + esc(t) + '</span>';
        }).join('') + '</div>';
    }

    function contentCard(item, opts) {
        opts = opts || {};
        var showStatus = !!opts.showStatus;
        var itemId = item && item.id ? String(item.id) : '';
        var href = (opts.baseHref || '/detalle/') + encodeURIComponent(itemId);
        var dateStr = fmtDate(item.date);
        var status = showStatus ? '<div class="absolute top-3 left-3">' + statusBadge(item.status) + '</div>' : '';

        return '<a href="' + href + '" class="group block" data-card-id="' + esc(itemId) + '">' +
            '<article class="museum-card content-card rounded overflow-hidden cursor-pointer flex flex-col h-full">' +
            '<div class="relative overflow-hidden h-44 bg-gray-900">' +
            '<img src="' + esc(item.image || '') + '" alt="' + esc(item.title || '') + '" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" loading="lazy">' +
            '<div class="absolute inset-0" style="background:linear-gradient(to top, rgba(0,0,0,0.7) 0%, transparent 60%)"></div>' + status +
            '</div>' +
            '<div class="p-4 flex flex-col flex-1 gap-2">' +
            '<div class="flex items-start justify-between gap-2">' + categoryBadge(item.category) +
            '<span class="text-xs font-mono flex-shrink-0" style="color:var(--muted-foreground)">' + esc(dateStr) + '</span>' +
            '</div>' +
            '<h3 class="font-serif text-base font-semibold leading-snug line-clamp-2">' + esc(item.title) + '</h3>' +
            '<p class="text-sm leading-relaxed line-clamp-2 flex-1" style="color:var(--muted-foreground)">' + esc(item.description) + '</p>' +
            '<div class="flex items-center gap-1.5 mt-1">' +
            '<div class="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center text-xs" style="background:rgba(211,47,47,0.15);color:#d32f2f">' + esc((item.author || '?').charAt(0)) + '</div>' +
            '<span class="text-xs truncate" style="color:var(--muted-foreground)">' + esc(item.author) + '</span>' +
            '</div>' +
            '<div class="flex items-center gap-1 text-xs font-medium text-[#d32f2f] opacity-0 -translate-x-1 transition-all duration-300 group-hover:opacity-100 group-hover:translate-x-0">Ver detalle <span aria-hidden="true">→</span></div>' +
            '</div>' +
            '</article>' +
            '</a>';
    }

    function emptyState(message, icon) {
        return '<div class="flex flex-col items-center justify-center py-20 text-center gap-3">' +
            '<span class="text-4xl opacity-30">' + (icon || '📂') + '</span>' +
            '<p style="color:var(--muted-foreground)">' + esc(message) + '</p>' +
            '</div>';
    }

    function statCard(cfg) {
        cfg = cfg || {};
        var color = cfg.color || '#d32f2f';
        var value = cfg.value === undefined || cfg.value === null ? '—' : Number(cfg.value).toLocaleString('es-CO');
        var sub = cfg.sub ? '<div class="text-xs mt-1" style="color:var(--muted-foreground)">' + esc(cfg.sub) + '</div>' : '';
        return '<div class="museum-card rounded p-5">' +
            '<div class="text-xs font-mono uppercase tracking-widest mb-1" style="color:var(--muted-foreground)">' + esc(cfg.label || '') + '</div>' +
            '<div class="font-serif text-3xl font-bold" style="color:' + color + '">' + value + '</div>' + sub +
            '</div>';
    }

    function sectionHeader(cfg) {
        cfg = cfg || {};
        var label = cfg.label ? '<div class="text-xs font-mono uppercase tracking-widest mb-2" style="color:#d32f2f">' + esc(cfg.label) + '</div>' : '';
        var subtitle = cfg.subtitle ? '<p class="mt-2 text-base" style="color:var(--muted-foreground)">' + esc(cfg.subtitle) + '</p>' : '';
        return '<div class="mb-8">' + label +
            '<h2 class="font-serif text-3xl md:text-4xl font-bold leading-tight" style="color:var(--foreground)">' + esc(cfg.title || '') + '</h2>' + subtitle +
            '</div>';
    }

    function cardSkeleton() {
        return '<div class="museum-card rounded overflow-hidden animate-pulse">' +
            '<div class="h-44" style="background:rgba(255,255,255,0.04)"></div>' +
            '<div class="p-4 flex flex-col gap-3">' +
            '<div class="h-3 w-20 rounded" style="background:rgba(255,255,255,0.06)"></div>' +
            '<div class="h-5 w-full rounded" style="background:rgba(255,255,255,0.06)"></div>' +
            '<div class="h-4 w-3/4 rounded" style="background:rgba(255,255,255,0.04)"></div>' +
            '</div></div>';
    }

    function stepIndicator(steps, currentStep) {
        var out = '<div class="flex items-center gap-2 mb-8">';
        (steps || []).forEach(function (label, i) {
            var num = i + 1;
            var isCompleted = currentStep > num;
            var isActive = currentStep >= num;
            var circleBg = isCompleted ? '#22c55e' : isActive ? 'var(--primary)' : 'rgba(255,255,255,0.06)';
            var circleColor = isActive ? 'var(--background)' : 'var(--muted-foreground)';
            var circleBorder = isActive ? 'none' : '1px solid rgba(255,255,255,0.1)';
            out += '<div class="flex items-center gap-2 flex-1">' +
                '<div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-mono font-bold transition-all" style="background:' + circleBg + ';color:' + circleColor + ';border:' + circleBorder + '">' +
                (isCompleted ? '✓' : num) + '</div>' +
                '<span class="text-xs hidden md:inline truncate" style="color:' + (isActive ? 'var(--secondary-foreground)' : 'var(--muted-foreground)') + '">' + esc(label) + '</span>';
            if (num < steps.length) {
                out += '<div class="h-px flex-1 mx-2" style="background:' + (isCompleted ? '#22c55e' : isActive ? 'var(--primary)' : 'rgba(255,255,255,0.1)') + '"></div>';
            }
            out += '</div>';
        });
        return out + '</div>';
    }

    function checkboxHtml(cfg) {
        cfg = cfg || {};
        return '<label class="flex items-start gap-3 cursor-pointer group">' +
            '<div class="w-5 h-5 rounded flex-shrink-0 mt-0.5 flex items-center justify-center transition-all" role="checkbox" aria-checked="' + (cfg.checked ? 'true' : 'false') + '" data-checkbox="' + esc(cfg.name || '') + '" data-value="' + esc(cfg.value || '') + '" style="background:' + (cfg.checked ? 'var(--primary)' : 'rgba(255,255,255,0.04)') + ';border:1px solid ' + (cfg.checked ? 'var(--primary)' : 'rgba(255,255,255,0.15)') + '">' +
            (cfg.checked ? '<span class="text-xs text-black font-bold">✓</span>' : '') + '</div>' +
            '<span class="text-sm" style="color:var(--secondary-foreground)">' + esc(cfg.label) + '</span></label>';
    }

    global.UI = {
        STATUS_CONFIG: STATUS_CONFIG,
        CATEGORY_LABELS: CATEGORY_LABELS,
        esc: esc,
        fmtDate: fmtDate,
        statusBadge: statusBadge,
        categoryBadge: categoryBadge,
        tagList: tagList,
        contentCard: contentCard,
        emptyState: emptyState,
        statCard: statCard,
        sectionHeader: sectionHeader,
        cardSkeleton: cardSkeleton,
        stepIndicator: stepIndicator,
        checkboxHtml: checkboxHtml,
    };

})(window);