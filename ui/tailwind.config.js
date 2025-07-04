module.exports = {
  content: ["./src/**/*.{html,js,ts,jsx,tsx}"],
  theme: {
    fontFamily: {
      sans: ['Roboto', 'sans-serif'],
      heading: ['Montserrat', 'sans-serif'],
    },
    extend: {
      colors: {
        neutral: {
          0: "#FFFFFF",
          10: "#FBFBFB",
          30: "#EEEEEE",
          40: "#E2E2E2",
          50: "#C9C9C9",
          100: "#B9B9B9",
          200: "#AFAFAF",
          400: "#767676",
          500: "#595959",
          600: "#424242",
          800: "#292929",
          900: "#1E1E1E",
        },
        primary: {
          100: "#C7E5B3",
          300: "#75C158",
          600: "#3F7719",
          700: "#315D13",
        },
        secondary: {
          200: "#B0C2D4",
          600: "#596E80",
        },
        tertiary: {
          100: "#ECCBB0",
          200: "#E2B28A",
          500: "#C15701",
          700: "#893E01",
        },
        info: {
          100: "#BFD6E5",
          500: "#2F7CAC",
          700: "#21587A",
        },
        // Brand palette colors
        'logo-green': '#75C158',
        'logo-gray': '#646464',
        'text-gray': '#444444',
        'orange': '#C15701',
        'light-blue': '#BFD6E5',
        'secondary-green': '#63A44B',
        'powder-blue': '#96A5B3',
        'powder-green': '#ECF3E8',
        'medium-blue': '#2B719D',
        'ivory': '#F7F4E7',
        'pastel-yellow': '#EEEADD',
      },
    },
  },
  plugins: [],
};
