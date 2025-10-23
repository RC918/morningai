/**
 * Image Optimization Utilities
 * Provides WebP support with fallbacks and lazy loading
 */

/**
 * Get optimized image source with WebP support
 * @param {string} src - Original image source
 * @param {Object} options - Optimization options
 * @returns {Object} - srcSet and fallback sources
 */
export function getOptimizedImageSrc(src, options = {}) {
  const {
    sizes = ['1x', '2x'],
    format = 'webp',
  } = options;

  const lastDotIndex = src.lastIndexOf('.');
  const baseName = src.substring(0, lastDotIndex);
  const extension = src.substring(lastDotIndex);

  const webpSources = sizes.map((size) => {
    const multiplier = size === '2x' ? '@2x' : '';
    return `${baseName}${multiplier}.${format} ${size}`;
  }).join(', ');

  const fallbackSources = sizes.map((size) => {
    const multiplier = size === '2x' ? '@2x' : '';
    return `${baseName}${multiplier}${extension} ${size}`;
  }).join(', ');

  return {
    webpSrcSet: webpSources,
    fallbackSrcSet: fallbackSources,
    src: `${baseName}${extension}`, // Default fallback
  };
}

/**
 * Check if browser supports WebP
 * @returns {Promise<boolean>}
 */
export function supportsWebP() {
  if (typeof window === 'undefined') return Promise.resolve(false);
  
  if (window.__webpSupport !== undefined) {
    return Promise.resolve(window.__webpSupport);
  }

  return new Promise((resolve) => {
    const webP = new Image();
    webP.onload = webP.onerror = function () {
      const support = webP.height === 2;
      window.__webpSupport = support;
      resolve(support);
    };
    webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
  });
}

/**
 * Lazy load image with IntersectionObserver
 * @param {HTMLImageElement} img - Image element
 * @param {Object} options - Observer options
 */
export function lazyLoadImage(img, options = {}) {
  const {
    rootMargin = '50px',
    threshold = 0.01,
  } = options;

  if (!('IntersectionObserver' in window)) {
    loadImage(img);
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        loadImage(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, {
    rootMargin,
    threshold,
  });

  observer.observe(img);
}

/**
 * Load image by setting src from data-src
 * @param {HTMLImageElement} img - Image element
 */
function loadImage(img) {
  const src = img.dataset.src;
  const srcset = img.dataset.srcset;

  if (srcset) {
    img.srcset = srcset;
  }
  if (src) {
    img.src = src;
  }

  img.classList.remove('lazy');
  img.classList.add('loaded');
}

/**
 * Preload critical images
 * @param {Array<string>} images - Array of image URLs
 */
export function preloadImages(images) {
  if (typeof window === 'undefined') return;

  images.forEach((src) => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'image';
    link.href = src;
    document.head.appendChild(link);
  });
}

/**
 * Convert image to WebP format (client-side)
 * Note: This requires a backend service or build-time conversion
 * This is a placeholder for the conversion logic
 * @param {string} src - Original image source
 * @returns {string} - WebP image source
 */
export function convertToWebP(src) {
  const lastDotIndex = src.lastIndexOf('.');
  const baseName = src.substring(0, lastDotIndex);
  return `${baseName}.webp`;
}

/**
 * Get responsive image sizes
 * @param {Object} breakpoints - Breakpoint configuration
 * @returns {string} - sizes attribute value
 */
export function getResponsiveSizes(breakpoints = {}) {
  const {
    mobile = '100vw',
    tablet = '50vw',
    desktop = '33vw',
  } = breakpoints;

  return `(max-width: 640px) ${mobile}, (max-width: 1024px) ${tablet}, ${desktop}`;
}
