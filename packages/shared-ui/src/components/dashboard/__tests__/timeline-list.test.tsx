import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { TimelineList } from "../timeline-list";

describe("TimelineList", () => {
  const sampleItems = [
    { id: "1", title: "Event A", desc: "Description A", time: "2 hours ago" },
    { id: "2", title: "Event B", desc: "Description B", time: "5 hours ago" },
    { id: "3", title: "Event C", desc: "Description C", time: "1 day ago" },
  ];

  it("renders all items", () => {
    render(<TimelineList items={sampleItems} />);
    expect(screen.getByText("Event A")).toBeInTheDocument();
    expect(screen.getByText("Event B")).toBeInTheDocument();
    expect(screen.getByText("Event C")).toBeInTheDocument();
  });

  it("renders descriptions", () => {
    render(<TimelineList items={sampleItems} />);
    expect(screen.getByText("Description A")).toBeInTheDocument();
    expect(screen.getByText("Description B")).toBeInTheDocument();
    expect(screen.getByText("Description C")).toBeInTheDocument();
  });

  it("renders time values", () => {
    render(<TimelineList items={sampleItems} />);
    expect(screen.getByText("2 hours ago")).toBeInTheDocument();
    expect(screen.getByText("5 hours ago")).toBeInTheDocument();
    expect(screen.getByText("1 day ago")).toBeInTheDocument();
  });

  it("renders as an unordered list", () => {
    render(<TimelineList items={sampleItems} />);
    expect(screen.getByRole("list")).toBeInTheDocument();
  });

  it("renders list items", () => {
    render(<TimelineList items={sampleItems} />);
    const listItems = screen.getAllByRole("listitem");
    expect(listItems.length).toBe(3);
  });

  it("renders empty list without errors", () => {
    render(<TimelineList items={[]} />);
    const list = screen.getByRole("list");
    expect(list).toBeInTheDocument();
    expect(list.children.length).toBe(0);
  });

  it("renders single item", () => {
    render(
      <TimelineList
        items={[{ id: "single", title: "Single", desc: "Only one", time: "Now" }]}
      />
    );
    expect(screen.getByText("Single")).toBeInTheDocument();
    expect(screen.getByText("Only one")).toBeInTheDocument();
    expect(screen.getByText("Now")).toBeInTheDocument();
  });

  describe("layout", () => {
    it("has correct wrapper styling", () => {
      render(<TimelineList items={sampleItems} />);
      const list = screen.getByRole("list");
      expect(list).toHaveClass("space-y-4", "text-sm");
    });

    it("renders title with correct styling", () => {
      render(<TimelineList items={sampleItems} />);
      const title = screen.getByText("Event A");
      expect(title).toHaveClass("font-medium");
    });

    it("renders description with correct styling", () => {
      render(<TimelineList items={sampleItems} />);
      const desc = screen.getByText("Description A");
      expect(desc).toHaveClass("text-xs");
    });

    it("renders time with correct styling", () => {
      render(<TimelineList items={sampleItems} />);
      const time = screen.getByText("2 hours ago");
      expect(time).toHaveClass("text-xs");
    });

    it("renders list items with flex justify-between", () => {
      const { container } = render(<TimelineList items={sampleItems} />);
      const listItems = container.querySelectorAll("li");
      listItems.forEach((item) => {
        expect(item).toHaveClass("flex", "justify-between");
      });
    });
  });

  describe("custom className", () => {
    it("applies custom className", () => {
      render(<TimelineList items={sampleItems} className="custom-class" />);
      const list = screen.getByRole("list");
      expect(list).toHaveClass("custom-class");
    });

    it("preserves default classes when custom className is added", () => {
      render(<TimelineList items={sampleItems} className="custom-class" />);
      const list = screen.getByRole("list");
      expect(list).toHaveClass("space-y-4", "text-sm", "custom-class");
    });
  });

  describe("item keys", () => {
    it("uses id as key for items", () => {
      const { container } = render(<TimelineList items={sampleItems} />);
      const listItems = container.querySelectorAll("li");
      expect(listItems.length).toBe(3);
    });
  });

  describe("edge cases", () => {
    it("handles long titles", () => {
      const longTitle = "This is a very long title that might overflow the container";
      render(
        <TimelineList
          items={[{ id: "long", title: longTitle, desc: "Short", time: "Now" }]}
        />
      );
      expect(screen.getByText(longTitle)).toBeInTheDocument();
    });

    it("handles long descriptions", () => {
      const longDesc = "This is a very long description that provides detailed information about the event";
      render(
        <TimelineList
          items={[{ id: "long", title: "Title", desc: longDesc, time: "Now" }]}
        />
      );
      expect(screen.getByText(longDesc)).toBeInTheDocument();
    });

    it("handles empty strings", () => {
      render(
        <TimelineList items={[{ id: "empty", title: "", desc: "", time: "" }]} />
      );
      const listItems = screen.getAllByRole("listitem");
      expect(listItems.length).toBe(1);
    });

    it("handles special characters in content", () => {
      render(
        <TimelineList
          items={[
            {
              id: "special",
              title: "Event <script>alert('xss')</script>",
              desc: "Description & more",
              time: "10:30 AM",
            },
          ]}
        />
      );
      expect(
        screen.getByText("Event <script>alert('xss')</script>")
      ).toBeInTheDocument();
      expect(screen.getByText("Description & more")).toBeInTheDocument();
    });
  });
});
