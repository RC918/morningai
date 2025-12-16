import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Settings, Activity } from "lucide-react";

import { SectionCard } from "../section-card";

describe("SectionCard", () => {
  it("renders with title and children", () => {
    render(
      <SectionCard title="Section Title">
        <p>Section content</p>
      </SectionCard>
    );
    expect(screen.getByText("Section Title")).toBeInTheDocument();
    expect(screen.getByText("Section content")).toBeInTheDocument();
  });

  it("renders as a div element", () => {
    const { container } = render(
      <SectionCard title="Test">
        <p>Content</p>
      </SectionCard>
    );
    const card = container.firstChild as HTMLElement;
    expect(card.tagName).toBe("DIV");
  });

  describe("title", () => {
    it("renders title as h2 heading", () => {
      render(
        <SectionCard title="Heading Title">
          <p>Content</p>
        </SectionCard>
      );
      const heading = screen.getByRole("heading", { level: 2 });
      expect(heading).toHaveTextContent("Heading Title");
    });

    it("applies correct title styling", () => {
      render(
        <SectionCard title="Styled Title">
          <p>Content</p>
        </SectionCard>
      );
      const heading = screen.getByRole("heading", { level: 2 });
      expect(heading).toHaveClass("text-sm", "font-semibold");
    });
  });

  describe("subtitle", () => {
    it("renders subtitle when provided", () => {
      render(
        <SectionCard title="Title" subtitle="This is a subtitle">
          <p>Content</p>
        </SectionCard>
      );
      expect(screen.getByText("This is a subtitle")).toBeInTheDocument();
    });

    it("does not render subtitle when not provided", () => {
      render(
        <SectionCard title="Title">
          <p>Content</p>
        </SectionCard>
      );
      expect(screen.queryByText("This is a subtitle")).not.toBeInTheDocument();
    });

    it("applies correct subtitle styling", () => {
      render(
        <SectionCard title="Title" subtitle="Styled Subtitle">
          <p>Content</p>
        </SectionCard>
      );
      const subtitle = screen.getByText("Styled Subtitle");
      expect(subtitle).toHaveClass("mt-0.5", "text-xs");
    });
  });

  describe("icon", () => {
    it("renders icon when provided", () => {
      render(
        <SectionCard title="With Icon" icon={<Settings data-testid="icon" />}>
          <p>Content</p>
        </SectionCard>
      );
      expect(screen.getByTestId("icon")).toBeInTheDocument();
    });

    it("does not render icon container when icon is not provided", () => {
      const { container } = render(
        <SectionCard title="No Icon">
          <p>Content</p>
        </SectionCard>
      );
      const iconSpan = container.querySelector(
        ".text-\\[var\\(--text-secondary\\)\\]"
      );
      expect(iconSpan).not.toBeInTheDocument();
    });
  });

  describe("action", () => {
    it("renders action when provided", () => {
      render(
        <SectionCard
          title="With Action"
          action={<button data-testid="action-btn">Action</button>}
        >
          <p>Content</p>
        </SectionCard>
      );
      expect(screen.getByTestId("action-btn")).toBeInTheDocument();
    });

    it("does not render action container when action is not provided", () => {
      const { container } = render(
        <SectionCard title="No Action">
          <p>Content</p>
        </SectionCard>
      );
      // The action container has text-xs class
      const actionContainers = container.querySelectorAll(".text-xs");
      // Should only have subtitle text-xs, not action container
      actionContainers.forEach((el) => {
        expect(el.tagName).not.toBe("DIV");
      });
    });
  });

  describe("custom className", () => {
    it("applies custom className", () => {
      const { container } = render(
        <SectionCard title="Custom" className="custom-class">
          <p>Content</p>
        </SectionCard>
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass("custom-class");
    });

    it("preserves default classes when custom className is added", () => {
      const { container } = render(
        <SectionCard title="Custom" className="custom-class">
          <p>Content</p>
        </SectionCard>
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass("rounded-xl", "border", "shadow-card");
    });
  });

  describe("layout", () => {
    it("has correct base styling", () => {
      const { container } = render(
        <SectionCard title="Layout">
          <p>Content</p>
        </SectionCard>
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass("rounded-xl", "border", "shadow-card");
    });

    it("renders header with border-b", () => {
      const { container } = render(
        <SectionCard title="Header">
          <p>Content</p>
        </SectionCard>
      );
      const header = container.querySelector(".border-b");
      expect(header).toBeInTheDocument();
    });

    it("renders content area with correct padding", () => {
      const { container } = render(
        <SectionCard title="Content Area">
          <p>Content</p>
        </SectionCard>
      );
      const contentArea = container.querySelector(".px-5.py-4:not(.border-b)");
      expect(contentArea).toBeInTheDocument();
    });
  });

  describe("props forwarding", () => {
    it("forwards additional HTML attributes", () => {
      render(
        <SectionCard title="Props" data-testid="section-card" aria-label="Test">
          <p>Content</p>
        </SectionCard>
      );
      const card = screen.getByTestId("section-card");
      expect(card).toHaveAttribute("aria-label", "Test");
    });
  });

  describe("complete example", () => {
    it("renders with all props", () => {
      render(
        <SectionCard
          title="Complete Section"
          subtitle="With all features"
          icon={<Activity data-testid="complete-icon" />}
          action={<button data-testid="complete-action">Edit</button>}
          className="complete-class"
        >
          <div data-testid="complete-content">Full content here</div>
        </SectionCard>
      );

      expect(screen.getByText("Complete Section")).toBeInTheDocument();
      expect(screen.getByText("With all features")).toBeInTheDocument();
      expect(screen.getByTestId("complete-icon")).toBeInTheDocument();
      expect(screen.getByTestId("complete-action")).toBeInTheDocument();
      expect(screen.getByTestId("complete-content")).toBeInTheDocument();
    });
  });
});
