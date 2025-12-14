import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Activity, Clock, Cpu } from "lucide-react";

import { MetricCard } from "../metric-card";

describe("MetricCard", () => {
  it("renders with title and value", () => {
    render(<MetricCard title="Response Time" value={245} />);
    expect(screen.getByText("Response Time")).toBeInTheDocument();
    expect(screen.getByText("245")).toBeInTheDocument();
  });

  it("renders with unit", () => {
    render(<MetricCard title="Response Time" value={245} unit="ms" />);
    expect(screen.getByText("ms")).toBeInTheDocument();
  });

  it("renders with description", () => {
    render(
      <MetricCard
        title="Response Time"
        value={245}
        description="Average response time"
      />
    );
    expect(screen.getByText("Average response time")).toBeInTheDocument();
  });

  describe("value formatting", () => {
    it("formats integer values without decimals", () => {
      render(<MetricCard title="Count" value={100} />);
      expect(screen.getByText("100")).toBeInTheDocument();
    });

    it("formats decimal values with two decimal places", () => {
      render(<MetricCard title="Rate" value={99.567} />);
      expect(screen.getByText("99.57")).toBeInTheDocument();
    });

    it("renders string values as-is", () => {
      render(<MetricCard title="Status" value="Healthy" />);
      expect(screen.getByText("Healthy")).toBeInTheDocument();
    });

    it("formats values like 99.5 with two decimal places", () => {
      render(<MetricCard title="Rate" value={99.5} />);
      expect(screen.getByText("99.50")).toBeInTheDocument();
    });
  });

  describe("trend indicators", () => {
    it("renders trending up indicator", () => {
      render(<MetricCard title="Success Rate" value={99} trend="up" />);
      expect(screen.getByLabelText("Trending up")).toBeInTheDocument();
      expect(screen.getByText("Increasing")).toBeInTheDocument();
    });

    it("renders trending down indicator", () => {
      render(<MetricCard title="Error Rate" value={2} trend="down" />);
      expect(screen.getByLabelText("Trending down")).toBeInTheDocument();
      expect(screen.getByText("Decreasing")).toBeInTheDocument();
    });

    it("renders stable indicator", () => {
      render(<MetricCard title="Users" value={100} trend="stable" />);
      expect(screen.getByLabelText("Stable")).toBeInTheDocument();
      expect(screen.getByText("Stable")).toBeInTheDocument();
    });

    it("does not render trend indicator when trend is not provided", () => {
      render(<MetricCard title="Metric" value={50} />);
      expect(screen.queryByLabelText("Trending up")).not.toBeInTheDocument();
      expect(screen.queryByLabelText("Trending down")).not.toBeInTheDocument();
      expect(screen.queryByLabelText("Stable")).not.toBeInTheDocument();
    });

    it("applies correct color class for up trend", () => {
      const { container } = render(
        <MetricCard title="Rate" value={99} trend="up" />
      );
      const trendIcon = container.querySelector('[aria-label="Trending up"]');
      expect(trendIcon).toHaveClass("text-[var(--success-600)]");
    });

    it("applies correct color class for down trend", () => {
      const { container } = render(
        <MetricCard title="Rate" value={2} trend="down" />
      );
      const trendIcon = container.querySelector('[aria-label="Trending down"]');
      expect(trendIcon).toHaveClass("text-[var(--error-600)]");
    });

    it("applies correct color class for stable trend", () => {
      const { container } = render(
        <MetricCard title="Rate" value={50} trend="stable" />
      );
      const trendIcon = container.querySelector('[aria-label="Stable"]');
      expect(trendIcon).toHaveClass("text-[var(--neutral-500)]");
    });
  });

  describe("progress bar", () => {
    it("renders progress bar when progress is provided", () => {
      const { container } = render(<MetricCard title="CPU Usage" value={67} progress={67} />);
      const progress = container.querySelector('[data-slot="progress"]');
      expect(progress).not.toBeNull();
      expect(progress!.closest('[aria-hidden="true"]')).not.toBeNull();
    });

    it("does not render progress bar when progress is not provided", () => {
      const { container } = render(<MetricCard title="Metric" value={50} />);
      const progress = container.querySelector('[data-slot="progress"]');
      expect(progress).toBeNull();
    });

    it("renders progress bar with value 0", () => {
      const { container } = render(<MetricCard title="Empty" value={0} progress={0} />);
      const progress = container.querySelector('[data-slot="progress"]');
      expect(progress).not.toBeNull();
      expect(progress!.closest('[aria-hidden="true"]')).not.toBeNull();
    });

    it("renders progress bar with value 100", () => {
      const { container } = render(<MetricCard title="Full" value={100} progress={100} />);
      const progress = container.querySelector('[data-slot="progress"]');
      expect(progress).not.toBeNull();
      expect(progress!.closest('[aria-hidden="true"]')).not.toBeNull();
    });
  });

  describe("icon rendering", () => {
    it("renders icon when provided", () => {
      render(
        <MetricCard
          title="Activity"
          value={100}
          icon={<Activity data-testid="metric-icon" />}
        />
      );
      expect(screen.getByTestId("metric-icon")).toBeInTheDocument();
    });

    it("does not render icon container when icon is not provided", () => {
      const { container } = render(<MetricCard title="No Icon" value={50} />);
      const iconContainer = container.querySelector(".shrink-0");
      expect(iconContainer).not.toBeInTheDocument();
    });

    it("applies variant color to icon", () => {
      const { container } = render(
        <MetricCard
          title="Blue Icon"
          value={100}
          icon={<Activity data-testid="metric-icon" />}
          variant="blue"
        />
      );
      const icon = screen.getByTestId("metric-icon");
      expect(icon).toHaveClass("text-[var(--primary-600)]");
    });
  });

  describe("variants", () => {
    it("applies default variant icon color", () => {
      const { container } = render(
        <MetricCard
          title="Default"
          value={100}
          icon={<Activity data-testid="icon" />}
          variant="default"
        />
      );
      const icon = screen.getByTestId("icon");
      expect(icon).toHaveClass("text-[var(--neutral-600)]");
    });

    it("applies blue variant icon color", () => {
      render(
        <MetricCard
          title="Blue"
          value={100}
          icon={<Activity data-testid="icon" />}
          variant="blue"
        />
      );
      const icon = screen.getByTestId("icon");
      expect(icon).toHaveClass("text-[var(--primary-600)]");
    });

    it("applies green variant icon color", () => {
      render(
        <MetricCard
          title="Green"
          value={100}
          icon={<Activity data-testid="icon" />}
          variant="green"
        />
      );
      const icon = screen.getByTestId("icon");
      expect(icon).toHaveClass("text-[var(--success-600)]");
    });

    it("applies yellow variant icon color", () => {
      render(
        <MetricCard
          title="Yellow"
          value={100}
          icon={<Activity data-testid="icon" />}
          variant="yellow"
        />
      );
      const icon = screen.getByTestId("icon");
      expect(icon).toHaveClass("text-[var(--warning-600)]");
    });

    it("applies red variant icon color", () => {
      render(
        <MetricCard
          title="Red"
          value={100}
          icon={<Activity data-testid="icon" />}
          variant="red"
        />
      );
      const icon = screen.getByTestId("icon");
      expect(icon).toHaveClass("text-[var(--error-600)]");
    });

    it("applies purple variant icon color", () => {
      render(
        <MetricCard
          title="Purple"
          value={100}
          icon={<Activity data-testid="icon" />}
          variant="purple"
        />
      );
      const icon = screen.getByTestId("icon");
      expect(icon).toHaveClass("text-[var(--color-accent-600)]");
    });
  });

  describe("custom className", () => {
    it("applies custom className to card", () => {
      const { container } = render(
        <MetricCard title="Custom" value={100} className="custom-class" />
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass("custom-class");
    });

    it("preserves default shadow-card class with custom className", () => {
      const { container } = render(
        <MetricCard title="Custom" value={100} className="custom-class" />
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass("shadow-card", "custom-class");
    });
  });

  describe("complete card rendering", () => {
    it("renders all elements together", () => {
      const { container } = render(
        <MetricCard
          title="CPU Usage"
          value={67.5}
          unit="%"
          icon={<Cpu data-testid="cpu-icon" />}
          trend="up"
          description="Current utilization"
          progress={67}
          variant="yellow"
        />
      );

      expect(screen.getByText("CPU Usage")).toBeInTheDocument();
      expect(screen.getByText("67.50")).toBeInTheDocument();
      expect(screen.getByText("%")).toBeInTheDocument();
      expect(screen.getByTestId("cpu-icon")).toBeInTheDocument();
      expect(screen.getByLabelText("Trending up")).toBeInTheDocument();
      expect(screen.getByText("Current utilization")).toBeInTheDocument();
      const progress = container.querySelector('[data-slot="progress"]');
      expect(progress).not.toBeNull();
      expect(progress!.closest('[aria-hidden="true"]')).not.toBeNull();
    });
  });

  describe("accessibility", () => {
    it("renders title in CardTitle component", () => {
      render(<MetricCard title="Accessible Title" value={100} />);
      const title = screen.getByText("Accessible Title");
      expect(title.tagName.toLowerCase()).toBe("div");
    });

    it("trend icons have aria-label for screen readers", () => {
      render(<MetricCard title="Rate" value={99} trend="up" />);
      expect(screen.getByLabelText("Trending up")).toBeInTheDocument();
    });
  });
});
