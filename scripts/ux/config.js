/**
 * UX AI Perceptual QA Configuration
 * Defines routes, tokens, and thresholds for AI-powered visual harmony scoring
 */

const fs = require('fs');
const path = require('path');

const tokensPath = path.join(__dirname, '../../packages/shared-ui/src/tokens.json');
const allTokens = JSON.parse(fs.readFileSync(tokensPath, 'utf-8'));

const relevantTokens = {
  colors: allTokens.colors,
  spacing: allTokens.spacing,
  typography: allTokens.typography,
  borderRadius: allTokens.borderRadius,
};

const PAGES = {
  'frontend-dashboard': [
    {
      name: 'Landing Page',
      path: '/',
      description: 'Public landing page',
      requiresAuth: false,
      viewport: { width: 1366, height: 900 },
    },
    {
      name: 'Login Page',
      path: '/login',
      description: 'User authentication page',
      requiresAuth: false,
      viewport: { width: 1366, height: 900 },
    },
    {
      name: 'Dashboard',
      path: '/dashboard',
      description: 'Main dashboard view',
      requiresAuth: true,
      viewport: { width: 1366, height: 900 },
    },
  ],
  'owner-console': [
    {
      name: 'Login Page',
      path: '/login',
      description: 'Owner console login',
      requiresAuth: false,
      viewport: { width: 1366, height: 900 },
    },
    {
      name: 'Dashboard',
      path: '/dashboard',
      description: 'Owner console dashboard',
      requiresAuth: true,
      viewport: { width: 1366, height: 900 },
    },
  ],
};

const AI_CONFIG = {
  model: process.env.UX_AI_MODEL || 'gpt-4o-mini',
  temperature: 0,
  maxTokens: 1500,
  imageQuality: 'auto', // auto, low, high
  imageDetail: 'auto', // auto, low, high
};

const THRESHOLDS = {
  harmony: {
    min: parseFloat(process.env.UX_HARMONY_MIN || '70'),
    target: 85,
  },
  delight: {
    min: parseFloat(process.env.UX_DELIGHT_MIN || '75'),
    target: 90,
  },
};

const DELIGHT_WEIGHTS = {
  harmony: parseFloat(process.env.UX_DELIGHT_W_HARMONY || '0.5'),
  motion: parseFloat(process.env.UX_DELIGHT_W_MOTION || '0.5'),
};

const BUDGET = {
  maxPagesPerApp: parseInt(process.env.UX_AI_MAX_PAGES || '3'),
  maxImageWidth: 1366,
  imageFormat: 'jpeg',
  imageQuality: 0.85,
};

module.exports = {
  PAGES,
  relevantTokens,
  AI_CONFIG,
  THRESHOLDS,
  DELIGHT_WEIGHTS,
  BUDGET,
};
