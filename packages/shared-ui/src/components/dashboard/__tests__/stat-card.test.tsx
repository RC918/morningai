import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Activity, DollarSign, TrendingUp, Zap } from "lucide-react";

import { StatCard } from "../stat-card";

describe("StatCard", () => {
  it("renders with label and value", () => {
    render(<StatCard label="Total Revenue" value="$45,231" />);
    expect(screen.getByText("Total Revenue")).toBeInTheDocument();
    expect(screen.getByText("$45,231")).toBeInTheDocument();
  });

  it("renders as a div element (not interactive)", () => {
    const { container } = render(<StatCard label="Test" value="42" />);
    const card = container.firstChild as HTMLElement;
    expect(card.tagName).toBe("DIV");
  });

  describe("variants", () => {
    it("renders default variant with correct icon color", () => {
      const { container } = render(
        <StatCard
          label="Default"
          value="100"
          icon={<Activity data-testid="icon" />}
          variant="default"
        />
      );
      const icon = container.querySelector('[data-testid="icon"]');
      expect(icon).toHaveClass("text-[var(--neutral-600)]");
    });

    it("renders blue variant with correct icon color", () => {
      const { container } = render(
        <StatCard
          label="Blue"
          value="200"
          icon={<Activity data-testid="icon" />}
          variant="blue"
        />
      );
      const icon = container.querySelector('[data-testid="icon"]');
      expect(icon).toHaveClass("text-[var(--primary-600)]");
    });

    it("renders green variant with correct icon color", () => {
      const { container } = render(
        <StatCard
          label="Green"
          value="300"
          icon={<Activity data-testid="icon" />}
          variant="green"
        />
      );
      const icon = container.querySelector('[data-testid="icon"]');
      expect(icon).toHaveClass("text-[var(--success-600)]");
    });

    it("renders yellow variant with correct icon color", () => {
      const { container } = render(
        <StatCard
          label="Yellow"
          value="400"
          icon={<Activity data-testid="icon" />}
          variant="yellow"
        />
      );
      const icon = container.querySelector('[data-testid="icon"]');
      expect(icon).toHaveClass("text-[var(--warning-600)]");
    });

    it("renders red variant with correct icon color", () => {
      const { container } = render(
        <StatCard
          label="Red"
          value="500"
          icon={<Activity data-testid="icon" />}
          variant="red"
        />
      );
      const icon = container.querySelector('[data-testid="icon"]');
      expect(icon).toHaveClass("text-[var(--error-600)]");
    });

    it("renders purple variant with correct icon color", () => {
      const { container } = render(
        <StatCard
          label="Purple"
          value="600"
          icon={<Activity data-testid="icon" />}
          variant="purple"
        />
      );
      const icon = container.querySelector('[data-testid="icon"]');
      expect(icon).toHaveClass("text-[var(--color-accent-600)]");
    });
  });

  describe("icon rendering", () => {
    it("renders icon when provided", () => {
      render(
        <StatCard
          label="With Icon"
          value="42"
          icon={<DollarSign data-testid="dollar-icon" />}
        />
      );
      expect(screen.getByTestId("dollar-icon")).toBeInTheDocument();
    });

    it("does not render icon container when icon is not provided", () => {
      const { container } = render(<StatCard label="No Icon" value="42" />);
      const iconContainer = container.querySelector(".ml-3.shrink-0");
      expect(iconContainer).not.toBeInTheDocument();
    });

    it("applies size-5 class to icon", () => {
      const { container } = render(
        <StatCard
          label="Sized Icon"
          value="42"
          icon={<Activity data-testid="sized-icon" />}
        />
      );
      const icon = container.querySelector('[data-testid="sized-icon"]');
      expect(icon).toHaveClass("size-5");
    });
  });

  describe("badge", () => {
    it("renders badge when provided", () => {
      render(<StatCard label="With Badge" value="85%" badge="On Target" />);
      expect(screen.getByText("On Target")).toBeInTheDocument();
    });

    it("does not render badge when not provided", () => {
      render(<StatCard label="No Badge" value="42" />);
      expect(screen.queryByText("On Target")).not.toBeInTheDocument();
    });

    it("applies correct badge styling", () => {
      render(<StatCard label="Styled Badge" value="85%" badge="On Target" />);
      const badge = screen.getByText("On Target");
      expect(badge).toHaveClass("px-2", "py-0.5", "text-[10px]", "rounded-full");
    });
  });

  describe("delta/trend display", () => {
    it("renders deltaLabel when provided", () => {
      render(
        <StatCard
          label="With Delta"
          value="98.5%"
          deltaLabel="+5.10% from last month"
        />
      );
      expect(screen.getByText("+5.10% from last month")).toBeInTheDocument();
    });

    it("renders deprecated trend prop for backwards compatibility", () => {
      render(
        <StatCard
          label="With Trend"
          value="100"
          trend="+5% (using deprecated trend prop)"
        />
      );
      expect(
        screen.getByText("+5% (using deprecated trend prop)")
      ).toBeInTheDocument();
    });

    it("prefers deltaLabel over trend when both are provided", () => {
      render(
        <StatCard
          label="Both Props"
          value="100"
          deltaLabel="Delta Label"
          trend="Trend Label"
        />
      );
      expect(screen.getByText("Delta Label")).toBeInTheDocument();
      expect(screen.queryByText("Trend Label")).not.toBeInTheDocument();
    });

    it("applies success color when deltaPositive is true", () => {
      render(
        <StatCard
          label="Positive"
          value="98.5%"
          deltaLabel="+5.10%"
          deltaPositive={true}
        />
      );
      const delta = screen.getByText("+5.10%");
      expect(delta).toHaveClass("text-[var(--success-600)]");
    });

    it("applies error color when deltaPositive is false", () => {
      render(
        <StatCard
          label="Negative"
          value="2.3%"
          deltaLabel="Up 0.5%"
          deltaPositive={false}
        />
      );
      const delta = screen.getByText("Up 0.5%");
      expect(delta).toHaveClass("text-[var(--error-600)]");
    });

    it("applies secondary text color when deltaPositive is neutral", () => {
      render(
        <StatCard
          label="Neutral"
          value="1,234"
          deltaLabel="Target: 1,500"
          deltaPositive="neutral"
        />
      );
      const delta = screen.getByText("Target: 1,500");
      expect(delta).toHaveClass("text-[var(--text-secondary)]");
    });

    it("defaults deltaPositive to true", () => {
      render(
        <StatCard label="Default Positive" value="100" deltaLabel="+10%" />
      );
      const delta = screen.getByText("+10%");
      expect(delta).toHaveClass("text-[var(--success-600)]");
    });
  });

  describe("custom className", () => {
    it("applies custom className", () => {
      const { container } = render(
        <StatCard label="Custom" value="42" className="custom-class" />
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass("custom-class");
    });

    it("preserves default classes when custom className is added", () => {
      const { container } = render(
        <StatCard label="Custom" value="42" className="custom-class" />
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass("rounded-xl", "border", "shadow-card");
    });
  });

  describe("layout", () => {
    it("has correct base styling", () => {
      const { container } = render(<StatCard label="Layout" value="42" />);
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass("rounded-xl", "border", "p-4", "shadow-card");
    });

    it("renders label with correct styling", () => {
      render(<StatCard label="Styled Label" value="42" />);
      const label = screen.getByText("Styled Label");
      expect(label).toHaveClass("text-xs", "font-medium");
    });

    it("renders value with correct styling", () => {
      render(<StatCard label="Test" value="$45,231" />);
      const value = screen.getByText("$45,231");
      expect(value).toHaveClass("text-2xl", "font-semibold");
    });
  });
});
