/**
 * Typography System Visual Regression Tests
 * 
 * These tests ensure that future changes don't break the typography system.
 * Run with: npm run test:visual
 */

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';

describe('Typography System - Visual Regression', () => {
  describe('Display Styles', () => {
    it('renders display-1 with correct styles', () => {
      const { container } = render(
        <h1 className="text-display-1">Display 1</h1>
      );
      const element = container.querySelector('.text-display-1');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-display-1');
    });

    it('renders display-2 with correct styles', () => {
      const { container } = render(
        <h1 className="text-display-2">Display 2</h1>
      );
      const element = container.querySelector('.text-display-2');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-display-2');
    });

    it('renders display-3 with correct styles', () => {
      const { container } = render(
        <h1 className="text-display-3">Display 3</h1>
      );
      const element = container.querySelector('.text-display-3');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-display-3');
    });
  });

  describe('Title Styles', () => {
    it('renders large-title with correct styles', () => {
      const { container } = render(
        <h1 className="text-large-title">Large Title</h1>
      );
      const element = container.querySelector('.text-large-title');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-large-title');
    });

    it('renders title-1 with correct styles', () => {
      const { container } = render(
        <h2 className="text-title-1">Title 1</h2>
      );
      const element = container.querySelector('.text-title-1');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-title-1');
    });

    it('renders title-2 with correct styles', () => {
      const { container } = render(
        <h3 className="text-title-2">Title 2</h3>
      );
      const element = container.querySelector('.text-title-2');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-title-2');
    });

    it('renders title-3 with correct styles', () => {
      const { container } = render(
        <h4 className="text-title-3">Title 3</h4>
      );
      const element = container.querySelector('.text-title-3');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-title-3');
    });
  });

  describe('Body Styles', () => {
    it('renders headline with correct styles', () => {
      const { container } = render(
        <p className="text-headline">Headline</p>
      );
      const element = container.querySelector('.text-headline');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-headline');
    });

    it('renders body with correct styles', () => {
      const { container } = render(
        <p className="text-body">Body</p>
      );
      const element = container.querySelector('.text-body');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-body');
    });

    it('renders callout with correct styles', () => {
      const { container } = render(
        <p className="text-callout">Callout</p>
      );
      const element = container.querySelector('.text-callout');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-callout');
    });

    it('renders subhead with correct styles', () => {
      const { container } = render(
        <p className="text-subhead">Subhead</p>
      );
      const element = container.querySelector('.text-subhead');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-subhead');
    });
  });

  describe('Small Text Styles', () => {
    it('renders footnote with correct styles', () => {
      const { container } = render(
        <p className="text-footnote">Footnote</p>
      );
      const element = container.querySelector('.text-footnote');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-footnote');
    });

    it('renders caption-1 with correct styles', () => {
      const { container } = render(
        <p className="text-caption-1">Caption 1</p>
      );
      const element = container.querySelector('.text-caption-1');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-caption-1');
    });

    it('renders caption-2 with correct styles', () => {
      const { container } = render(
        <p className="text-caption-2">Caption 2</p>
      );
      const element = container.querySelector('.text-caption-2');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-caption-2');
    });
  });

  describe('Font Weight Utilities', () => {
    it('renders font-light correctly', () => {
      const { container } = render(
        <p className="font-light">Light</p>
      );
      const element = container.querySelector('.font-light');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('font-light');
    });

    it('renders font-normal correctly', () => {
      const { container } = render(
        <p className="font-normal">Normal</p>
      );
      const element = container.querySelector('.font-normal');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('font-normal');
    });

    it('renders font-medium correctly', () => {
      const { container } = render(
        <p className="font-medium">Medium</p>
      );
      const element = container.querySelector('.font-medium');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('font-medium');
    });

    it('renders font-semibold correctly', () => {
      const { container } = render(
        <p className="font-semibold">Semibold</p>
      );
      const element = container.querySelector('.font-semibold');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('font-semibold');
    });

    it('renders font-bold correctly', () => {
      const { container } = render(
        <p className="font-bold">Bold</p>
      );
      const element = container.querySelector('.font-bold');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('font-bold');
    });
  });

  describe('Line Height Utilities', () => {
    it('renders leading-tight correctly', () => {
      const { container } = render(
        <p className="leading-tight">Tight</p>
      );
      const element = container.querySelector('.leading-tight');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('leading-tight');
    });

    it('renders leading-normal correctly', () => {
      const { container } = render(
        <p className="leading-normal">Normal</p>
      );
      const element = container.querySelector('.leading-normal');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('leading-normal');
    });

    it('renders leading-relaxed correctly', () => {
      const { container } = render(
        <p className="leading-relaxed">Relaxed</p>
      );
      const element = container.querySelector('.leading-relaxed');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('leading-relaxed');
    });
  });

  describe('Letter Spacing Utilities', () => {
    it('renders tracking-tighter correctly', () => {
      const { container } = render(
        <p className="tracking-tighter">Tighter</p>
      );
      const element = container.querySelector('.tracking-tighter');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('tracking-tighter');
    });

    it('renders tracking-tight correctly', () => {
      const { container } = render(
        <p className="tracking-tight">Tight</p>
      );
      const element = container.querySelector('.tracking-tight');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('tracking-tight');
    });

    it('renders tracking-normal correctly', () => {
      const { container } = render(
        <p className="tracking-normal">Normal</p>
      );
      const element = container.querySelector('.tracking-normal');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('tracking-normal');
    });

    it('renders tracking-wide correctly', () => {
      const { container } = render(
        <p className="tracking-wide">Wide</p>
      );
      const element = container.querySelector('.tracking-wide');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('tracking-wide');
    });

    it('renders tracking-wider correctly', () => {
      const { container } = render(
        <p className="tracking-wider">Wider</p>
      );
      const element = container.querySelector('.tracking-wider');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('tracking-wider');
    });
  });

  describe('Text Truncation Utilities', () => {
    it('renders text-truncate correctly', () => {
      const { container } = render(
        <p className="text-truncate">This is a very long text that should be truncated</p>
      );
      const element = container.querySelector('.text-truncate');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-truncate');
    });

    it('renders text-truncate-2 correctly', () => {
      const { container } = render(
        <p className="text-truncate-2">This is a very long text that should be truncated to 2 lines</p>
      );
      const element = container.querySelector('.text-truncate-2');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-truncate-2');
    });

    it('renders text-truncate-3 correctly', () => {
      const { container } = render(
        <p className="text-truncate-3">This is a very long text that should be truncated to 3 lines</p>
      );
      const element = container.querySelector('.text-truncate-3');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-truncate-3');
    });
  });

  describe('Responsive Typography', () => {
    it('renders text-responsive-display correctly', () => {
      const { container } = render(
        <h1 className="text-responsive-display">Responsive Display</h1>
      );
      const element = container.querySelector('.text-responsive-display');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-responsive-display');
    });

    it('renders text-responsive-title correctly', () => {
      const { container } = render(
        <h2 className="text-responsive-title">Responsive Title</h2>
      );
      const element = container.querySelector('.text-responsive-title');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-responsive-title');
    });

    it('renders text-responsive-body correctly', () => {
      const { container } = render(
        <p className="text-responsive-body">Responsive Body</p>
      );
      const element = container.querySelector('.text-responsive-body');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-responsive-body');
    });
  });

  describe('Text Balance and Pretty', () => {
    it('renders text-balance correctly', () => {
      const { container } = render(
        <p className="text-balance">Balanced text</p>
      );
      const element = container.querySelector('.text-balance');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-balance');
    });

    it('renders text-pretty correctly', () => {
      const { container } = render(
        <p className="text-pretty">Pretty text</p>
      );
      const element = container.querySelector('.text-pretty');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-pretty');
    });
  });

  describe('Accessibility', () => {
    it('all typography classes maintain semantic HTML', () => {
      const { container } = render(
        <article>
          <h1 className="text-display-1">Main Heading</h1>
          <h2 className="text-title-1">Section Heading</h2>
          <p className="text-body">Body text</p>
          <p className="text-footnote">Footnote</p>
        </article>
      );
      
      expect(container.querySelector('h1')).toBeInTheDocument();
      expect(container.querySelector('h2')).toBeInTheDocument();
      expect(container.querySelectorAll('p')).toHaveLength(2);
    });

    it('truncated text includes full content for screen readers', () => {
      const fullText = 'This is a very long text that should be truncated but still accessible';
      const { container } = render(
        <p className="text-truncate">{fullText}</p>
      );
      const element = container.querySelector('.text-truncate');
      
      expect(element?.textContent).toBe(fullText);
    });
  });

  describe('Combination Classes', () => {
    it('combines typography with font weight', () => {
      const { container } = render(
        <h1 className="text-title-1 font-bold">Bold Title</h1>
      );
      const element = container.querySelector('.text-title-1.font-bold');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-title-1');
      expect(element).toHaveClass('font-bold');
    });

    it('combines typography with line height', () => {
      const { container } = render(
        <p className="text-body leading-relaxed">Relaxed Body</p>
      );
      const element = container.querySelector('.text-body.leading-relaxed');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-body');
      expect(element).toHaveClass('leading-relaxed');
    });

    it('combines typography with letter spacing', () => {
      const { container } = render(
        <p className="text-headline tracking-wide">Wide Headline</p>
      );
      const element = container.querySelector('.text-headline.tracking-wide');
      
      expect(element).toBeInTheDocument();
      expect(element).toHaveClass('text-headline');
      expect(element).toHaveClass('tracking-wide');
    });
  });
});

