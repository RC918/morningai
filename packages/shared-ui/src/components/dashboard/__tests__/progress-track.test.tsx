import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { ProgressTrack } from "../progress-track";

describe("ProgressTrack", () => {
  const sampleItems = [
    { label: "Task A", value: 75 },
    { label: "Task B", value: 50 },
    { label: "Task C", value: 100 },
  ];

  it("renders all items", () => {
    render(<ProgressTrack items={sampleItems} />);
    expect(screen.getByText("Task A")).toBeInTheDocument();
    expect(screen.getByText("Task B")).toBeInTheDocument();
    expect(screen.getByText("Task C")).toBeInTheDocument();
  });

  it("renders percentage values", () => {
    render(<ProgressTrack items={sampleItems} />);
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("50%")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("renders empty list without errors", () => {
    const { container } = render(<ProgressTrack items={[]} />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toBeInTheDocument();
    expect(wrapper.children.length).toBe(0);
  });

  it("renders single item", () => {
    render(<ProgressTrack items={[{ label: "Single", value: 42 }]} />);
    expect(screen.getByText("Single")).toBeInTheDocument();
    expect(screen.getByText("42%")).toBeInTheDocument();
  });

  describe("progress bar", () => {
    it("renders progress bar with correct width", () => {
      const { container } = render(
        <ProgressTrack items={[{ label: "Test", value: 75 }]} />
      );
      const progressBar = container.querySelector(
        ".bg-\\[var\\(--brand-500\\)\\]"
      );
      expect(progressBar).toHaveStyle({ width: "75%" });
    });

    it("renders 0% progress correctly", () => {
      const { container } = render(
        <ProgressTrack items={[{ label: "Zero", value: 0 }]} />
      );
      const progressBar = container.querySelector(
        ".bg-\\[var\\(--brand-500\\)\\]"
      );
      expect(progressBar).toHaveStyle({ width: "0%" });
    });

    it("renders 100% progress correctly", () => {
      const { container } = render(
        <ProgressTrack items={[{ label: "Full", value: 100 }]} />
      );
      const progressBar = container.querySelector(
        ".bg-\\[var\\(--brand-500\\)\\]"
      );
      expect(progressBar).toHaveStyle({ width: "100%" });
    });

    it("has correct progress bar container styling", () => {
      const { container } = render(
        <ProgressTrack items={[{ label: "Test", value: 50 }]} />
      );
      const progressContainer = container.querySelector(
        ".h-1\\.5.w-full.overflow-hidden.rounded-full"
      );
      expect(progressContainer).toBeInTheDocument();
    });
  });

  describe("layout", () => {
    it("has correct wrapper styling", () => {
      const { container } = render(<ProgressTrack items={sampleItems} />);
      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper).toHaveClass("space-y-5");
    });

    it("renders label with correct styling", () => {
      render(<ProgressTrack items={[{ label: "Styled Label", value: 50 }]} />);
      const label = screen.getByText("Styled Label");
      expect(label).toHaveClass("text-xs", "font-medium");
    });

    it("renders percentage with correct styling", () => {
      render(<ProgressTrack items={[{ label: "Test", value: 50 }]} />);
      const percentage = screen.getByText("50%");
      expect(percentage).toHaveClass("text-xs");
    });
  });

  describe("custom className", () => {
    it("applies custom className", () => {
      const { container } = render(
        <ProgressTrack items={sampleItems} className="custom-class" />
      );
      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper).toHaveClass("custom-class");
    });

    it("preserves default classes when custom className is added", () => {
      const { container } = render(
        <ProgressTrack items={sampleItems} className="custom-class" />
      );
      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper).toHaveClass("space-y-5", "custom-class");
    });
  });

  describe("item keys", () => {
    it("uses label as key for items", () => {
      const { container } = render(<ProgressTrack items={sampleItems} />);
      const items = container.querySelectorAll(".space-y-1");
      expect(items.length).toBe(3);
    });
  });

  describe("edge cases", () => {
    it("handles decimal values", () => {
      render(<ProgressTrack items={[{ label: "Decimal", value: 33.33 }]} />);
      expect(screen.getByText("33.33%")).toBeInTheDocument();
    });

    it("clamps values greater than 100 to 100%", () => {
      const { container } = render(
        <ProgressTrack items={[{ label: "Over", value: 150 }]} />
      );
      const progressBar = container.querySelector(
        ".bg-\\[var\\(--brand-500\\)\\]"
      );
      expect(progressBar).toHaveStyle({ width: "100%" });
      expect(screen.getByText("100%")).toBeInTheDocument();
    });

    it("clamps negative values to 0%", () => {
      const { container } = render(
        <ProgressTrack items={[{ label: "Negative", value: -10 }]} />
      );
      const progressBar = container.querySelector(
        ".bg-\\[var\\(--brand-500\\)\\]"
      );
      expect(progressBar).toHaveStyle({ width: "0%" });
      expect(screen.getByText("0%")).toBeInTheDocument();
    });

    it("handles long labels", () => {
      const longLabel = "This is a very long label that might overflow";
      render(<ProgressTrack items={[{ label: longLabel, value: 50 }]} />);
      expect(screen.getByText(longLabel)).toBeInTheDocument();
    });
  });
});
