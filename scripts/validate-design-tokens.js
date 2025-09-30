#!/usr/bin/env node

const fs = require('fs')
const path = require('path')

const tokensPath = path.join(__dirname, '../docs/UX/tokens.json')

console.log('🔍 Validating design tokens...')

try {
  if (!fs.existsSync(tokensPath)) {
    console.error('❌ Design tokens file not found:', tokensPath)
    process.exit(1)
  }

  const tokens = JSON.parse(fs.readFileSync(tokensPath, 'utf8'))

  const requiredSections = ['color', 'font', 'space', 'radius', 'shadow']
  const missing = requiredSections.filter(section => !tokens[section])

  if (missing.length > 0) {
    console.error('❌ Missing required token sections:', missing)
    process.exit(1)
  }

  const requiredColorSections = ['primary', 'semantic', 'neutral', 'background']
  const missingColors = requiredColorSections.filter(section => !tokens.color[section])

  if (missingColors.length > 0) {
    console.error('❌ Missing required color sections:', missingColors)
    process.exit(1)
  }

  const requiredFontSections = ['family', 'size', 'weight', 'lineHeight']
  const missingFonts = requiredFontSections.filter(section => !tokens.font[section])

  if (missingFonts.length > 0) {
    console.error('❌ Missing required font sections:', missingFonts)
    process.exit(1)
  }

  console.log('✅ Design tokens validation passed')
  console.log(`📊 Token sections found: ${Object.keys(tokens).length}`)
  console.log(`🎨 Color variants: ${Object.keys(tokens.color).length}`)
  console.log(`📝 Font properties: ${Object.keys(tokens.font).length}`)
  console.log(`📏 Spacing values: ${Object.keys(tokens.space).length}`)

} catch (error) {
  console.error('❌ Error validating design tokens:', error.message)
  process.exit(1)
}
