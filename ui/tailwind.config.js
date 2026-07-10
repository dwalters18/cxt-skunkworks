/**
 * CXT design language:
 *   headings Poppins, body Inter (self-hosted via @fontsource)
 *   primary green #3F7719, #75C158 on dark surfaces
 *   dark theme first, 16px card radius (rounded-card)
 */
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./src/**/*.{html,js,ts,jsx,tsx}'],
  theme: {
    fontFamily: {
      sans: ['Inter', 'system-ui', 'sans-serif'],
      heading: ['Poppins', 'Inter', 'sans-serif'],
      mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
    },
    extend: {
      colors: {
        // Semantic tokens are CSS-variable-driven so the whole app flips with
        // the `dark` class (see :root/.dark in src/index.css). Components use
        // bg-surface / text-foreground / border-accent etc. directly — no
        // dark: prefixes needed — and the Settings toggle just works.
        //
        // Primary follows the CXT spec: deep #3F7719 on light surfaces,
        // #75C158 on dark. Fixed shades stay available (primary-600 etc).
        primary: {
          DEFAULT: 'rgb(var(--c-primary) / <alpha-value>)',
          100: '#C7E5B3',
          300: '#75C158',
          600: '#3F7719',
          700: '#315D13',
        },
        background: 'rgb(var(--c-background) / <alpha-value>)',
        surface: 'rgb(var(--c-surface) / <alpha-value>)',
        'surface-raised': 'rgb(var(--c-surface-raised) / <alpha-value>)',
        foreground: 'rgb(var(--c-foreground) / <alpha-value>)',
        muted: 'rgb(var(--c-muted) / <alpha-value>)',
        accent: 'rgb(var(--c-accent) / <alpha-value>)', // hairline borders
        // Semantic (legible on both themes)
        danger: '#E5484D',
        warn: '#F5A524',
        info: '#3B9EDB',
      },
      borderRadius: {
        card: '16px',
      },
      boxShadow: {
        card: '0 1px 2px rgba(0,0,0,0.35), 0 8px 24px rgba(0,0,0,0.25)',
      },
    },
  },
  plugins: [],
};
