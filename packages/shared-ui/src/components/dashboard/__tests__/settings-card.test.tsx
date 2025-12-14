import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Settings, Shield, Bell, Lock } from "lucide-react";

import { SettingsCard } from "../settings-card";

describe("SettingsCard", () => {
  it("renders with title", () => {
    render(<SettingsCard title="General Settings" />);
    expect(screen.getByText("General Settings")).toBeInTheDocument();
  });

  it("renders with title and description", () => {
    render(
      <SettingsCard
        title="Security Settings"
        description="Manage your security preferences"
      />
    );
    expect(screen.getByText("Security Settings")).toBeInTheDocument();
    expect(screen.getByText("Manage your security preferences")).toBeInTheDocument();
  });

  it("renders with icon", () => {
    render(
      <SettingsCard
        title="Settings"
        icon={<Settings data-testid="settings-icon" />}
      />
    );
    expect(screen.getByTestId("settings-icon")).toBeInTheDocument();
  });

  it("renders children content", () => {
    render(
      <SettingsCard title="Notifications">
        <div data-testid="notification-toggle">Toggle notifications</div>
      </SettingsCard>
    );
    expect(screen.getByTestId("notification-toggle")).toBeInTheDocument();
  });

  it("renders without children", () => {
    const { container } = render(<SettingsCard title="Empty Card" />);
    expect(container.querySelector('[class*="CardContent"]')).not.toBeInTheDocument();
  });

  describe("variants", () => {
    it("applies default variant icon color", () => {
      render(
        <SettingsCard
          title="Default"
          icon={<Settings data-testid="icon" />}
          variant="default"
        />
      );
      const icon = screen.getByTestId("icon");
      expect(icon.className).toContain("text-[var(--neutral-600)]");
    });

    it("applies blue variant icon color", () => {
      render(
        <SettingsCard
          title="Blue"
          icon={<Settings data-testid="icon" />}
          variant="blue"
        />
      );
      const icon = screen.getByTestId("icon");
      expect(icon.className).toContain("text-[var(--primary-600)]");
    });

    it("applies green variant icon color", () => {
      render(
        <SettingsCard
          title="Green"
          icon={<Shield data-testid="icon" />}
          variant="green"
        />
      );
      const icon = screen.getByTestId("icon");
      expect(icon.className).toContain("text-[var(--success-600)]");
    });

    it("applies yellow variant icon color", () => {
      render(
        <SettingsCard
          title="Yellow"
          icon={<Bell data-testid="icon" />}
          variant="yellow"
        />
      );
      const icon = screen.getByTestId("icon");
      expect(icon.className).toContain("text-[var(--warning-600)]");
    });

    it("applies red variant icon color", () => {
      render(
        <SettingsCard
          title="Red"
          icon={<Lock data-testid="icon" />}
          variant="red"
        />
      );
      const icon = screen.getByTestId("icon");
      expect(icon.className).toContain("text-[var(--error-600)]");
    });

    it("applies purple variant icon color", () => {
      render(
        <SettingsCard
          title="Purple"
          icon={<Settings data-testid="icon" />}
          variant="purple"
        />
      );
      const icon = screen.getByTestId("icon");
      expect(icon.className).toContain("text-[var(--color-accent-600)]");
    });
  });

  describe("noPadding option", () => {
    it("applies default padding when noPadding is false", () => {
      const { container } = render(
        <SettingsCard title="With Padding" noPadding={false}>
          <div>Content</div>
        </SettingsCard>
      );
      const cardContent = container.querySelector('[class*="space-y-4"]');
      expect(cardContent).toBeInTheDocument();
    });

    it("removes padding when noPadding is true", () => {
      const { container } = render(
        <SettingsCard title="No Padding" noPadding={true}>
          <div>Content</div>
        </SettingsCard>
      );
      const cardContent = container.querySelector('[class*="p-0"]');
      expect(cardContent).toBeInTheDocument();
    });
  });

  describe("custom className", () => {
    it("applies custom className to card", () => {
      const { container } = render(
        <SettingsCard title="Custom" className="custom-class" />
      );
      expect(container.firstChild).toHaveClass("custom-class");
    });

    it("preserves default shadow-card class with custom className", () => {
      const { container } = render(
        <SettingsCard title="Custom" className="my-custom-class" />
      );
      expect(container.firstChild).toHaveClass("shadow-card");
      expect(container.firstChild).toHaveClass("my-custom-class");
    });
  });

  describe("complete card rendering", () => {
    it("renders all elements together", () => {
      render(
        <SettingsCard
          title="Complete Settings"
          description="All settings in one place"
          icon={<Settings data-testid="complete-icon" />}
          variant="blue"
        >
          <div data-testid="settings-content">
            <button>Save</button>
          </div>
        </SettingsCard>
      );

      expect(screen.getByText("Complete Settings")).toBeInTheDocument();
      expect(screen.getByText("All settings in one place")).toBeInTheDocument();
      expect(screen.getByTestId("complete-icon")).toBeInTheDocument();
      expect(screen.getByTestId("settings-content")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
    });
  });

  describe("accessibility", () => {
    it("renders title in CardTitle component", () => {
      render(<SettingsCard title="Accessible Title" />);
      const title = screen.getByText("Accessible Title");
      expect(title.tagName.toLowerCase()).toBe("div");
    });

    it("renders description in CardDescription component", () => {
      render(
        <SettingsCard
          title="Title"
          description="Accessible description"
        />
      );
      const description = screen.getByText("Accessible description");
      expect(description).toBeInTheDocument();
    });
  });
});
