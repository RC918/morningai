import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { getSpringConfig, triggerHaptic } from '@/lib/spring-animation';

/**
 * TotpInput Component
 * 
 * A specialized 6-digit input component for TOTP codes with auto-submit functionality.
 * Features:
 * - 6 individual digit boxes with auto-focus progression
 * - Auto-submit when all 6 digits are entered
 * - Backspace support to move to previous box
 * - Paste support for full 6-digit codes
 * - Haptic feedback on interaction
 * - Error state styling
 */
export function TotpInput({
  value,
  onChange,
  onComplete,
  disabled = false,
  error = false,
  autoFocus = true,
  className,
}) {
  const { t } = useTranslation();
  const inputRefs = useRef([]);
  const [digits, setDigits] = useState(Array(6).fill(''));

  useEffect(() => {
    const newDigits = value.padEnd(6, '').split('').slice(0, 6);
    setDigits(newDigits);
  }, [value]);

  useEffect(() => {
    if (autoFocus && inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, [autoFocus]);

  const handleChange = (index, newValue) => {
    if (disabled) return;

    const sanitized = newValue.replace(/[^0-9]/g, '');
    
    if (sanitized.length === 0) {
      const newDigits = [...digits];
      newDigits[index] = '';
      setDigits(newDigits);
      onChange(newDigits.join(''));
      return;
    }

    if (sanitized.length === 1) {
      const newDigits = [...digits];
      newDigits[index] = sanitized;
      setDigits(newDigits);
      onChange(newDigits.join(''));

      triggerHaptic('light');

      if (index < 5) {
        inputRefs.current[index + 1]?.focus();
      }

      const code = newDigits.join('');
      if (code.length === 6 && onComplete) {
        onComplete(code);
      }
    } else if (sanitized.length > 1) {
      handlePaste(sanitized, index);
    }
  };

  const handleKeyDown = (index, e) => {
    if (disabled) return;

    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
      triggerHaptic('light');
    } else if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1]?.focus();
    } else if (e.key === 'ArrowRight' && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (pastedText, startIndex = 0) => {
    const sanitized = pastedText.replace(/[^0-9]/g, '').slice(0, 6);
    const newDigits = [...digits];
    
    for (let i = 0; i < sanitized.length && startIndex + i < 6; i++) {
      newDigits[startIndex + i] = sanitized[i];
    }
    
    setDigits(newDigits);
    onChange(newDigits.join(''));

    triggerHaptic('medium');

    const nextEmptyIndex = newDigits.findIndex(d => !d);
    if (nextEmptyIndex !== -1) {
      inputRefs.current[nextEmptyIndex]?.focus();
    } else {
      inputRefs.current[5]?.focus();
      
      const code = newDigits.join('');
      if (code.length === 6 && onComplete) {
        onComplete(code);
      }
    }
  };

  const handleFocus = (index) => {
    inputRefs.current[index]?.select();
  };

  return (
    <div className={cn('flex gap-2 justify-center', className)}>
      {digits.map((digit, index) => (
        <motion.div
          key={index}
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={getSpringConfig('gentle', index * 0.05)}
        >
          <input
            ref={(el) => (inputRefs.current[index] = el)}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={(e) => handleChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            onFocus={() => handleFocus(index)}
            onPaste={(e) => {
              e.preventDefault();
              const pastedText = e.clipboardData.getData('text');
              handlePaste(pastedText, index);
            }}
            disabled={disabled}
            aria-label={t('auth.2fa.totpDigitLabel', { index: index + 1 })}
            className={cn(
              'w-12 h-14 text-center text-2xl font-semibold',
              'rounded-lg border-2 transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-offset-2',
              error
                ? 'border-destructive focus:border-destructive focus:ring-destructive'
                : 'border-input focus:border-primary focus:ring-primary',
              disabled && 'opacity-50 cursor-not-allowed bg-muted',
              !disabled && 'hover:border-primary/50'
            )}
          />
        </motion.div>
      ))}
    </div>
  );
}
