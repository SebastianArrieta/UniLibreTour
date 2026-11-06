# Brief de paleta — UniLibreTour

Paleta cálida e institucional: **rojo**, **dorado**, **marrón** y **negros/neutros cálidos**.
Cada color tiene **un solo trabajo**. Si un color aparece en todas partes, deja de destacar, y por eso el rojo se reserva para lo que de verdad importa.

Todo se define como variables CSS en `app/static/css/main.css` (bloques `:root` = tema oscuro y `[data-theme='light']` = tema claro).
**Nunca escribas un hex o `rgba()` directo en una plantilla**: usa `var(--token)` o una de las clases de abajo.

---

## 1. El rol de cada color

| Color | Para qué se usa | Ejemplos | No usar en |
|---|---|---|---|
| **Rojo** `--primary` | Acción e identidad | Botón principal (uno por vista), ítem activo del menú, enlaces, logo, errores y "Devuelto" | Bordes de tarjetas, fondos, etiquetas genéricas, títulos de sección |
| **Dorado** `--gold` | Valor y logro | Puntos, niveles, insignias ganadas, trofeos, premios, "Publicado", cifras del programa | Botones, textos largos |
| **Marrón** `--brown` | Estructura secundaria | Títulos pequeños de sección, categorías y etiquetas, iconos de tarjetas, fechas de agenda, "En revisión", botón secundario al pasar el mouse | Llamadas a la acción |
| **Neutros** `--foreground`, `--muted-foreground`, `--surface-*`, `--border*` | Todo lo demás | Fondos, tarjetas, texto, bordes, números de KPI | — |

> **Regla rápida:** si dudas, va en neutro. Máximo uno o dos acentos de color por tarjeta.

---

## 2. Tokens

| Token | Oscuro | Claro | Uso |
|---|---|---|---|
| `--background` | `#100e0c` | `#faf6ef` | Fondo de página |
| `--card` | `#1a1714` | `#ffffff` | Tarjetas |
| `--foreground` | `#f2ebe1` | `#1d1814` | Texto principal |
| `--secondary-foreground` | `#cbbfb0` | `#3f352c` | Texto secundario |
| `--muted-foreground` | `#9a8d7d` | `#6b5e50` | Texto de apoyo, etiquetas |
| `--primary` | `#ec5a4e` | `#b3261e` | Rojo para **texto e iconos** |
| `--primary-solid` | `#c62828` | `#b3261e` | Rojo para **rellenos** (botones, menú activo) |
| `--gold` | `#e6ad35` | `#8a6200` | Dorado |
| `--brown` | `#c4966a` | `#7d5634` | Marrón |
| `--border` / `--border-subtle` / `--border-strong` | neutro 9 % / 7 % / 16 % | neutro 10 % / 7 % / 18 % | Bordes (ya **no** son rojizos) |
| `--surface-1/2/3` | neutro 3 % / 6 % / 10 % | neutro 3 % / 5 % / 9 % | Fondos sutiles, chips, pistas de barras |

Cada acento tiene además `-soft` (fondo suave) y `-border` (borde): `--primary-soft`, `--gold-border`, `--brown-soft`, etc.
Medallas: `--medal-gold`, `--medal-silver`, `--medal-bronze`.

### Contraste verificado (WCAG AA: texto ≥ 4.5:1)

| Texto | Oscuro (sobre tarjeta) | Claro (sobre tarjeta) |
|---|---|---|
| `--foreground` | 15.1 | 17.6 |
| `--secondary-foreground` | 9.9 | 12.0 |
| `--muted-foreground` | 5.5 | 6.3 |
| `--primary` | 5.2 (4.65 sobre `-soft`) | 6.5 (5.75 sobre `-soft`) |
| `--gold` | 8.8 (7.4 sobre `-soft`) | 5.5 (4.65 sobre `-soft`) |
| `--brown` | 6.7 (5.8 sobre `-soft`) | 6.5 (5.75 sobre `-soft`) |
| Blanco sobre botón rojo | 5.6 | 6.5 |

---

## 3. Significados fijos

**Estados de contenido.** Siempre llevan **icono + texto**, nunca solo color. Usa el macro `status_badge()` o las clases `.status-*`.

| Estado | Color | Icono |
|---|---|---|
| Publicado | dorado | `fa-check` |
| En revisión | marrón | `fa-clock` |
| Institucional | neutro | `fa-building-columns` |
| Devuelto | rojo | `fa-arrow-rotate-left` |

**Tipos de hito (cronología y home):** fundación = rojo · logro = dorado · evento = marrón · investigación = neutro.
**Tipos de evento (calendario):** conferencia = rojo · graduación = dorado · taller = marrón · cultural = neutro.
**Podio y medallas:** 1.º oro, 2.º plata (neutro claro), 3.º bronce (marrón).
**KPIs:** el **número va en neutro**. Solo el icono lleva color según su significado; nada de tarjetas "arcoíris".
**Barras de progreso de puntos/nivel:** dorado sobre `--surface-2`.

---

## 4. Clases listas para usar

```html
<!-- Título pequeño de sección -->
<div class="eyebrow mb-2">Mantente informado</div>

<!-- Etiquetas -->
<span class="chip chip-brown">Investigación</span>
<span class="chip chip-gold">+120 pts</span>
<span class="chip chip-red">Devuelto</span>
<span class="chip chip-neutral">Borrador</span>

<!-- Cuadrito de icono -->
<div class="icon-tile icon-tile-gold w-8 h-8"><i class="fa-solid fa-trophy"></i></div>

<!-- Aviso informativo (antes era azul) -->
<div class="note-box rounded p-3 text-sm"><i class="fa-solid fa-circle-info"></i> Texto</div>

<!-- Texto con acento -->
<span class="text-gold">8.540</span>  <span class="text-brown">Líder del grupo</span>
```

Botones: `.btn-primary` (rojo, la acción principal) y `.btn-outline-primary` (secundario **neutro**, que toma marrón al pasar el mouse).

---

## 5. Excepciones permitidas

- Degradados oscuros sobre **fotografías** (`rgba(0,0,0,…)`) y texto blanco encima de ellas, para legibilidad.
- Texto blanco sobre rellenos sólidos (`--primary-solid`).

## 6. Checklist antes de subir cambios visuales

- [ ] No hay hex ni `rgba()` nuevos en `app/templates` ni `app/static/js` (salvo las excepciones).
- [ ] Hay un solo botón rojo principal por vista.
- [ ] Los estados llevan icono + texto.
- [ ] Revisado en **tema oscuro y claro**.
