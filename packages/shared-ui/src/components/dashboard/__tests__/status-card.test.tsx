import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Activity, CheckCircle, Clock } from "lucide-react";

import { StatusCard } from "../status-card";

describe("StatusCard", () => {
  it("renders with label and value", () => {
    render(
      <StatusCard
        label="Total Sessions"
        value="128"
        icon={<Activity data-testid="icon" />}
      />
    );
    expect(screen.getByText("Total Sessions")).toBeInTheDocument();
    expect(screen.getByText("128")).toBeInTheDocument();
  });

  it("renders as a button element", () => {
    render(
      <StatusCard label="Test" value="42" icon={<Activity />} />
    );
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("has type='button' to prevent form submission", () => {
    render(
      <StatusCard label="Test" value="42" icon={<Activity />} />
    );
    expect(screen.getByRole("button")).toHaveAttribute("type", "button");
  });

  describe("variants", () => {
    it("renders default variant", () => {
      const { container } = render(
        <StatusCard
          label="Default"
          value="100"
          icon={<Activity />}
          variant="default"
        />
      );
      const button = container.firstChild as HTMLElement;
      expect(button).toHaveClass("rounded-xl", "border");
    });

    it("renders blue variant with active state", () => {
      const { container } = render(
        <StatusCard
          label="Active"
          value="42"
          icon={<Clock />}
          variant="blue"
          isActive
        />
      );
      const button = container.firstChild as HTMLElement;
      expect(button).toHaveClass("bg-primary-50", "border-primary-500");
    });

    it("renders green variant with active state", () => {
      const { container } = render(
        <StatusCard
          label="Completed"
          value="86"
          icon={<CheckCircle />}
          variant="green"
          isActive
        />
      );
      const button = container.firstChild as HTMLElement;
      expect(button).toHaveClass("bg-success-50", "border-success-500");
    });

    it("renders yellow variant with active state", () => {
      const { container } = render(
        <StatusCard
          label="Pending"
          value="15"
          icon={<Activity />}
          variant="yellow"
          isActive
        />
      );
      const button = container.firstChild as HTMLElement;
      expect(button).toHaveClass("bg-warning-50", "border-warning-500");
    });

    it("renders red variant with active state", () => {
      const { container } = render(
        <StatusCard
          label="Failed"
          value="3"
          icon={<Activity />}
          variant="red"
          isActive
        />
      );
      const button = container.firstChild as HTMLElement;
      expect(button).toHaveClass("bg-error-50", "border-error-500");
    });
  });

  describe("active state", () => {
    it("sets aria-pressed to true when active", () => {
      render(
        <StatusCard
          label="Active Card"
          value="42"
          icon={<Activity />}
          isActive
        />
      );
      expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "true");
    });

    it("sets aria-pressed to false when not active", () => {
      render(
        <StatusCard
          label="Inactive Card"
          value="42"
          icon={<Activity />}
          isActive={false}
        />
      );
      expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "false");
    });

    it("renders highlight bar when active", () => {
      const { container } = render(
        <StatusCard
          label="Active Card"
          value="42"
          icon={<Activity />}
          isActive
        />
      );
      const highlightBar = container.querySelector('[aria-hidden="true"]');
      expect(highlightBar).toBeInTheDocument();
      expect(highlightBar).toHaveClass("w-0.5", "rounded-full");
    });

    it("does not render highlight bar when not active", () => {
      const { container } = render(
        <StatusCard
          label="Inactive Card"
          value="42"
          icon={<Activity />}
          isActive={false}
        />
      );
      // The only aria-hidden element should be the icon, not the highlight bar
      const ariaHiddenElements = container.querySelectorAll('[aria-hidden="true"]');
      // Check that none of them have the highlight bar classes
      ariaHiddenElements.forEach((el) => {
        expect(el).not.toHaveClass("w-0.5");
      });
    });

    it("applies shadow-md when active", () => {
      const { container } = render(
        <StatusCard
          label="Active Card"
          value="42"
          icon={<Activity />}
          isActive
        />
      );
      const button = container.firstChild as HTMLElement;
      expect(button).toHaveClass("shadow-md");
    });
  });

  describe("disabled state", () => {
    it("sets aria-disabled when disabled", () => {
      render(
        <StatusCard
          label="Disabled Card"
          value="0"
          icon={<Activity />}
          disabled
        />
      );
      expect(screen.getByRole("button")).toHaveAttribute("aria-disabled", "true");
    });

    it("applies disabled styling", () => {
      const { container } = render(
        <StatusCard
          label="Disabled Card"
          value="0"
          icon={<Activity />}
          disabled
        />
      );
      const button = container.firstChild as HTMLElement;
      expect(button).toHaveClass("opacity-50", "cursor-not-allowed");
    });

    it("does not trigger onClick when disabled", async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();

      render(
        <StatusCard
          label="Disabled Card"
          value="0"
          icon={<Activity />}
          disabled
          onClick={handleClick}
        />
      );

      await user.click(screen.getByRole("button"));
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe("click handling", () => {
    it("triggers onClick when clicked", async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();

      render(
        <StatusCard
          label="Clickable Card"
          value="42"
          icon={<Activity />}
          onClick={handleClick}
        />
      );

      await user.click(screen.getByRole("button"));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe("tooltip", () => {
    it("renders title attribute when tooltip is provided", () => {
      render(
        <StatusCard
          label="Card with Tooltip"
          value="42"
          icon={<Activity />}
          tooltip="This is a tooltip"
        />
      );
      expect(screen.getByRole("button")).toHaveAttribute(
        "title",
        "This is a tooltip"
      );
    });
  });

  describe("icon rendering", () => {
    it("renders icon with correct size classes using design tokens", () => {
      const { container } = render(
        <StatusCard
          label="Card with Icon"
          value="42"
          icon={<Activity data-testid="test-icon" />}
        />
      );
      // Icon container uses CSS variable tokens: --card-icon-status-containerSize
      const iconContainer = container.querySelector('[class*="h-[var(--card-icon-status-containerSize"]');
      expect(iconContainer).toBeInTheDocument();
    });
  });

  describe("custom className", () => {
    it("applies custom className", () => {
      const { container } = render(
        <StatusCard
          label="Custom Card"
          value="42"
          icon={<Activity />}
          className="custom-class"
        />
      );
      const button = container.firstChild as HTMLElement;
      expect(button).toHaveClass("custom-class");
    });
  });

  describe("accessibility", () => {
    it("has focus-visible styles for keyboard navigation", () => {
      const { container } = render(
        <StatusCard label="Focusable Card" value="42" icon={<Activity />} />
      );
      const button = container.firstChild as HTMLElement;
      expect(button).toHaveClass("focus-visible:outline-none", "focus-visible:ring-2");
    });

    it("renders numeric value correctly", () => {
      render(
        <StatusCard label="Numeric Value" value={1234} icon={<Activity />} />
      );
      expect(screen.getByText("1234")).toBeInTheDocument();
    });

    it("renders string value correctly", () => {
      render(
        <StatusCard label="String Value" value="1,234" icon={<Activity />} />
      );
      expect(screen.getByText("1,234")).toBeInTheDocument();
    });
  });

  describe("layout", () => {
    it("has fixed height of h-24", () => {
      const { container } = render(
        <StatusCard label="Fixed Height" value="42" icon={<Activity />} />
      );
      const button = container.firstChild as HTMLElement;
      expect(button).toHaveClass("h-24");
    });

    it("has minimum width of min-w-[140px]", () => {
      const { container } = render(
        <StatusCard label="Min Width" value="42" icon={<Activity />} />
      );
      const button = container.firstChild as HTMLElement;
      expect(button).toHaveClass("min-w-[140px]");
    });
  });
});
