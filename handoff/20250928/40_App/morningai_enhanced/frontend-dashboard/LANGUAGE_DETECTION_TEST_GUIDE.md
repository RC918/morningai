# Language Detection Testing Guide

## Automated Tests
Run automated tests with:
```bash
pnpm test:run
```

All 17 automated tests cover:
- Browser language detection (zh-TW, zh-CN, zh-Hant, zh-Hans, zh, ja-JP, ko-KR, en-US)
- localStorage priority
- Edge cases (incognito mode, SSR, missing navigator.language)
- Language caching

## Manual Browser Testing

### Test 1: Browser Language Detection

#### Chrome
1. Open Chrome Settings → Languages
2. Set "Chinese (Traditional)" as the first language
3. Clear localStorage: Open DevTools → Application → Local Storage → Clear All
4. Reload the page
5. **Expected**: UI displays in Traditional Chinese (繁體中文)

#### Firefox
1. Open Firefox Settings → Language
2. Set "Chinese (Traditional) [zh-TW]" as the first language
3. Clear localStorage: Open DevTools → Storage → Local Storage → Clear All
4. Reload the page
5. **Expected**: UI displays in Traditional Chinese (繁體中文)

#### Safari
1. System Preferences → Language & Region
2. Add "繁體中文" as the first language
3. Restart Safari
4. Clear localStorage: Develop → Show Web Inspector → Storage → Local Storage → Clear
5. Reload the page
6. **Expected**: UI displays in Traditional Chinese (繁體中文)

### Test 2: English Fallback

1. Set browser language to Japanese (ja-JP) or Korean (ko-KR)
2. Clear localStorage
3. Reload the page
4. **Expected**: UI displays in English

### Test 3: Manual Language Switching

1. Click the language switcher (globe icon) in the sidebar
2. Select a different language
3. **Expected**: UI immediately switches to the selected language
4. Reload the page
5. **Expected**: UI remains in the selected language (persisted in localStorage)

### Test 4: localStorage Priority

1. Set browser language to Chinese
2. Use language switcher to select English
3. Reload the page
4. **Expected**: UI displays in English (localStorage takes priority)

### Test 5: Incognito Mode

1. Open the app in incognito/private browsing mode
2. Set browser language to Chinese
3. **Expected**: UI displays in Chinese (falls back to browser language detection)
4. Try to switch language using the language switcher
5. **Expected**: Language switches immediately, but may not persist after reload (localStorage unavailable)

### Test 6: localStorage Clearing

1. Set language to Chinese using the language switcher
2. Open DevTools → Application/Storage → Local Storage
3. Delete the `i18nextLng` key
4. Reload the page
5. **Expected**: UI falls back to browser language detection

## Edge Cases Covered

### SSR Compatibility
- ✅ Checks for `window` object before accessing browser APIs
- ✅ Returns default language (en-US) in SSR environment

### localStorage Unavailable
- ✅ Gracefully handles localStorage access errors
- ✅ Falls back to browser language detection
- ✅ Logs warnings to console (check DevTools Console)

### Missing navigator.language
- ✅ Handles browsers without `navigator.language` support
- ✅ Falls back to default language (en-US)

## Language Mapping

| Browser Language | Detected As | Notes |
|-----------------|-------------|-------|
| zh-TW | zh-TW | Traditional Chinese (Taiwan) |
| zh-Hant | zh-TW | Traditional Chinese (Script) |
| zh-CN | zh-TW | Simplified Chinese → Traditional |
| zh-Hans | zh-TW | Simplified Chinese (Script) → Traditional |
| zh | zh-TW | Generic Chinese → Traditional |
| zh-HK | zh-TW | Hong Kong Chinese → Traditional |
| zh-SG | zh-TW | Singapore Chinese → Traditional |
| en-US | en-US | English (US) |
| en-GB | en-US | English (UK) → US English |
| ja-JP | en-US | Japanese → English |
| ko-KR | en-US | Korean → English |
| * | en-US | All other languages → English |

## Known Limitations

1. **Dashboard Pages Not Migrated**: Only the LoginPage is fully migrated to i18n. Dashboard and other inner pages still display hardcoded Chinese text.

2. **No Simplified Chinese Support**: Currently, all Chinese variants map to Traditional Chinese (zh-TW). If you need Simplified Chinese support, add a `zh-CN` locale file.

3. **No Auto-Detection of Region Changes**: Language detection only runs on initial page load. If the user changes their browser language while the app is open, they need to reload the page.

## Troubleshooting

### Language not switching
1. Check DevTools Console for errors
2. Verify localStorage is available (not blocked by browser settings)
3. Clear browser cache and localStorage
4. Check that the language switcher is visible (sidebar not collapsed)

### Language not persisting
1. Check if localStorage is enabled in browser settings
2. Verify not in incognito/private browsing mode
3. Check DevTools → Application → Local Storage for `i18nextLng` key

### Wrong language detected
1. Check browser language settings
2. Clear localStorage and reload
3. Check DevTools Console for language detection warnings
