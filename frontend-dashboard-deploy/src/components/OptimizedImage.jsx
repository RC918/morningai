import { useEffect, useRef, useState } from 'react';
import { getOptimizedImageSrc, lazyLoadImage, supportsWebP } from '@/lib/image-optimization';

/**
 * OptimizedImage Component
 * Provides WebP support with fallbacks and lazy loading
 */
export function OptimizedImage({
  src,
  alt,
  className = '',
  loading = 'lazy',
  sizes,
  width,
  height,
  onLoad,
  onError,
  ...props
}) {
  const imgRef = useRef(null);
  const [webpSupported, setWebpSupported] = useState(null);

  useEffect(() => {
    supportsWebP().then(setWebpSupported);
  }, []);

  useEffect(() => {
    if (loading === 'lazy' && imgRef.current) {
      lazyLoadImage(imgRef.current);
    }
  }, [loading]);

  const { webpSrcSet, fallbackSrcSet, src: fallbackSrc } = getOptimizedImageSrc(src);

  if (webpSupported === null) {
    return (
      <div
        className={`bg-gray-200 animate-pulse ${className}`}
        style={{ width, height }}
        aria-label="Loading image"
      />
    );
  }

  if (loading === 'lazy') {
    return (
      <picture>
        {webpSupported && (
          <source
            type="image/webp"
            data-srcset={webpSrcSet}
            sizes={sizes}
          />
        )}
        <img
          ref={imgRef}
          data-src={fallbackSrc}
          data-srcset={fallbackSrcSet}
          alt={alt}
          className={`lazy ${className}`}
          width={width}
          height={height}
          onLoad={onLoad}
          onError={onError}
          {...props}
        />
      </picture>
    );
  }

  return (
    <picture>
      {webpSupported && (
        <source
          type="image/webp"
          srcSet={webpSrcSet}
          sizes={sizes}
        />
      )}
      <img
        ref={imgRef}
        src={fallbackSrc}
        srcSet={fallbackSrcSet}
        alt={alt}
        className={className}
        width={width}
        height={height}
        loading={loading}
        onLoad={onLoad}
        onError={onError}
        {...props}
      />
    </picture>
  );
}

/**
 * OptimizedBackgroundImage Component
 * Provides optimized background images with lazy loading
 */
export function OptimizedBackgroundImage({
  src,
  className = '',
  children,
  loading = 'lazy',
  ...props
}) {
  const divRef = useRef(null);
  const [loaded, setLoaded] = useState(loading === 'eager');
  const [webpSupported, setWebpSupported] = useState(null);

  useEffect(() => {
    supportsWebP().then(setWebpSupported);
  }, []);

  useEffect(() => {
    if (loading === 'lazy' && divRef.current && !loaded) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              setLoaded(true);
              observer.unobserve(entry.target);
            }
          });
        },
        { rootMargin: '50px' }
      );

      observer.observe(divRef.current);

      return () => observer.disconnect();
    }
  }, [loading, loaded]);

  const { src: fallbackSrc } = getOptimizedImageSrc(src);
  const webpSrc = webpSupported ? fallbackSrc.replace(/\.(jpg|jpeg|png)$/, '.webp') : fallbackSrc;
  const backgroundImage = loaded ? `url(${webpSrc})` : 'none';

  return (
    <div
      ref={divRef}
      className={`${className} ${!loaded ? 'bg-gray-200' : ''}`}
      style={{ backgroundImage }}
      {...props}
    >
      {children}
    </div>
  );
}
