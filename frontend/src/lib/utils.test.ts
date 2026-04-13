import { cn } from "./utils";

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("a", "b")).toBe("a b");
  });

  it("applies tailwind-merge for conflicts", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
  });
});
