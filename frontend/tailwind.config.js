/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        base: 'var(--bg-base)',
        elevated: 'var(--bg-elevated)',
        surface: {
          1: 'var(--surface-1)',
          2: 'var(--surface-2)',
          3: 'var(--surface-3)',
        },
        border: {
          subtle: 'var(--border-subtle)',
          strong: 'var(--border-strong)',
        },
        brand: {
          orange: 'var(--brand-orange)',
          amber: 'var(--brand-amber)',
        },
        accent: {
          mint: 'var(--accent-mint)',
          green: 'var(--accent-green)',
        },
        txt: {
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          muted: 'var(--text-muted)',
        },
        danger: 'var(--danger)',
        warning: 'var(--warning)',
        info: 'var(--info)',
      },
      fontFamily: {
        sans: ['"Outfit"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      borderRadius: {
        card: '24px',
        inner: '16px',
        nav: '14px',
      },
      boxShadow: {
        glass: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.06)',
        'orange-glow': '0 8px 28px -6px rgba(255, 104, 3, 0.45)',
        'mint-glow': '0 8px 24px -6px rgba(48, 255, 172, 0.3)',
      },
    },
  },
  plugins: [],
}
