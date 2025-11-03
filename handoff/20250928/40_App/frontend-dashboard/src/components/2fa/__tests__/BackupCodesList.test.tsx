import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BackupCodesList } from '../BackupCodesList';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'settings.2fa.backupCodes.saveTitle': 'Save Your Backup Codes',
        'settings.2fa.backupCodes.saveDescription': 'Store these codes in a safe place. Each code can only be used once.',
        'settings.2fa.backupCodes.copied': 'Copied!',
        'settings.2fa.backupCodes.copyAll': 'Copy All',
        'settings.2fa.backupCodes.download': 'Download',
        'settings.2fa.backupCodes.important': 'Important:',
        'settings.2fa.backupCodes.warningMessage': 'These codes will not be shown again. Make sure to save them before continuing.',
        'settings.2fa.backupCodes.confirmSaved': "I've Saved My Backup Codes",
      };
      return translations[key] || key;
    },
  }),
}));

vi.mock('lucide-react', () => {
  const React = require('react');
  return {
    AlertCircle: ({ className }: any) => React.createElement('span', { className }, 'AlertCircle'),
    Copy: ({ className }: any) => React.createElement('span', { className }, 'Copy'),
    Download: ({ className }: any) => React.createElement('span', { className }, 'Download'),
    CheckCircle2: ({ className }: any) => React.createElement('span', { className }, 'CheckCircle2'),
  };
});

