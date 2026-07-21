# فاهمك — Design System (Colors + Icons)

Derived from the approved logo: white wordmark on light sage green (`#C0DD97`–`#EAF3DE` range). Everything below extends that base into a usable UI palette — not a fresh color decision, a derivation of it, so the logo and the product feel like the same object.

## 1. Color Palette

### 1.1 Primary — green ramp

The logo background sits mid-ramp. The rest of the ramp is generated around it so header/footer/button surfaces stay in the same hue family instead of introducing a second green.

| Token | Hex | Role |
|---|---|---|
| `--green-50` | `#F5F9EE` | Subtle tinted backgrounds (hover states on light surfaces) |
| `--green-100` | `#EAF3DE` | Card backgrounds, badges |
| `--green-200` | `#C0DD97` | **Logo background** — light accents, chips, secondary buttons |
| `--green-400` | `#97C459` | Active/hover state for the 200 stop, mid-emphasis fills |
| `--green-600` | `#639922` | Borders on green surfaces, icon strokes on light bg |
| `--green-800` | `#27500A` | **Primary dark** — header, nav, primary buttons, footer |
| `--green-900` | `#173404` | Text-on-green-50/100, deepest emphasis, pressed states |

Reasoning: `--green-200` is fixed to the logo's exact background so any UI element that needs to "match the logo" pulls this token, not a guessed hex. `--green-800` replaces the earlier `#1B4332` recommendation — that was a placeholder before the logo existed; now the palette is built around the confirmed asset instead of the other way around.

### 1.2 Accent — gold

| Token | Hex | Role |
|---|---|---|
| `--gold-100` | `#FAEEDA` | Highlight backgrounds (retrieved-chunk markers in chat) |
| `--gold-400` | `#EF9F27` | Active accent, status dot, citation badges |
| `--gold-800` | `#633806` | Text on gold-100/400 backgrounds |

Use sparingly — one accent color, reserved for things the user should notice first (a citation, an active state, an in-progress indicator), never as a decorative fill.

### 1.3 Neutrals — text & structure

| Token | Hex | Role |
|---|---|---|
| `--neutral-0` | `#FFFFFF` | Wordmark white, text on green-600+/gold-400+ |
| `--neutral-50` | `#FAF9F6` | App page background (off-white, not pure white) |
| `--neutral-200` | `#E2E0D8` | Hairline borders, dividers |
| `--neutral-500` | `#8A8A7F` | Secondary/muted text, placeholders |
| `--neutral-800` | `#2B2B26` | Primary body text |

### 1.4 Semantic — document/chat pipeline status

Your schema has a real, fixed state machine (`document.status`: `uploaded → chunking → embedding → indexed | failed`) — map it to color once, reuse everywhere a status badge appears, so the meaning stays consistent app-wide.

| Status | Token | Hex | Notes |
|---|---|---|---|
| `uploaded` | `--status-neutral` | `#8A8A7F` | Waiting, no action yet |
| `chunking` / `embedding` | `--status-pending` | `#EF9F27` (gold-400) | In-progress — reuse the accent, don't invent a new color for "processing" |
| `indexed` | `--status-success` | `#639922` (green-600) | Reuse primary ramp — success = "on-brand," not a generic UI green |
| `failed` | `--status-danger` | `#C1443A` | New — only true "outside the palette" color, reserved exclusively for errors so it stays alarming |

### 1.5 Contrast reference

| Foreground | Background | Ratio | Passes |
|---|---|---|---|
| `--neutral-0` (white) | `--green-800` | ~9.8:1 | AAA |
| `--neutral-0` (white) | `--green-200` (logo bg) | ~1.6:1 | **Fails** — this is why the logo itself uses a bold/thick typeface to carry contrast structurally, not color contrast. Do not set body text in white on `--green-200` anywhere in the UI. |
| `--neutral-800` | `--neutral-50` | ~11.9:1 | AAA |
| `--gold-800` | `--gold-100` | ~7.1:1 | AAA |

The one real constraint this creates: `--green-200` (your logo's own background) is a brand color, not a text-safe surface. Use it for chips/badges/logo contexts with dark text or no text, never as a background behind white or light UI copy.

---

## 2. Icon Sources

For an Arabic-first, RTL product, icon choice matters beyond style — check each set's stance on **directional icons** (arrows, chevrons, "back," playback controls) needing a mirrored variant in RTL layouts.

| Source | Style | License | Notes |
|---|---|---|---|
| [Tabler Icons](https://tabler.io/icons) | Outline, consistent 24px grid, 5,900+ icons | MIT (free, commercial OK) | Matches the geometric/technical character of the logo well; large enough set to cover document/chat/upload/status icons without gaps |
| [Phosphor Icons](https://phosphoricons.com) | 6 weights (thin → bold, duotone) per icon | MIT | Weight flexibility is useful if you want icon boldness to echo the logo's bold strokes specifically |
| [Lucide](https://lucide.dev) | Outline, fork of Feather, actively maintained | ISC (permissive) | Clean, minimal — safer "quiet" choice if icons should recede behind the green/gold palette rather than compete with it |
| [Heroicons](https://heroicons.com) | Outline + solid, by the Tailwind team | MIT | Small set (~300) but every icon is production-polished; pairs natively if the frontend uses Tailwind |
| [Iconoir](https://iconoir.com) | Outline, 1,600+, includes some Arabic/RTL-conscious sets | MIT | Worth checking directly for RTL-mirrored variants of directional icons |
| [Remix Icon](https://remixicon.com) | Outline + filled pairs for every icon | Apache 2.0 | Useful if you want an active/inactive state per icon (e.g. filled = selected chat, outline = unselected) |

**Recommendation**: Tabler as the primary set — geometric, consistent stroke weight close in spirit to the Reem Kufi/kufic logo character, MIT-licensed, and large enough to cover every icon this app will need (upload, file, chunk/vector, chat bubble, send, status states, settings, user). Fall back to Phosphor for any icon Tabler lacks, since both share an outline-first visual language and won't clash if mixed.

**RTL check before locking a set**: search the chosen library's docs for "RTL" or "mirror" explicitly — most outline sets require you to flip directional icons yourself via CSS (`transform: scaleX(-1)`) rather than shipping pre-mirrored assets. Confirm this before building the icon component wrapper so mirroring is handled once, centrally, not per-usage.
