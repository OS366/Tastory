/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./public/**/*.{html,js}",
    "./public/*.{html,js}",
    // If app.py generates HTML with Tailwind classes, we'll need to handle that separately
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        'gold': {
          50: '#FFFBEB',   // Lightest gold
          100: '#FEF3C7',  // Very light gold
          200: '#FDE68A',  // Lighter gold
          300: '#FFD700', // Light gold
          400: '#FFC107', // Medium gold
          500: '#FFB300', // Primary gold
          600: '#FFA000', // Dark gold
          700: '#FF8F00', // Darker gold
          800: '#FF6F00', // Very dark gold
          900: '#E65100', // Darkest gold
        },
        // Adding slate colors for glassmorphism
        'slate': {
          600: '#475569', // For dark:border-slate-600/30
          700: '#334155', // For dark:border-slate-700/40 and dark:bg-slate-700/20
          800: '#1e293b', // For dark:bg-slate-800/30
        }
      }
    },
  },
  plugins: [],
  safelist: [
    // Layout and spacing
    'bg-white', 'dark:bg-gray-800', 'bg-gray-50', 'dark:bg-gray-700',
    'p-6', 'p-4', 'p-3', 'mb-1', 'mb-2', 'mb-3', 'mb-4',
    'space-y-1', 'space-y-0.5', 'space-y-2',

    // Positioning & Sizing
    'relative', 'absolute', 'inset-0', 'z-10', 'z-40',
    'z-0', 'z-20', 'z-50',
    'z-30', 'top-2', 'right-2', '-top-1', '-right-1',
    'fixed', 'top-0', 'right-0', 'top-4', 'right-4', 'right-6',
    'h-80', 'w-full', 'h-full', 'w-80', 'h-5', 'w-5',
    'overflow-hidden', 'overflow-y-auto',
    'transform', 'translate-x-full', 'translate-x-0',

    // Glassmorphism, Gradients & Opacity
    'bg-white/30', 'bg-white/20',
    'dark:bg-slate-800/30', 'dark:bg-slate-700/20', 'bg-slate-800/90', 'dark:bg-black/80', 'dark:bg-black/90',
    'bg-gold-500/80', // Added for search button
    'backdrop-blur-md', 'backdrop-blur-sm', 'backdrop-blur-lg',
    'border', 'border-white/40', 'border-white/30',
    'dark:border-slate-700/40', 'dark:border-slate-600/30',
    'bg-gradient-to-t', 'from-black/80', 'via-black/60', 'to-transparent',

    'rounded-lg', 'shadow-lg', 'hover:shadow-xl', 'shadow-2xl',
    
    // Transitions
    'transition-shadow', 'transition-opacity', 'transition-transform',
    'duration-300', 'duration-200', 'ease-in-out',
    
    // Typography
    'text-xl', 'text-2xl', 'text-3xl', 'text-4xl', 'text-sm', 'font-bold', 'font-semibold',
    'text-gray-900', 'dark:text-gray-100',
    'text-gray-700', 'dark:text-gray-300',
    'text-gray-600', 'dark:text-gray-400',
    'text-white', 'text-white/80', 'text-gray-100', 'text-gray-200', 'text-gray-300',
    'drop-shadow-md', 'drop-shadow-sm',
    'leading-relaxed', 'leading-none',
    
    // Images
    'w-32', 'h-32', 'object-cover', 'rounded-full',
    'w-16', 'h-16', 'md:w-20', 'md:h-20',
    'border-4', 'border-gray-200', 'dark:border-gray-600',
    
    // Flexbox & Grid
    'flex', 'flex-col', 'flex-wrap', 'gap-2', 'gap-4', 'mt-auto',
    'justify-between', 'justify-center', 'items-center',
    'grid', 'grid-cols-1', 'md:grid-cols-2', 'gap-6', 'self-start',
    
    // Interactive states
    'opacity-60', 'opacity-100', 'hover:opacity-100', 'hover:text-white',
    'cursor-pointer', 'group', 'group-hover:text-gold-500', 'dark:group-hover:text-gold-400',
    'focus:outline-none', 'focus:ring-2', 'focus:ring-gold-400', 'focus:ring-opacity-50', 'focus:ring-opacity-75',
    'hover:scale-110',
    
    // Star rating classes
    'inline-flex', 'gap-1', 'ml-1',
    'text-gold-500', 'text-gold-500/50', 'text-gray-400',
    
    // Like button classes
    'p-2', 'bg-white/80', 'dark:bg-gray-800/80', 'backdrop-blur-sm',
    'text-red-500', 'text-xl',
    
    // Gold theme color classes
    'bg-gold-50', 'bg-gold-100', 'bg-gold-200', 'bg-gold-300', 'bg-gold-400', 'bg-gold-500', 'bg-gold-600', 'bg-gold-700',
    'text-gold-50', 'text-gold-100', 'text-gold-200', 'text-gold-300', 'text-gold-400', 'text-gold-500', 'text-gold-600', 'text-gold-700',
    'border-gold-50', 'border-gold-100', 'border-gold-200', 'border-gold-300', 'border-gold-400', 'border-gold-500', 'border-gold-600', 'border-gold-700',
    'hover:bg-gold-100', 'hover:bg-gold-200', 'hover:bg-gold-600', 'hover:bg-gold-700',
    'hover:text-gold-700', 'dark:hover:bg-gold-600',
    'dark:bg-gold-700', 'dark:border-gold-600', 'dark:text-gold-100',
    
    // Favorites badge and button classes
    'bg-red-500', 'hover:bg-red-600', 'text-xs', 'mr-2',
    'col-span-full', // For empty favorites message
    
    // Visibility
    'hidden',
    
    // Lists
    'list-decimal', 'list-inside', 'list-disc', 'pl-5',
    
    // Classes for recent search buttons (being more explicit)
    'bg-gold-100', 'text-gold-700', 'hover:bg-gold-200',
    'dark:bg-gold-700', 'dark:text-gold-100', 'dark:hover:bg-gold-600',
    'bg-gold-500', 'hover:bg-gold-600',
    'dark:bg-gold-500', 'dark:hover:bg-gold-400',
    'text-white', 'dark:text-white',
    'px-3', 'py-1', 'text-sm', 'rounded-full', // Already likely covered, but good to have if debugging
    
    // Classes for suggestions dropdown
    'hover:bg-gray-100', 'dark:hover:bg-gray-700',
    'text-gray-900', // Added for suggestion text light mode
    'dark:text-gray-200', 'dark:hover:text-gray-100', // Added for suggestion text dark mode & hover
    'px-4', 'py-2', // General padding, likely covered but good to note
    
    // Ensure all dark mode variants are included for gray and gold
    {
      pattern: /^(bg|text|border)-(gray|gold)-(50|100|200|300|400|500|600|700|800|900)$/,
      variants: ['dark'],
    },
    // Ensure dark mode variants for new slate colors with opacity are covered
    // For bg-slate-800/30, bg-slate-700/20
    // For border-slate-700/40, border-slate-600/30
    // Tailwind's default pattern matching for safelist might not catch these opacity modifiers easily
    // Explicitly listing them above is safer. The pattern below is for full color slate if needed.
    {
        pattern: /^(bg|text|border)-slate-(600|700|800)$/,
        variants: ['dark'],
    }
  ]
}

