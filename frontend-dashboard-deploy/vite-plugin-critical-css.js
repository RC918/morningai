/**
 * Vite Plugin for Critical CSS Inlining
 * Extracts and inlines critical above-the-fold CSS
 */

import fs from 'fs';
import path from 'path';

export function criticalCSSPlugin(options = {}) {
  const {
    criticalCSS = '',
    inlineThreshold = 14 * 1024, // 14KB threshold
  } = options;

  return {
    name: 'vite-plugin-critical-css',
    
    transformIndexHtml: {
      order: 'post',
      handler(html, ctx) {
        if (!ctx.bundle) return html;

        let extractedCSS = criticalCSS;

        if (!extractedCSS) {
          const cssFiles = Object.keys(ctx.bundle).filter(
            (file) => file.endsWith('.css')
          );

          if (cssFiles.length > 0) {
            const mainCSSFile = cssFiles[0];
            const cssContent = ctx.bundle[mainCSSFile].source;

            extractedCSS = extractCriticalCSS(cssContent);
          }
        }

        if (extractedCSS) {
          const criticalStyleTag = `
    <style id="critical-css">
      ${extractedCSS}
    </style>`;

          html = html.replace('</head>', `${criticalStyleTag}\n  </head>`);
        }

        return html;
      },
    },
  };
}

/**
 * Extract critical CSS (simplified)
 * In production, use a proper critical CSS extraction tool
 */
function extractCriticalCSS(cssContent) {
  const criticalSelectors = [
    '*',
    '::before',
    '::after',
    'html',
    'body',
    '#root',
    '.container',
    'header',
    'nav',
    'main',
    'h1',
    'h2',
    'h3',
    'button',
    'a',
    'input',
  ];

  const criticalRules = [];
  const lines = cssContent.split('\n');
  let inCriticalRule = false;
  let currentRule = '';

  for (const line of lines) {
    const hasCriticalSelector = criticalSelectors.some((selector) =>
      line.includes(selector)
    );

    if (hasCriticalSelector && line.includes('{')) {
      inCriticalRule = true;
      currentRule = line;
    } else if (inCriticalRule) {
      currentRule += '\n' + line;
      if (line.includes('}')) {
        criticalRules.push(currentRule);
        inCriticalRule = false;
        currentRule = '';
      }
    }
  }

  return criticalRules.join('\n');
}

export default criticalCSSPlugin;