describe('BackupCodesList', () => {
  const mockBackupCodes = [
    'ABCD-EFGH-IJKL-MNOP',
    'QRST-UVWX-YZAB-CDEF',
    'GHIJ-KLMN-OPQR-STUV',
    'WXYZ-ABCD-EFGH-IJKL',
    'MNOP-QRST-UVWX-YZAB',
    'CDEF-GHIJ-KLMN-OPQR',
    'STUV-WXYZ-ABCD-EFGH',
    'IJKL-MNOP-QRST-UVWX',
  ];

  let mockOnContinue: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockOnContinue = vi.fn();
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.restoreAllMocks();
  });

  it('renders all backup codes', () => {
    render(<BackupCodesList backupCodes={mockBackupCodes} />);

    mockBackupCodes.forEach(code => {
      expect(screen.getByText(code)).toBeInTheDocument();
    });
  });

  it('displays title and description', () => {
    render(<BackupCodesList backupCodes={mockBackupCodes} />);

    expect(screen.getByText('Save Your Backup Codes')).toBeInTheDocument();
    expect(screen.getByText(/Store these codes in a safe place/)).toBeInTheDocument();
  });

  it('displays warning message', () => {
    render(<BackupCodesList backupCodes={mockBackupCodes} />);

    expect(screen.getByText('Important:')).toBeInTheDocument();
    expect(screen.getByText(/These codes will not be shown again/)).toBeInTheDocument();
  });

  it('copies all codes to clipboard when copy button is clicked', async () => {
    render(<BackupCodesList backupCodes={mockBackupCodes} />);

    const copyButton = screen.getByRole('button', { name: /Copy All/i });
    fireEvent.click(copyButton);

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        mockBackupCodes.join('\n')
      );
    });
  });

  it('shows "Copied!" message after successful copy', async () => {
    render(<BackupCodesList backupCodes={mockBackupCodes} />);

    const copyButton = screen.getByRole('button', { name: /Copy All/i });
    fireEvent.click(copyButton);

    await waitFor(() => {
      expect(screen.getByText('Copied!')).toBeInTheDocument();
    });
  });

  it('resets "Copied!" message after 2 seconds', async () => {
    vi.useFakeTimers();

    render(<BackupCodesList backupCodes={mockBackupCodes} />);

    const copyButton = screen.getByRole('button', { name: /Copy All/i });
    fireEvent.click(copyButton);

    await vi.runOnlyPendingTimersAsync();

    expect(screen.getByText('Copied!')).toBeInTheDocument();

    vi.advanceTimersByTime(2000);
    await vi.runOnlyPendingTimersAsync();

    expect(screen.queryByText('Copied!')).not.toBeInTheDocument();
    expect(screen.getByText('Copy All')).toBeInTheDocument();

    vi.useRealTimers();
  });

  it('handles copy error gracefully', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const writeTextMock = vi.fn().mockRejectedValue(new Error('Copy failed'));
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: writeTextMock,
      },
      writable: true,
      configurable: true,
    });

    render(<BackupCodesList backupCodes={mockBackupCodes} />);

    const copyButton = screen.getByRole('button', { name: /Copy All/i });
    fireEvent.click(copyButton);

    await waitFor(() => {
      expect(writeTextMock).toHaveBeenCalled();
    });

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'Failed to copy backup codes:',
      expect.any(Error)
    );

    consoleErrorSpy.mockRestore();
  });

  it('downloads backup codes as text file when download button is clicked', () => {
    render(<BackupCodesList backupCodes={mockBackupCodes} />);

    const createElementSpy = vi.spyOn(document, 'createElement');
    const appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation((node) => node);
    const removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation((node) => node);
    const createObjectURLSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock-url');
    const revokeObjectURLSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});

    const downloadButton = screen.getByRole('button', { name: /Download/i });
    fireEvent.click(downloadButton);

    expect(createElementSpy).toHaveBeenCalledWith('a');
    expect(createObjectURLSpy).toHaveBeenCalled();
    expect(appendChildSpy).toHaveBeenCalled();
    expect(removeChildSpy).toHaveBeenCalled();
    expect(revokeObjectURLSpy).toHaveBeenCalledWith('blob:mock-url');

    createElementSpy.mockRestore();
    appendChildSpy.mockRestore();
    removeChildSpy.mockRestore();
    createObjectURLSpy.mockRestore();
    revokeObjectURLSpy.mockRestore();
  });

  it('generates correct filename for download', () => {
    render(<BackupCodesList backupCodes={mockBackupCodes} />);

    const createElementSpy = vi.spyOn(document, 'createElement');
    const appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation((node) => node);
    const removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation((node) => node);
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock-url');
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});

    const downloadButton = screen.getByRole('button', { name: /Download/i });
    fireEvent.click(downloadButton);

    const anchorElement = createElementSpy.mock.results[0].value as HTMLAnchorElement;
    expect(anchorElement.download).toMatch(/^2fa-backup-codes-\d{4}-\d{2}-\d{2}\.txt$/);

    createElementSpy.mockRestore();
    appendChildSpy.mockRestore();
    removeChildSpy.mockRestore();
  });

  it('renders continue button when onContinue is provided', () => {
    render(<BackupCodesList backupCodes={mockBackupCodes} onContinue={mockOnContinue} />);

    const continueButton = screen.getByRole('button', { name: /I've Saved My Backup Codes/i });
    expect(continueButton).toBeInTheDocument();
  });

  it('does not render continue button when onContinue is not provided', () => {
    render(<BackupCodesList backupCodes={mockBackupCodes} />);

    const continueButton = screen.queryByRole('button', { name: /I've Saved My Backup Codes/i });
    expect(continueButton).not.toBeInTheDocument();
  });

  it('calls onContinue when continue button is clicked', () => {
    render(<BackupCodesList backupCodes={mockBackupCodes} onContinue={mockOnContinue} />);

    const continueButton = screen.getByRole('button', { name: /I've Saved My Backup Codes/i });
    fireEvent.click(continueButton);

    expect(mockOnContinue).toHaveBeenCalledTimes(1);
  });

  it('displays codes in a 2-column grid', () => {
    const { container } = render(<BackupCodesList backupCodes={mockBackupCodes} />);

    const grid = container.querySelector('.grid-cols-2');
    expect(grid).toBeInTheDocument();
  });

  it('renders correct number of code elements', () => {
    const { container } = render(<BackupCodesList backupCodes={mockBackupCodes} />);

    const codeElements = container.querySelectorAll('.font-mono .px-3');
    expect(codeElements).toHaveLength(8);
  });

  it('handles empty backup codes array', () => {
    render(<BackupCodesList backupCodes={[]} />);

    expect(screen.getByText('Save Your Backup Codes')).toBeInTheDocument();
  });

  it('handles single backup code', () => {
    const singleCode = ['ABCD-EFGH-IJKL-MNOP'];
    render(<BackupCodesList backupCodes={singleCode} />);

    expect(screen.getByText(singleCode[0])).toBeInTheDocument();
  });
});
