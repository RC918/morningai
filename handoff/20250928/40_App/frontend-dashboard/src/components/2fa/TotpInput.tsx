import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { getSpringConfig, triggerHaptic } from '@/lib/spring-animation';

interface TotpInputProps {
  value: string;
  onChange: (value: string) => void;
  onComplete?: (value: string) => void;
  disabled?: boolean;
  error?: boolean;
  autoFocus?: boolean;
  className?: string;
}

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
}: TotpInputProps) {
  const { t } = useTranslation();
  const [focusedIndex, setFocusedIndex] = useState<number | null>(autoFocus ? 0 : null);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const springConfig = getSpringConfig('smooth');

  const digits = Array.from({ length: 6 }, (_, i) => value?.[i] ?? ' ');

  useEffect(() => {
    if (autoFocus && inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, [autoFocus]);

  useEffect(() => {
    if (value.length === 6 && onComplete) {
      onComplete(value);
    }
  }, [value, onComplete]);

  const handleChange = (index: number, digitValue: string) => {
    if (disabled) return;

    const sanitized = digitValue.replace(/\D/g, '');
    if (sanitized.length === 0) {
      if (digits[index].trim()) {
        const newDigits = [...digits];
        newDigits[index] = ' ';
        onChange(newDigits.join('').replace(/\s/g, ''));
        
        if (index > 0) {
          inputRefs.current[index - 1]?.focus();
        }
      }
      return;
    }

    if (sanitized.length === 1) {
      const newDigits = [...digits];
      newDigits[index] = sanitized;
      const newValue = newDigits.join('').replace(/\s/g, '');
      onChange(newValue);

      if (index < 5 && inputRefs.current[index + 1]) {
        inputRefs.current[index + 1]?.focus();
      }
    } else {
      const pastedDigits = sanitized.slice(0, 6 - index);
      const newDigits = [...digits];
      for (let i = 0; i < pastedDigits.length; i++) {
        if (index + i < 6) {
          newDigits[index + i] = pastedDigits[i];
        }
      }
      const newValue = newDigits.join('').replace(/\s/g, '');
      onChange(newValue);

      const nextEmptyIndex = newDigits.findIndex((d, i) => i > index && !d);
      const targetIndex = nextEmptyIndex !== -1 ? nextEmptyIndex : Math.min(index + pastedDigits.length, 5);
      inputRefs.current[targetIndex]?.focus();
    }

    if (inputRefs.current[index]) {
      triggerHaptic(inputRefs.current[index]!, 'light');
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (disabled) return;

    const currentInput = e.currentTarget as HTMLInputElement;
    if (e.key === 'Backspace' && !currentInput.value && index > 0) {
      inputRefs.current[index - 1]?.focus();
      e.preventDefault();
    } else if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1]?.focus();
      e.preventDefault();
    } else if (e.key === 'ArrowRight' && index < 5) {
      inputRefs.current[index + 1]?.focus();
      e.preventDefault();
    }
  };

  const handleFocus = (index: number) => {
    setFocusedIndex(index);
    inputRefs.current[index]?.select();
  };

  const handleBlur = () => {
    setFocusedIndex(null);
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '');
    if (pastedData) {
      const newDigits = [...digits];
      const target = e.currentTarget as HTMLInputElement;
      const startIndex = inputRefs.current.indexOf(target);
      
      for (let i = 0; i < pastedData.length && startIndex + i < 6; i++) {
        newDigits[startIndex + i] = pastedData[i];
      }
      
      const newValue = newDigits.join('').replace(/\s/g, '');
      onChange(newValue);
      
      const targetIndex = Math.min(startIndex + pastedData.length - 1, 5);
      inputRefs.current[targetIndex]?.focus();
    }
  };

  return (
    <div className={cn('flex flex-col gap-2', className)}>
      <label className="text-sm font-medium text-foreground">
        {t('auth.2fa.totpCodeLabel')}
      </label>
      <div className="flex gap-2 justify-center">
        {digits.map((digit, index) => (
          <motion.input
            key={index}
            data-testid={`totp-input-${index}`}
            ref={(el) => {
              inputRefs.current[index] = el;
            }}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit.trim()}
            onChange={(e) => handleChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            onFocus={() => handleFocus(index)}
            onBlur={handleBlur}
            onPaste={handlePaste}
            disabled={disabled}
            className={cn(
              'w-12 h-14 text-center text-2xl font-semibold rounded-xl border-2 transition-all outline-none',
              'bg-background/80 backdrop-blur-sm',
              'focus:ring-[3px] focus:ring-primary/20',
              error
                ? 'border-destructive focus:border-destructive focus:ring-destructive/20'
                : focusedIndex === index
                ? 'border-primary'
                : 'border-input',
              disabled && 'opacity-50 cursor-not-allowed',
              'selection:bg-primary selection:text-primary-foreground'
            )}
            aria-label={t('auth.2fa.totpDigitLabel', { index: index + 1 })}
            whileFocus={{ scale: 1.05 }}
            transition={springConfig}
          />
        ))}
      </div>
      <p className="text-xs text-muted-foreground text-center">
        {t('auth.2fa.totpCodeHelp')}
      </p>
    </div>
  );
}
