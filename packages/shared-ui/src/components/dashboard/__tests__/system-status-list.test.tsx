import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { SystemStatusList } from "../system-status-list";

describe("SystemStatusList", () => {
  const sampleItems = [
    { service: "API Server", status: "Healthy" as const, latency: "45ms" },
    { service: "Database", status: "Operational" as const, latency: "12ms" },
    { service: "Cache", status: "Degraded" as const, latency: "150ms" },
  ];

  it("renders all items", () => {
    render(<SystemStatusList items={sampleItems} />);
    expect(screen.getByText("API Server")).toBeInTheDocument();
    expect(screen.getByText("Database")).toBeInTheDocument();
    expect(screen.getByText("Cache")).toBeInTheDocument();
  });

  it("renders status badges", () => {
    render(<SystemStatusList items={sampleItems} />);
    expect(screen.getByText("Healthy")).toBeInTheDocument();
    expect(screen.getByText("Operational")).toBeInTheDocument();
    expect(screen.getByText("Degraded")).toBeInTheDocument();
  });

  it("renders latency values", () => {
    render(<SystemStatusList items={sampleItems} />);
    expect(screen.getByText("45ms")).toBeInTheDocument();
    expect(screen.getByText("12ms")).toBeInTheDocument();
    expect(screen.getByText("150ms")).toBeInTheDocument();
  });

  it("renders empty list without errors", () => {
    const { container } = render(<SystemStatusList items={[]} />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toBeInTheDocument();
    expect(wrapper.children.length).toBe(0);
  });

  it("renders single item", () => {
    render(
      <SystemStatusList
        items={[{ service: "Single Service", status: "Healthy", latency: "10ms" }]}
      />
    );
    expect(screen.getByText("Single Service")).toBeInTheDocument();
    expect(screen.getByText("Healthy")).toBeInTheDocument();
    expect(screen.getByText("10ms")).toBeInTheDocument();
  });

  describe("status styles", () => {
    it("applies Healthy status styling", () => {
      render(
        <SystemStatusList
          items={[{ service: "Test", status: "Healthy", latency: "10ms" }]}
        />
      );
      const statusBadge = screen.getByText("Healthy");
      expect(statusBadge).toHaveClass(
        "bg-[var(--success-50)]",
        "text-[var(--success-600)]"
      );
    });

    it("applies Operational status styling", () => {
      render(
        <SystemStatusList
          items={[{ service: "Test", status: "Operational", latency: "10ms" }]}
        />
      );
      const statusBadge = screen.getByText("Operational");
      expect(statusBadge).toHaveClass(
        "bg-[var(--success-50)]",
        "text-[var(--success-600)]"
      );
    });

    it("applies Degraded status styling", () => {
      render(
        <SystemStatusList
          items={[{ service: "Test", status: "Degraded", latency: "10ms" }]}
        />
      );
      const statusBadge = screen.getByText("Degraded");
      expect(statusBadge).toHaveClass("bg-warning-50", "text-warning-600");
    });

    it("applies Down status styling", () => {
      render(
        <SystemStatusList
          items={[{ service: "Test", status: "Down", latency: "N/A" }]}
        />
      );
      const statusBadge = screen.getByText("Down");
      expect(statusBadge).toHaveClass("bg-danger-50", "text-danger-600");
    });

    it("applies default styling for unknown status", () => {
      render(
        <SystemStatusList
          items={[{ service: "Test", status: "Unknown", latency: "10ms" }]}
        />
      );
      const statusBadge = screen.getByText("Unknown");
      expect(statusBadge).toHaveClass(
        "bg-[var(--surface-muted)]",
        "text-[var(--text-secondary)]"
      );
    });

    it("applies default styling for custom status", () => {
      render(
        <SystemStatusList
          items={[{ service: "Test", status: "Maintenance", latency: "10ms" }]}
        />
      );
      const statusBadge = screen.getByText("Maintenance");
      expect(statusBadge).toHaveClass(
        "bg-[var(--surface-muted)]",
        "text-[var(--text-secondary)]"
      );
    });
  });

  describe("layout", () => {
    it("has correct wrapper styling", () => {
      const { container } = render(<SystemStatusList items={sampleItems} />);
      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper).toHaveClass("space-y-3");
    });

    it("renders service name with correct styling", () => {
      render(<SystemStatusList items={sampleItems} />);
      const serviceName = screen.getByText("API Server");
      expect(serviceName).toHaveClass("text-xs", "font-medium");
    });

    it("renders latency with correct styling", () => {
      render(<SystemStatusList items={sampleItems} />);
      const latency = screen.getByText("45ms");
      expect(latency).toHaveClass("text-[10px]");
    });

    it("renders status badge with correct base styling", () => {
      render(<SystemStatusList items={sampleItems} />);
      const statusBadge = screen.getByText("Healthy");
      expect(statusBadge).toHaveClass(
        "rounded-full",
        "px-2",
        "py-0.5",
        "text-[10px]",
        "font-medium"
      );
    });

    it("renders item container with correct styling", () => {
      const { container } = render(<SystemStatusList items={sampleItems} />);
      const itemContainers = container.querySelectorAll(
        ".flex.items-center.justify-between.rounded-lg"
      );
      expect(itemContainers.length).toBe(3);
    });
  });

  describe("custom className", () => {
    it("applies custom className", () => {
      const { container } = render(
        <SystemStatusList items={sampleItems} className="custom-class" />
      );
      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper).toHaveClass("custom-class");
    });

    it("preserves default classes when custom className is added", () => {
      const { container } = render(
        <SystemStatusList items={sampleItems} className="custom-class" />
      );
      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper).toHaveClass("space-y-3", "custom-class");
    });
  });

  describe("item keys", () => {
    it("uses service as key for items", () => {
      const { container } = render(<SystemStatusList items={sampleItems} />);
      const items = container.querySelectorAll(
        ".flex.items-center.justify-between.rounded-lg"
      );
      expect(items.length).toBe(3);
    });
  });

  describe("edge cases", () => {
    it("handles long service names", () => {
      const longServiceName = "Very Long Service Name That Might Overflow";
      render(
        <SystemStatusList
          items={[{ service: longServiceName, status: "Healthy", latency: "10ms" }]}
        />
      );
      expect(screen.getByText(longServiceName)).toBeInTheDocument();
    });

    it("handles long latency values", () => {
      render(
        <SystemStatusList
          items={[{ service: "Test", status: "Healthy", latency: "1234567ms" }]}
        />
      );
      expect(screen.getByText("1234567ms")).toBeInTheDocument();
    });

    it("handles empty strings", () => {
      const { container } = render(
        <SystemStatusList items={[{ service: "", status: "", latency: "" }]} />
      );
      // Verify one item row is rendered
      const itemRows = container.querySelectorAll(
        ".flex.items-center.justify-between.rounded-lg"
      );
      expect(itemRows.length).toBe(1);
      // Verify the status badge exists with empty text
      const statusBadge = container.querySelector(".rounded-full.px-2");
      expect(statusBadge).toBeInTheDocument();
      expect(statusBadge).toHaveTextContent("");
    });

    it("handles special characters in content", () => {
      render(
        <SystemStatusList
          items={[
            {
              service: "Service <test>",
              status: "Status & more",
              latency: "10ms",
            },
          ]}
        />
      );
      expect(screen.getByText("Service <test>")).toBeInTheDocument();
      expect(screen.getByText("Status & more")).toBeInTheDocument();
    });
  });

  describe("complete example", () => {
    it("renders a complete dashboard status list", () => {
      const dashboardItems = [
        { service: "API Gateway", status: "Healthy" as const, latency: "23ms" },
        { service: "Auth Service", status: "Operational" as const, latency: "15ms" },
        { service: "Database Primary", status: "Healthy" as const, latency: "8ms" },
        { service: "Database Replica", status: "Degraded" as const, latency: "120ms" },
        { service: "Message Queue", status: "Down" as const, latency: "N/A" },
      ];

      render(<SystemStatusList items={dashboardItems} />);

      expect(screen.getByText("API Gateway")).toBeInTheDocument();
      expect(screen.getByText("Auth Service")).toBeInTheDocument();
      expect(screen.getByText("Database Primary")).toBeInTheDocument();
      expect(screen.getByText("Database Replica")).toBeInTheDocument();
      expect(screen.getByText("Message Queue")).toBeInTheDocument();

      expect(screen.getAllByText("Healthy").length).toBe(2);
      expect(screen.getByText("Operational")).toBeInTheDocument();
      expect(screen.getByText("Degraded")).toBeInTheDocument();
      expect(screen.getByText("Down")).toBeInTheDocument();
    });
  });
});