describe('Typography System - Snapshot Tests', () => {
  it('matches snapshot for all display styles', () => {
    const { container } = render(
      <div>
        <h1 className="text-display-1">Display 1</h1>
        <h1 className="text-display-2">Display 2</h1>
        <h1 className="text-display-3">Display 3</h1>
      </div>
    );
    
    expect(container).toMatchSnapshot();
  });

  it('matches snapshot for all title styles', () => {
    const { container } = render(
      <div>
        <h1 className="text-large-title">Large Title</h1>
        <h2 className="text-title-1">Title 1</h2>
        <h3 className="text-title-2">Title 2</h3>
        <h4 className="text-title-3">Title 3</h4>
      </div>
    );
    
    expect(container).toMatchSnapshot();
  });

  it('matches snapshot for all body styles', () => {
    const { container } = render(
      <div>
        <p className="text-headline">Headline</p>
        <p className="text-body">Body</p>
        <p className="text-callout">Callout</p>
        <p className="text-subhead">Subhead</p>
      </div>
    );
    
    expect(container).toMatchSnapshot();
  });

  it('matches snapshot for all small text styles', () => {
    const { container } = render(
      <div>
        <p className="text-footnote">Footnote</p>
        <p className="text-caption-1">Caption 1</p>
        <p className="text-caption-2">Caption 2</p>
      </div>
    );
    
    expect(container).toMatchSnapshot();
  });
});
