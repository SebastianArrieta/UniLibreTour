/* ============================================================================
   UniLibreTour — UI renderers y Componentes de interfaz
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
        return '<span class="text-xs px-2 py-0.5 rounded font-mono" style="background:var(--primary-soft);color:var(--primary);border:1px solid var(--primary-border)">' + esc(label) + '</span>';
    }

    function tagList(tags) {
        if (!tags || !tags.length) return '';
        return '<div class="flex flex-wrap gap-1.5">' + tags.map(function (t) {
            return '<span class="text-xs px-2 py-0.5 rounded font-mono" style="background:var(--surface-1);color:var(--muted-foreground);border:1px solid var(--border-subtle)">#' + esc(t) + '</span>';
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
            '<div class="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center text-xs" style="background:var(--primary-soft);color:var(--primary)">' + esc((item.author || '?').charAt(0)) + '</div>' +
            '<span class="text-xs truncate" style="color:var(--muted-foreground)">' + esc(item.author) + '</span>' +
            '</div>' +
            '<div class="flex items-center gap-1 text-xs font-medium opacity-0 -translate-x-1 transition-all duration-300 group-hover:opacity-100 group-hover:translate-x-0" style="color:var(--primary)">Ver detalle <span aria-hidden="true">→</span></div>' +
            '</div>' +
            '</article>' +
            '</a>';
    }

    function emptyState(message, icon) {
        var iconHtml = '<i class="fa-solid fa-folder-open text-3xl opacity-30"></i>';
        if (icon) {
            if (icon.indexOf('<') !== -1) {
                iconHtml = icon;
            } else if (icon.indexOf('fa-') !== -1) {
                iconHtml = '<i class="' + esc(icon) + ' text-3xl opacity-30"></i>';
            } else {
                iconHtml = '<span class="text-3xl opacity-30">' + icon + '</span>';
            }
        }
        return '<div class="ui-empty" role="status">' +
            iconHtml +
            '<p style="color:var(--muted-foreground)">' + esc(message) + '</p>' +
            '</div>';
    }

    function statCard(cfg) {
        cfg = cfg || {};
        var color = cfg.color || 'var(--primary)';
        var value = cfg.value === undefined || cfg.value === null ? '—' : Number(cfg.value).toLocaleString('es-CO');
        var sub = cfg.sub ? '<div class="text-xs mt-1" style="color:var(--muted-foreground)">' + esc(cfg.sub) + '</div>' : '';
        return '<div class="museum-card rounded p-5">' +
            '<div class="text-xs font-mono uppercase tracking-widest mb-1" style="color:var(--muted-foreground)">' + esc(cfg.label || '') + '</div>' +
            '<div class="font-serif text-3xl font-bold" style="color:' + color + '">' + value + '</div>' + sub +
            '</div>';
    }

    function sectionHeader(cfg) {
        cfg = cfg || {};
        var label = cfg.label ? '<div class="text-xs font-mono uppercase tracking-widest mb-2" style="color:var(--primary)">' + esc(cfg.label) + '</div>' : '';
        var subtitle = cfg.subtitle ? '<p class="mt-2 text-base" style="color:var(--muted-foreground)">' + esc(cfg.subtitle) + '</p>' : '';
        return '<div class="mb-8">' + label +
            '<h2 class="font-serif text-3xl md:text-4xl font-bold leading-tight" style="color:var(--foreground)">' + esc(cfg.title || '') + '</h2>' + subtitle +
            '</div>';
    }

    function cardSkeleton() {
        return '<div class="museum-card rounded overflow-hidden ui-skeleton" aria-hidden="true">' +
            '<div class="h-44"></div>' +
            '<div class="p-4 flex flex-col gap-3">' +
            '<div class="h-3 w-20 rounded ui-skeleton"></div>' +
            '<div class="h-5 w-full rounded ui-skeleton"></div>' +
            '<div class="h-4 w-3/4 rounded ui-skeleton"></div>' +
            '</div></div>';
    }

    function stepIndicator(steps, currentStep) {
        var out = '<div class="flex items-center gap-2 mb-8">';
        (steps || []).forEach(function (label, i) {
            var num = i + 1;
            var isCompleted = currentStep > num;
            var isActive = currentStep >= num;
            var circleBg = isCompleted ? '#22c55e' : isActive ? 'var(--primary)' : 'var(--surface-2)';
            var circleColor = isActive ? 'var(--primary-foreground)' : 'var(--muted-foreground)';
            var circleBorder = isActive ? 'none' : '1px solid var(--border-subtle)';
            out += '<div class="flex items-center gap-2 flex-1">' +
                '<div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-mono font-bold transition-all" style="background:' + circleBg + ';color:' + circleColor + ';border:' + circleBorder + '">' +
                (isCompleted ? '<i class="fa-solid fa-check text-xs"></i>' : num) + '</div>' +
                '<span class="text-xs hidden md:inline truncate" style="color:' + (isActive ? 'var(--secondary-foreground)' : 'var(--muted-foreground)') + '">' + esc(label) + '</span>';
            if (num < steps.length) {
                out += '<div class="h-px flex-1 mx-2" style="background:' + (isCompleted ? '#22c55e' : isActive ? 'var(--primary)' : 'var(--border-subtle)') + '"></div>';
            }
            out += '</div>';
        });
        return out + '</div>';
    }

    function checkboxHtml(cfg) {
        cfg = cfg || {};
        var checked = !!cfg.checked;
        return '<label class="flex items-start gap-3 cursor-pointer group">' +
            '<button type="button" class="w-5 h-5 rounded flex-shrink-0 mt-0.5 flex items-center justify-center transition-all" role="checkbox" aria-checked="' + (checked ? 'true' : 'false') + '" aria-label="' + esc(cfg.label || '') + '" data-checkbox="' + esc(cfg.name || '') + '" data-value="' + esc(cfg.value || '') + '" style="background:' + (checked ? 'var(--primary)' : 'var(--surface-1)') + ';border:1px solid ' + (checked ? 'var(--primary)' : 'var(--border-subtle)') + '">' +
            (checked ? '<i class="fa-solid fa-check text-xs text-black font-bold" aria-hidden="true"></i>' : '') + '</button>' +
            '<span class="text-sm" style="color:var(--secondary-foreground)">' + esc(cfg.label) + '</span></label>';
    }

    var TYPE_META = {
        success: { cls: 'ui-toast-success', icon: 'fa-check', role: 'status' },
        err: { cls: 'ui-toast-error', icon: 'fa-triangle-exclamation', role: 'alert' },
        error: { cls: 'ui-toast-error', icon: 'fa-triangle-exclamation', role: 'alert' },
        info: { cls: 'ui-toast-info', icon: 'fa-circle-info', role: 'status' }
    };

    function toastRegion() {
        var region = document.getElementById('ui-toast-region');
        if (!region) {
            region = document.createElement('div');
            region.id = 'ui-toast-region';
            region.className = 'ui-toast-region';
            region.setAttribute('role', 'region');
            region.setAttribute('aria-label', 'Notificaciones');
            region.setAttribute('aria-live', 'polite');
            document.body.appendChild(region);
        }
        return region;
    }

    function dismissToast(box) {
        if (!box || box.classList.contains('is-leaving')) return;
        box.classList.add('is-leaving');
        setTimeout(function () { if (box.parentNode) box.parentNode.removeChild(box); }, 220);
    }

    function toast(msg, type) {
        var conf = TYPE_META[type] || TYPE_META.info;
        var box = document.createElement('div');
        box.className = 'ui-toast ' + conf.cls;
        box.setAttribute('role', conf.role);
        box.innerHTML = '<i class="fa-solid ' + conf.icon + ' text-base mt-0.5" aria-hidden="true"></i>' +
            '<span>' + esc(msg) + '</span>' +
            '<button type="button" aria-label="Cerrar notificación"><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>';

        var closer = box.querySelector('button');
        closer.addEventListener('click', function () { dismissToast(box); });

        var timer = setTimeout(function () { dismissToast(box); }, 4200);
        box.addEventListener('mouseenter', function () { clearTimeout(timer); });
        box.addEventListener('mouseleave', function () {
            timer = setTimeout(function () { dismissToast(box); }, 1800);
        });

        toastRegion().appendChild(box);
        return box;
    }

    function focusable(modal) {
        return Array.prototype.slice.call(modal.querySelectorAll(
            'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        )).filter(function (el) { return el.offsetParent !== null || el === document.activeElement; });
    }

    function bindModal(modal) {
        if (!modal || modal.__uiModalBound) return modal;
        modal.__uiModalBound = true;
        modal.setAttribute('role', modal.getAttribute('role') || 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.addEventListener('click', function (e) {
            if (e.target === modal) closeModal(modal);
        });
        return modal;
    }

    function openModal(modal) {
        if (!modal) return;
        bindModal(modal);
        modal.__uiLastFocus = document.activeElement;
        modal.classList.remove('hidden');
        modal.style.display = 'flex';
        document.body.classList.add('ui-modal-open');

        modal.__uiTrap = function (e) {
            if (e.key === 'Escape') {
                e.preventDefault();
                closeModal(modal);
                return;
            }
            if (e.key !== 'Tab') return;
            var items = focusable(modal);
            if (!items.length) return;
            var first = items[0];
            var last = items[items.length - 1];
            if (e.shiftKey && document.activeElement === first) {
                e.preventDefault();
                last.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        };
        document.addEventListener('keydown', modal.__uiTrap);

        var firstFocus = modal.querySelector('[data-autofocus]') || modal.querySelector('[autofocus]') || focusable(modal)[0];
        if (firstFocus) setTimeout(function () { firstFocus.focus(); }, 30);
    }

    function closeModal(modal) {
        if (!modal) return;
        modal.classList.add('hidden');
        modal.style.display = 'none';
        document.body.classList.remove('ui-modal-open');
        if (modal.__uiTrap) {
            document.removeEventListener('keydown', modal.__uiTrap);
            modal.__uiTrap = null;
        }
        if (modal.__uiLastFocus && typeof modal.__uiLastFocus.focus === 'function') {
            modal.__uiLastFocus.focus();
        }
        modal.__uiLastFocus = null;
    }

    function confirmDialog(opts) {
        opts = opts || {};
        return new Promise(function (resolve) {
            var wrap = document.createElement('div');
            wrap.className = 'ui-modal hidden';
            wrap.innerHTML =
                '<div class="museum-card w-full max-w-sm rounded-xl p-6 text-center" style="border:1px solid var(--border);background:var(--card)">' +
                '<div class="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-4" style="background:var(--primary-soft);border:2px solid var(--primary-border)">' +
                '<i class="fa-solid ' + (opts.icon || 'fa-triangle-exclamation') + ' text-xl" style="color:var(--primary)" aria-hidden="true"></i></div>' +
                '<h3 class="font-serif text-lg font-bold mb-1.5" style="color:var(--foreground)">' + esc(opts.title || '¿Confirmar acción?') + '</h3>' +
                '<p class="text-sm mb-6 leading-relaxed" style="color:var(--muted-foreground)">' + esc(opts.message || '') + '</p>' +
                '<div class="flex items-center justify-center gap-3">' +
                '<button type="button" data-ui-cancel class="flex-1 py-2.5 px-4 rounded-lg text-xs font-medium btn-outline-primary">' + esc(opts.cancelLabel || 'Cancelar') + '</button>' +
                '<button type="button" data-ui-ok class="flex-1 py-2.5 px-4 rounded-lg text-xs font-semibold btn-primary">' + esc(opts.confirmLabel || 'Confirmar') + '</button>' +
                '</div></div>';

            document.body.appendChild(wrap);
            wrap.querySelector('[data-ui-cancel]').addEventListener('click', function () {
                closeModal(wrap);
                wrap.remove();
                resolve(false);
            });
            wrap.querySelector('[data-ui-ok]').addEventListener('click', function () {
                closeModal(wrap);
                wrap.remove();
                resolve(true);
            });
            openModal(wrap);
        });
    }

    function setBusy(button, busy, busyLabel) {
        if (!button) return;
        if (busy) {
            if (!button.dataset.uiOriginal) button.dataset.uiOriginal = button.innerHTML;
            button.disabled = true;
            button.setAttribute('aria-busy', 'true');
            button.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin" aria-hidden="true"></i> ' + esc(busyLabel || 'Procesando…');
        } else {
            button.disabled = false;
            button.removeAttribute('aria-busy');
            if (button.dataset.uiOriginal) {
                button.innerHTML = button.dataset.uiOriginal;
                delete button.dataset.uiOriginal;
            }
        }
    }

    var toastFn = toast;

    global.toast = toastFn;

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
        toast: toastFn,
        openModal: openModal,
        closeModal: closeModal,
        bindModal: bindModal,
        confirm: confirmDialog,
        setBusy: setBusy,
    };

})(window);